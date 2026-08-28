#!/usr/bin/env python3
"""Generate concrete Pydantic source modules from Sliver descriptors."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from google.protobuf import descriptor_pb2
from grpc_tools import protoc

ROOT_DIR = Path(__file__).resolve().parents[1]
PROTO_DIR = ROOT_DIR / "sliver" / "protobuf"
OUT_DIR = ROOT_DIR / "src" / "sliver" / "models"
PROTO_FILES = (
    PROTO_DIR / "commonpb" / "common.proto",
    PROTO_DIR / "sliverpb" / "sliver.proto",
    PROTO_DIR / "clientpb" / "client.proto",
)
GENERATED_MODULES = ("commonpb", "sliverpb", "clientpb")
GENERATED_FILES = tuple(
    f"{module}{suffix}"
    for module in GENERATED_MODULES
    for suffix in (".py", ".pyi")
)

_NAMING_PATH = OUT_DIR / "_naming.py"
_NAMING_SPEC = importlib.util.spec_from_file_location(
    "sliver_pydantic_model_naming", _NAMING_PATH
)
if _NAMING_SPEC is None or _NAMING_SPEC.loader is None:
    raise RuntimeError(f"cannot load model naming rules from {_NAMING_PATH}")
_NAMING_MODULE = importlib.util.module_from_spec(_NAMING_SPEC)
_NAMING_SPEC.loader.exec_module(_NAMING_MODULE)
_python_field_name = _NAMING_MODULE.python_field_name

_SCALAR_TYPES = {
    descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE: "float",
    descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT: "float",
    descriptor_pb2.FieldDescriptorProto.TYPE_INT64: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_UINT64: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_INT32: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_FIXED64: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_FIXED32: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_BOOL: "bool",
    descriptor_pb2.FieldDescriptorProto.TYPE_STRING: "str",
    descriptor_pb2.FieldDescriptorProto.TYPE_BYTES: "bytes",
    descriptor_pb2.FieldDescriptorProto.TYPE_UINT32: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED32: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED64: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_SINT32: "int",
    descriptor_pb2.FieldDescriptorProto.TYPE_SINT64: "int",
}
_INTEGER_BOUNDS = {
    descriptor_pb2.FieldDescriptorProto.TYPE_INT32: (-(2**31), (2**31) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_SINT32: (-(2**31), (2**31) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED32: (-(2**31), (2**31) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_UINT32: (0, (2**32) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_FIXED32: (0, (2**32) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_INT64: (-(2**63), (2**63) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_SINT64: (-(2**63), (2**63) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_SFIXED64: (-(2**63), (2**63) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_UINT64: (0, (2**64) - 1),
    descriptor_pb2.FieldDescriptorProto.TYPE_FIXED64: (0, (2**64) - 1),
}


@dataclass(frozen=True, slots=True)
class MessageInfo:
    file: descriptor_pb2.FileDescriptorProto
    descriptor: descriptor_pb2.DescriptorProto
    path: tuple[str, ...]

    @property
    def full_name(self) -> str:
        return ".".join((self.file.package, *self.path))

    @property
    def python_name(self) -> str:
        if len(self.path) == 1:
            return self.path[0]
        return "_" + "_".join(self.path)

    @property
    def is_map_entry(self) -> bool:
        return self.descriptor.options.map_entry


@dataclass(frozen=True, slots=True)
class EnumInfo:
    file: descriptor_pb2.FileDescriptorProto
    descriptor: descriptor_pb2.EnumDescriptorProto
    path: tuple[str, ...]

    @property
    def full_name(self) -> str:
        return ".".join((self.file.package, *self.path))

    @property
    def python_name(self) -> str:
        if len(self.path) == 1:
            return self.path[0]
        return "_" + "_".join(self.path)


def _descriptor_set() -> descriptor_pb2.FileDescriptorSet:
    missing = [path for path in PROTO_FILES if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "missing protobuf sources: "
            + ", ".join(str(path.relative_to(ROOT_DIR)) for path in missing)
        )
    grpc_include = Path(str(files("grpc_tools") / "_proto"))
    with tempfile.TemporaryDirectory(prefix="sliver-py-descriptors-") as temp_dir:
        descriptor_path = Path(temp_dir) / "sliver.pb"
        arguments = [
            "grpc_tools.protoc",
            f"-I{grpc_include}",
            f"-I{PROTO_DIR}",
            f"--descriptor_set_out={descriptor_path}",
            "--include_imports",
            *(str(path) for path in PROTO_FILES),
        ]
        if protoc.main(arguments) != 0:
            raise RuntimeError("protoc failed while generating the descriptor set")
        result = descriptor_pb2.FileDescriptorSet()
        result.ParseFromString(descriptor_path.read_bytes())
        return result


def _index_descriptors(
    descriptor_set: descriptor_pb2.FileDescriptorSet,
) -> tuple[
    dict[str, descriptor_pb2.FileDescriptorProto],
    dict[str, MessageInfo],
    dict[str, EnumInfo],
]:
    selected_names = {str(path.relative_to(PROTO_DIR)) for path in PROTO_FILES}
    selected_files = {
        file.name: file for file in descriptor_set.file if file.name in selected_names
    }
    messages: dict[str, MessageInfo] = {}
    enums: dict[str, EnumInfo] = {}

    def visit_message(
        file: descriptor_pb2.FileDescriptorProto,
        message: descriptor_pb2.DescriptorProto,
        path: tuple[str, ...],
    ) -> None:
        info = MessageInfo(file, message, path)
        messages[info.full_name] = info
        for enum in message.enum_type:
            enum_info = EnumInfo(file, enum, (*path, enum.name))
            enums[enum_info.full_name] = enum_info
        for nested in message.nested_type:
            visit_message(file, nested, (*path, nested.name))

    for file in selected_files.values():
        for enum in file.enum_type:
            info = EnumInfo(file, enum, (enum.name,))
            enums[info.full_name] = info
        for message in file.message_type:
            visit_message(file, message, (message.name,))
    return selected_files, messages, enums


def _is_repeated(field: descriptor_pb2.FieldDescriptorProto) -> bool:
    return field.label == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED


def _has_presence(
    file: descriptor_pb2.FileDescriptorProto,
    field: descriptor_pb2.FieldDescriptorProto,
) -> bool:
    if _is_repeated(field):
        return False
    if field.type in (
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        descriptor_pb2.FieldDescriptorProto.TYPE_GROUP,
    ):
        return True
    return field.HasField("oneof_index") or file.syntax != "proto3"


def _reference_name(
    full_name: str,
    current_package: str,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    target: MessageInfo | EnumInfo
    if full_name in messages:
        target = messages[full_name]
    else:
        target = enums[full_name]
    if target.file.package == current_package:
        return target.python_name
    return f"{target.file.package}.{target.python_name}"


def _singular_annotation(
    field: descriptor_pb2.FieldDescriptorProto,
    current_package: str,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    if field.type in (
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        descriptor_pb2.FieldDescriptorProto.TYPE_GROUP,
        descriptor_pb2.FieldDescriptorProto.TYPE_ENUM,
    ):
        return _reference_name(
            field.type_name.removeprefix("."), current_package, messages, enums
        )
    if field.type in _INTEGER_BOUNDS:
        minimum, maximum = _INTEGER_BOUNDS[field.type]
        return f"Annotated[int, Field(ge={minimum}, le={maximum})]"
    return _SCALAR_TYPES[field.type]


def _annotation(
    info: MessageInfo,
    field: descriptor_pb2.FieldDescriptorProto,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE:
        target = messages[field.type_name.removeprefix(".")]
        if target.is_map_entry:
            fields = {item.name: item for item in target.descriptor.field}
            key = _singular_annotation(
                fields["key"], info.file.package, messages, enums
            )
            value = _singular_annotation(
                fields["value"], info.file.package, messages, enums
            )
            return f"dict[{key}, {value}]"

    result = _singular_annotation(field, info.file.package, messages, enums)
    if _is_repeated(field):
        return f"list[{result}]"
    if _has_presence(info.file, field):
        return f"{result} | None"
    return result


def _scalar_default(field: descriptor_pb2.FieldDescriptorProto) -> str:
    if field.HasField("default_value"):
        value = field.default_value
        if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_BOOL:
            return "True" if value.lower() == "true" else "False"
        if field.type in _INTEGER_BOUNDS:
            return str(int(value, 0))
        if field.type in (
            descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE,
            descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT,
        ):
            if value == "inf":
                return 'float("inf")'
            if value == "-inf":
                return 'float("-inf")'
            if value == "nan":
                return 'float("nan")'
            return repr(float(value))
        if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_BYTES:
            return repr(value.encode("latin1"))
        return repr(value)

    defaults = {
        descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE: "0.0",
        descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT: "0.0",
        descriptor_pb2.FieldDescriptorProto.TYPE_BOOL: "False",
        descriptor_pb2.FieldDescriptorProto.TYPE_STRING: '""',
        descriptor_pb2.FieldDescriptorProto.TYPE_BYTES: 'b""',
    }
    if field.type in _INTEGER_BOUNDS:
        return "0"
    return defaults[field.type]


def _default_expression(
    info: MessageInfo,
    field: descriptor_pb2.FieldDescriptorProto,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> tuple[str, str | None]:
    if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE:
        target = messages[field.type_name.removeprefix(".")]
        if target.is_map_entry:
            return "default_factory", "dict"
    if _is_repeated(field):
        return "default_factory", "list"
    if field.label == descriptor_pb2.FieldDescriptorProto.LABEL_REQUIRED:
        return "required", None
    if _has_presence(info.file, field):
        return "default", "None"
    if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_ENUM:
        enum = enums[field.type_name.removeprefix(".")]
        member_name = (
            field.default_value
            if field.HasField("default_value")
            else enum.descriptor.value[0].name
        )
        enum_name = _reference_name(
            enum.full_name, info.file.package, messages, enums
        )
        return "default", f"{enum_name}.{member_name}"
    return "default", _scalar_default(field)


def _render_enum(info: EnumInfo) -> list[str]:
    lines = [
        f'@_register_enum("{info.full_name}")',
        f"class {info.python_name}(ProtobufEnum):",
        f'    """Pydantic enum for ``{info.full_name}``."""',
        "",
    ]
    for value in info.descriptor.value:
        lines.append(f"    {value.name} = {value.number}")
    lines.append("")
    return lines


def _render_stub_enum(info: EnumInfo) -> list[str]:
    lines = [f"class {info.python_name}(ProtobufEnum):"]
    for value in info.descriptor.value:
        lines.append(f"    {value.name}: {info.python_name}")
    lines.append("")
    return lines


def _render_model(
    info: MessageInfo,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> list[str]:
    lines = [
        f'@_register_model("{info.full_name}")',
        f"class {info.python_name}(ProtobufModel):",
        f'    """Pydantic model for ``{info.full_name}``."""',
        "",
    ]
    content: list[str] = []
    for nested in info.descriptor.enum_type:
        nested_info = enums[f"{info.full_name}.{nested.name}"]
        content.append(
            f"    {nested.name}: ClassVar[type[{nested_info.python_name}]] = "
            f"{nested_info.python_name}"
        )
    for nested in info.descriptor.nested_type:
        nested_info = messages[f"{info.full_name}.{nested.name}"]
        if not nested_info.is_map_entry:
            content.append(
                f"    {nested.name}: ClassVar[type[{nested_info.python_name}]] = "
                f"{nested_info.python_name}"
            )
    used_names: set[str] = set()
    for field in info.descriptor.field:
        python_name = _python_field_name(field.name)
        while python_name in used_names:
            python_name += "_"
        used_names.add(python_name)
        annotation = _annotation(info, field, messages, enums)
        default_kind, default = _default_expression(info, field, messages, enums)
        arguments = [
            repr(field.name),
            repr(field.json_name or field.name),
            repr(f"{info.full_name}.{field.name}"),
            str(field.number),
        ]
        if default_kind != "required":
            arguments.append(f"{default_kind}={default}")
        content.append(
            f"    {python_name}: {annotation} = _protobuf_field({', '.join(arguments)})"
        )
    if not content:
        content.append("    pass")
    lines.extend(content)
    lines.append("")
    return lines


def _render_stub_model(
    info: MessageInfo,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> list[str]:
    lines = [f"class {info.python_name}(ProtobufModel):"]
    content: list[str] = []
    for nested in info.descriptor.enum_type:
        nested_info = enums[f"{info.full_name}.{nested.name}"]
        content.append(
            f"    {nested.name}: ClassVar[type[{nested_info.python_name}]]"
        )
    for nested in info.descriptor.nested_type:
        nested_info = messages[f"{info.full_name}.{nested.name}"]
        if not nested_info.is_map_entry:
            content.append(
                f"    {nested.name}: ClassVar[type[{nested_info.python_name}]]"
            )

    fields: list[tuple[str, str, bool]] = []
    used_names: set[str] = set()
    for field in info.descriptor.field:
        python_name = _python_field_name(field.name)
        while python_name in used_names:
            python_name += "_"
        used_names.add(python_name)
        annotation = _stub_annotation(info, field, messages, enums)
        default_kind, _ = _default_expression(info, field, messages, enums)
        fields.append((python_name, annotation, default_kind != "required"))
        content.append(f"    {python_name}: {annotation}")

    if fields:
        content.extend(
            [
                "    def __init__(",
                "        self,",
                "        *,",
                *(
                    f"        {name}: {annotation}{' = ...' if has_default else ''},"
                    for name, annotation, has_default in fields
                ),
                "    ) -> None: ...",
            ]
        )
    else:
        content.append("    def __init__(self) -> None: ...")
    lines.extend(content)
    lines.append("")
    return lines


def _message_order(
    file: descriptor_pb2.FileDescriptorProto,
    messages: dict[str, MessageInfo],
) -> list[MessageInfo]:
    result: list[MessageInfo] = []

    def visit(info: MessageInfo) -> None:
        for nested in info.descriptor.nested_type:
            nested_info = messages[f"{info.full_name}.{nested.name}"]
            if not nested_info.is_map_entry:
                visit(nested_info)
        result.append(info)

    for descriptor in file.message_type:
        visit(messages[f"{file.package}.{descriptor.name}"])
    return result


def _enum_order(
    file: descriptor_pb2.FileDescriptorProto,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> list[EnumInfo]:
    result = [enums[f"{file.package}.{descriptor.name}"] for descriptor in file.enum_type]

    def visit(info: MessageInfo) -> None:
        result.extend(
            enums[f"{info.full_name}.{descriptor.name}"]
            for descriptor in info.descriptor.enum_type
        )
        for nested in info.descriptor.nested_type:
            nested_info = messages[f"{info.full_name}.{nested.name}"]
            if not nested_info.is_map_entry:
                visit(nested_info)

    for descriptor in file.message_type:
        visit(messages[f"{file.package}.{descriptor.name}"])
    return result


def _stub_singular_annotation(
    field: descriptor_pb2.FieldDescriptorProto,
    current_package: str,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    if field.type in (
        descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        descriptor_pb2.FieldDescriptorProto.TYPE_GROUP,
        descriptor_pb2.FieldDescriptorProto.TYPE_ENUM,
    ):
        return _reference_name(
            field.type_name.removeprefix("."), current_package, messages, enums
        )
    if field.type in _INTEGER_BOUNDS:
        return "int"
    return _SCALAR_TYPES[field.type]


def _stub_annotation(
    info: MessageInfo,
    field: descriptor_pb2.FieldDescriptorProto,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    if field.type == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE:
        target = messages[field.type_name.removeprefix(".")]
        if target.is_map_entry:
            fields = {item.name: item for item in target.descriptor.field}
            key = _stub_singular_annotation(
                fields["key"], info.file.package, messages, enums
            )
            value = _stub_singular_annotation(
                fields["value"], info.file.package, messages, enums
            )
            return f"dict[{key}, {value}]"

    result = _stub_singular_annotation(field, info.file.package, messages, enums)
    if _is_repeated(field):
        return f"list[{result}]"
    if _has_presence(info.file, field):
        return f"{result} | None"
    return result


def _render_module(
    file: descriptor_pb2.FileDescriptorProto,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    imports = [
        "# @generated by scripts/pydanticgen.py; DO NOT EDIT.",
        f'"""Concrete Pydantic models for Sliver package ``{file.package}``."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Annotated, ClassVar",
        "",
        "from pydantic import Field",
        "",
    ]
    dependency_packages = sorted(
        {
            dependency.split("/", 1)[0]
            for dependency in file.dependency
            if dependency.endswith(".proto")
            and dependency.split("/", 1)[0]
            in {"commonpb", "sliverpb", "clientpb"}
        }
    )
    for package in dependency_packages:
        imports.append(f"from . import {package}")
    if dependency_packages:
        imports.append("")
    imports.extend(
        [
            "from ._runtime import (",
            "    ProtobufEnum,",
            "    ProtobufModel,",
            "    _protobuf_field,",
            "    _register_enum,",
            "    _register_model,",
            ")",
            "",
        ]
    )
    lines = imports
    public_enums = [descriptor.name for descriptor in file.enum_type]
    for info in _enum_order(file, messages, enums):
        lines.extend(_render_enum(info))
    for info in _message_order(file, messages):
        lines.extend(_render_model(info, messages, enums))
    public_models = [descriptor.name for descriptor in file.message_type]
    exported = [*public_enums, *public_models]
    lines.append("__all__ = [")
    lines.extend(f'    "{name}",' for name in sorted(exported))
    lines.extend(["]", ""])
    return "\n".join(lines)


