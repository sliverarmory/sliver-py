from __future__ import annotations

import ast
import re
from pathlib import Path

from sliver import GOARCH, GOOS, Client, InteractiveBeacon, InteractiveSession
from sliver._rpc_generated import GeneratedPydanticSliverRPCStub
from sliver.interactive import BaseInteractiveCommands

from .e2e.coverage import (
    COVERAGE_GROUPS,
    HIGH_LEVEL_RPC_NAMES,
    HIGH_LEVEL_RPC_REACHABLE,
    NATIVE_E2E,
    NATIVE_TARGETS,
    SLIVER_RPC_TOTAL,
)


def _public_methods(cls: type[object]) -> set[str]:
    return {
        name
        for name in dir(cls)
        if not name.startswith("_") and callable(getattr(cls, name))
    }


def _exported_surface() -> set[str]:
    shared = _public_methods(BaseInteractiveCommands)
    session = _public_methods(InteractiveSession) - shared
    beacon = _public_methods(InteractiveBeacon) - shared
    return (
        {f"Client.{name}" for name in _public_methods(Client)}
        | {f"Interactive.{name}" for name in shared}
        | {f"InteractiveSession.{name}" for name in session}
        | {f"InteractiveBeacon.{name}" for name in beacon}
    )


def test_every_exported_high_level_method_has_one_e2e_disposition() -> None:
    observed: set[str] = set()
    for group, methods in COVERAGE_GROUPS.items():
        overlap = observed & methods
        assert not overlap, f"duplicate E2E dispositions in {group}: {sorted(overlap)}"
        observed.update(methods)

    exported = _exported_surface()
    assert observed == exported, (
        f"unclassified={sorted(exported - observed)!r}, "
        f"stale={sorted(observed - exported)!r}"
    )


def test_native_e2e_disposition_only_names_public_callables() -> None:
    classes = {
        "Client": Client,
        "Interactive": BaseInteractiveCommands,
        "InteractiveSession": InteractiveSession,
        "InteractiveBeacon": InteractiveBeacon,
    }
    for qualified_name in NATIVE_E2E:
        surface, name = qualified_name.split(".", 1)
        assert callable(getattr(classes[surface], name)), qualified_name


def test_native_e2e_ledger_names_appear_in_managed_scenario_calls() -> None:
    e2e_root = Path(__file__).resolve().parent / "e2e"
    called_names: set[str] = set()
    for source in e2e_root.glob("*.py"):
        if source.name == "coverage.py":
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"))
        called_names.update(
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        )

    expected_names = {name.split(".", 1)[1] for name in NATIVE_E2E}
    assert expected_names <= called_names, sorted(expected_names - called_names)


def test_native_matrix_matches_the_exact_workflow_targets() -> None:
    expected = frozenset(
        {
            (GOOS.DARWIN, GOARCH.ARM64),
            (GOOS.LINUX, GOARCH.AMD64),
            (GOOS.WINDOWS, GOARCH.AMD64),
        }
    )
    assert NATIVE_TARGETS == expected

    repository = Path(__file__).resolve().parents[1]
    workflow = (repository / ".github/workflows/e2e.yml").read_text(encoding="utf-8")
    workflow_targets = frozenset(
        (GOOS(goos), GOARCH(goarch))
        for goos, goarch in re.findall(
            r"^\s+goos:\s+([a-z0-9]+)\s*$\n^\s+goarch:\s+([a-z0-9]+)\s*$",
            workflow,
            flags=re.MULTILINE,
        )
    )
    assert workflow_targets == expected


def test_high_level_api_reachability_is_reconciled_with_the_pinned_rpc_surface() -> (
    None
):
    declarations = list(GeneratedPydanticSliverRPCStub.__annotations__)
    assert len(declarations) % 2 == 0
    aliases: dict[str, str] = {}
    for index in range(0, len(declarations), 2):
        snake_name, sliver_name = declarations[index : index + 2]
        assert snake_name.islower()
        assert not sliver_name.islower()
        aliases[snake_name] = snake_name
        aliases[sliver_name] = snake_name

    repository = Path(__file__).resolve().parents[1]
    reachable: set[str] = set()
    for relative_path in (
        "src/sliver/client.py",
        "src/sliver/session.py",
        "src/sliver/beacon.py",
        "src/sliver/interactive.py",
    ):
        tree = ast.parse((repository / relative_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and node.attr in aliases
                and isinstance(node.value, ast.Attribute)
                and node.value.attr in {"pydantic_stub", "rpc", "_stub"}
            ):
                reachable.add(aliases[node.attr])
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_execute"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                assert node.args[0].value in aliases
                reachable.add(aliases[node.args[0].value])

    assert len(declarations) // 2 == SLIVER_RPC_TOTAL
    assert reachable == HIGH_LEVEL_RPC_NAMES
    assert len(reachable) == HIGH_LEVEL_RPC_REACHABLE
