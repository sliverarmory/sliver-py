#!/usr/bin/env python3
"""Generate companion stubs for the handwritten public Sliver API.

The protobuf-derived models and RPC surface have their own generators.  This
generator keeps the handwritten client and interactive APIs equally precise for
type checkers that intentionally do not inspect installed implementation files.
"""

from __future__ import annotations

import argparse
import ast
import copy
import difflib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "src" / "sliver"

MODULE_PREAMBLES = {
    "client": """\
from __future__ import annotations

from collections.abc import AsyncGenerator

import grpc

from . import models
from ._rpc import PydanticSliverRPCStub
from .beacon import InteractiveBeacon
from .config import SliverClientConfig
from .session import InteractiveSession
""",
    "session": """\
from __future__ import annotations

import grpc

from . import models
from .interactive import BaseInteractiveCommands
""",
    "beacon": """\
from __future__ import annotations

import grpc

from . import models
from .interactive import BaseInteractiveCommands
""",
    "interactive": """\
from __future__ import annotations

from . import models
""",
    "config": """\
from __future__ import annotations

import os

from pydantic import BaseModel
""",
}

CLASS_ATTRIBUTES = {
    ("client", "BaseClient"): (
        "config: SliverClientConfig",
    ),
    ("session", "BaseSession"): ("timeout: int",),
    ("beacon", "BaseBeacon"): ("timeout: int",),
}

PUBLIC_DUNDERS = {"__init__", "__repr__", "__str__"}


def _is_public_method(name: str) -> bool:
    return not name.startswith("_") or name in PUBLIC_DUNDERS


def _contains_yield(function: ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, (ast.Yield, ast.YieldFrom)) for node in ast.walk(function)
    )


def _stub_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    stub = copy.deepcopy(function)
    stub.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
    stub.type_comment = None

    # ``async def`` plus an ellipsis is a coroutine in a stub.  Async-generator
    # APIs instead use a regular ``def`` returning AsyncGenerator, matching the
    # callable type of their implementation (which contains ``yield``).
    if isinstance(stub, ast.AsyncFunctionDef) and _contains_yield(function):
        returns = stub.returns
        if (
            isinstance(returns, ast.Subscript)
            and isinstance(returns.value, ast.Name)
            and returns.value.id == "AsyncGenerator"
            and isinstance(returns.slice, ast.Tuple)
        ):
            returns.slice = returns.slice.elts[0]
        stub = ast.FunctionDef(
            name=stub.name,
            args=stub.args,
            body=stub.body,
            decorator_list=stub.decorator_list,
            returns=returns,
            type_comment=None,
        )

    # The implementation annotates interactive ``self`` with an internal
    # protocol so it can type-check the mixin.  Consumers only need the method
    # parameters and concrete return type.
    positional = [*stub.args.posonlyargs, *stub.args.args]
    if positional and positional[0].arg in {"self", "cls"}:
        positional[0].annotation = None
    return stub


def _pydantic_constructor(class_node: ast.ClassDef) -> str:
    parameters: list[str] = []
    for node in class_node.body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id.startswith("_") or node.target.id == "model_config":
            continue
        parameter = f"{node.target.id}: {ast.unparse(node.annotation)}"
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            parameter += " = ..."
        parameters.append(parameter)
    return f"def __init__(self, *, {', '.join(parameters)}) -> None: ..."


def _assignment_annotation(value: ast.expr) -> str | None:
    if isinstance(value, ast.Constant):
        if isinstance(value.value, bool):
            return "bool"
        if isinstance(value.value, int):
            return "int"
        if isinstance(value.value, str):
            return "str"
    if isinstance(value, ast.BinOp):
        return "int"
    if isinstance(value, ast.List):
        element_types = {
            annotation
            for element in value.elts
            if (annotation := _assignment_annotation(element)) is not None
        }
        if len(element_types) == 1:
            return f"list[{element_types.pop()}]"
    return None


def _render_class(module: str, class_node: ast.ClassDef) -> str:
    bases = ", ".join(ast.unparse(base) for base in class_node.bases)
    header = f"class {class_node.name}"
    if bases:
        header += f"({bases})"
    header += ":"

    members: list[str] = list(CLASS_ATTRIBUTES.get((module, class_node.name), ()))
    for node in class_node.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id.startswith("_"):
            continue
        annotation = _assignment_annotation(node.value)
        if annotation is not None:
            members.append(f"{target.id}: {annotation}")

    if module == "config":
        for node in class_node.body:
            if not isinstance(node, ast.AnnAssign) or not isinstance(
                node.target, ast.Name
            ):
                continue
            if node.target.id.startswith("_") or node.target.id == "model_config":
                continue
            members.append(f"{node.target.id}: {ast.unparse(node.annotation)}")
        members.append(_pydantic_constructor(class_node))

    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
            _is_public_method(node.name)
        ):
            members.append(ast.unparse(ast.fix_missing_locations(_stub_function(node))))

    if not members:
        members.append("...")

    rendered_members = []
    for member in members:
        rendered_members.append("\n".join(f"    {line}" for line in member.splitlines()))
    return f"{header}\n" + "\n\n".join(rendered_members)


def _render_module(module: str) -> str:
    source = PACKAGE_ROOT / f"{module}.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    sections = [
        "# @generated by scripts/highlevelstubgen.py; DO NOT EDIT.",
        MODULE_PREAMBLES[module].rstrip(),
    ]

    constants = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id.startswith("_"):
            continue
        annotation = _assignment_annotation(node.value)
        if annotation is not None:
            constants.append(f"{target.id}: {annotation}")
    if constants:
        sections.append("\n".join(constants))

    sections.extend(
        _render_class(module, node)
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    )
    return "\n\n".join(sections) + "\n"


def _render_package_init() -> str:
    source = PACKAGE_ROOT / "__init__.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    imports: dict[str, tuple[str | None, str]] = {}
    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            for alias in node.names:
                imports[alias.asname or alias.name] = (node.module, alias.name)
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
            and isinstance(node.value, (ast.List, ast.Tuple))
        ):
            exports = [
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant)
                and isinstance(element.value, str)
            ]

    lines = [
        "# @generated by scripts/highlevelstubgen.py; DO NOT EDIT.",
        "from __future__ import annotations",
        "",
    ]
    reexports: list[tuple[str, str]] = []
    for export in exports:
        imported = imports.get(export)
        if imported is None:
            continue
        module, original = imported
        if module is None:
            reexports.append(("", f"from . import {original} as {export}"))
        else:
            reexports.append(
                (module, f"from .{module} import {original} as {export}")
            )
    lines.extend(line for _, line in sorted(reexports))
    lines.extend(("", "__version__: str", ""))
    return "\n".join(lines)


def generated_files() -> dict[Path, str]:
    files = {
        PACKAGE_ROOT / f"{module}.pyi": _render_module(module)
        for module in MODULE_PREAMBLES
    }
    files[PACKAGE_ROOT / "__init__.pyi"] = _render_package_init()
    return files


def _check(files: dict[Path, str]) -> bool:
    current = True
    for path, expected in files.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual == expected:
            continue
        current = False
        print(
            "".join(
                difflib.unified_diff(
                    actual.splitlines(keepends=True),
                    expected.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=f"generated:{path}",
                )
            ),
            end="",
        )
    return current


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when checked-in high-level stubs are stale",
    )
    args = parser.parse_args()
    files = generated_files()
    if args.check:
        if not _check(files):
            raise SystemExit(1)
        return
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