def _render_stub_module(
    file: descriptor_pb2.FileDescriptorProto,
    messages: dict[str, MessageInfo],
    enums: dict[str, EnumInfo],
) -> str:
    has_nested_types = any(
        info.descriptor.enum_type
        or any(not messages[f"{info.full_name}.{nested.name}"].is_map_entry for nested in info.descriptor.nested_type)
        for info in messages.values()
        if info.file.name == file.name and not info.is_map_entry
    )
    lines = [
        "# @generated by scripts/pydanticgen.py; DO NOT EDIT.",
        f'"""Static types for the concrete models in ``{file.package}``."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    if has_nested_types:
        lines.extend(["from typing import ClassVar", ""])
    dependency_packages = sorted(
        {
            dependency.split("/", 1)[0]
            for dependency in file.dependency
            if dependency.endswith(".proto")
            and dependency.split("/", 1)[0]
            in {"commonpb", "sliverpb", "clientpb"}
        }
    )
    for package in dependency_packages:
        lines.append(f"from . import {package} as {package}")
    if dependency_packages:
        lines.append("")
    runtime_imports = ["ProtobufModel"]
    if file.enum_type or any(
        info.descriptor.enum_type
        for info in messages.values()
        if info.file.name == file.name
    ):
        runtime_imports.insert(0, "ProtobufEnum")
    if len(runtime_imports) == 1:
        lines.extend(["from ._runtime import ProtobufModel", ""])
    else:
        lines.extend(
            [
                "from ._runtime import (",
                *(f"    {name}," for name in runtime_imports),
                ")",
                "",
            ]
        )

    for info in _enum_order(file, messages, enums):
        lines.extend(_render_stub_enum(info))
    for info in _message_order(file, messages):
        lines.extend(_render_stub_model(info, messages, enums))
    exported = [
        *(descriptor.name for descriptor in file.enum_type),
        *(descriptor.name for descriptor in file.message_type),
    ]
    lines.append("__all__ = [")
    lines.extend(f'    "{name}",' for name in sorted(exported))
    lines.extend(["]", ""])
    return "\n".join(lines)


def _format_generated(directory: Path) -> None:
    ruff = shutil.which("ruff")
    if ruff is None:
        candidate = Path(sys.executable).with_name("ruff")
        if candidate.is_file():
            ruff = str(candidate)
    if ruff is None:
        raise RuntimeError("ruff is required to format generated Pydantic modules")
    generated_paths = [str(directory / name) for name in GENERATED_FILES]
    subprocess.run(
        [ruff, "check", "--fix", *generated_paths],
        check=True,
    )
    subprocess.run(
        [ruff, "format", *generated_paths],
        check=True,
    )


def _generate_candidate(directory: Path) -> None:
    descriptor_set = _descriptor_set()
    selected_files, messages, enums = _index_descriptors(descriptor_set)
    directory.mkdir(parents=True, exist_ok=True)
    for package in GENERATED_MODULES:
        file = next(item for item in selected_files.values() if item.package == package)
        (directory / f"{package}.py").write_text(
            _render_module(file, messages, enums), encoding="utf-8"
        )
        (directory / f"{package}.pyi").write_text(
            _render_stub_module(file, messages, enums), encoding="utf-8"
        )
    _format_generated(directory)


def generate_models(*, check: bool = False) -> bool:
    with tempfile.TemporaryDirectory(prefix="sliver-py-pydantic-") as temp_dir:
        candidate_dir = Path(temp_dir)
        _generate_candidate(candidate_dir)
        changed = [
            name
            for name in GENERATED_FILES
            if not (OUT_DIR / name).is_file()
            or (OUT_DIR / name).read_bytes() != (candidate_dir / name).read_bytes()
        ]
        if check:
            if changed:
                print("Generated Pydantic modules are stale: " + ", ".join(changed))
                return False
            print("Generated Pydantic modules are up to date")
            return True
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for name in GENERATED_FILES:
            shutil.copy2(candidate_dir / name, OUT_DIR / name)
        print(f"Generated concrete Pydantic modules in {OUT_DIR}")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when checked-in generated modules differ",
    )
    args = parser.parse_args()
    if not generate_models(check=args.check):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
