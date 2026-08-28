#!/usr/bin/env python3
"""Regenerate Sliver's Python gRPC bindings from the pinned submodule."""

from __future__ import annotations

import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

from grpc_tools import protoc

ROOT_DIR = Path(__file__).resolve().parents[1]
PROTO_DIR = ROOT_DIR / "sliver" / "protobuf"
OUT_DIR = ROOT_DIR / "src" / "sliver" / "_pb"

PROTO_FILES = (
    PROTO_DIR / "commonpb" / "common.proto",
    PROTO_DIR / "sliverpb" / "sliver.proto",
    PROTO_DIR / "clientpb" / "client.proto",
    PROTO_DIR / "rpcpb" / "services.proto",
)

PACKAGE_IMPORTS = {
    "from commonpb import common_pb2": "from ..commonpb import common_pb2",
    "from sliverpb import sliver_pb2": "from ..sliverpb import sliver_pb2",
    "from clientpb import client_pb2": "from ..clientpb import client_pb2",
    "import commonpb.common_pb2": "from ..commonpb import common_pb2",
    "import sliverpb.sliver_pb2": "from ..sliverpb import sliver_pb2",
    "import clientpb.client_pb2": "from ..clientpb import client_pb2",
    "commonpb.common_pb2": "common_pb2",
    "sliverpb.sliver_pb2": "sliver_pb2",
    "clientpb.client_pb2": "client_pb2",
}


def _run_protoc(output_dir: Path) -> None:
    grpc_include = Path(str(files("grpc_tools") / "_proto"))
    common_args = [
        "grpc_tools.protoc",
        f"-I{grpc_include}",
        f"-I{PROTO_DIR}",
        f"--python_out={output_dir}",
        f"--mypy_out=readable_stubs:{output_dir}",
    ]

    message_protos = [path for path in PROTO_FILES if path.name != "services.proto"]
    if protoc.main([*common_args, *(str(path) for path in message_protos)]) != 0:
        raise RuntimeError("protoc failed while generating protobuf messages")

    service_proto = PROTO_DIR / "rpcpb" / "services.proto"
    service_args = [
        *common_args,
        f"--grpc_python_out={output_dir}",
        f"--mypy_grpc_out={output_dir}",
        str(service_proto),
    ]
    if protoc.main(service_args) != 0:
        raise RuntimeError("protoc failed while generating gRPC services")


def _rewrite_package_imports(output_dir: Path) -> None:
    for generated_file in output_dir.glob("**/*_pb2*.py*"):
        content = generated_file.read_text()
        for absolute, relative in PACKAGE_IMPORTS.items():
            content = content.replace(absolute, relative)
        content = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
        generated_file.write_text(content)


def _replace_generated_tree(candidate_dir: Path) -> None:
    generated_names = {path.name for path in candidate_dir.glob("**/*_pb2*.py*")}
    for old_file in OUT_DIR.glob("**/*_pb2*.py*"):
        if old_file.name in generated_names or old_file.name.startswith(
            ("common_pb2", "sliver_pb2", "client_pb2", "services_pb2")
        ):
            old_file.unlink()

    for package in ("commonpb", "sliverpb", "clientpb", "rpcpb"):
        source_package = candidate_dir / package
        target_package = OUT_DIR / package
        target_package.mkdir(parents=True, exist_ok=True)
        (target_package / "__init__.py").touch(exist_ok=True)
        for generated_file in source_package.glob("*_pb2*.py*"):
            shutil.copy2(generated_file, target_package / generated_file.name)


def main() -> None:
    missing = [path for path in PROTO_FILES if not path.is_file()]
    if missing:
        missing_names = ", ".join(str(path.relative_to(ROOT_DIR)) for path in missing)
        raise FileNotFoundError(f"missing protobuf sources: {missing_names}")

    with tempfile.TemporaryDirectory(prefix="sliver-py-protobuf-") as temp_dir:
        candidate_dir = Path(temp_dir)
        _run_protoc(candidate_dir)
        _rewrite_package_imports(candidate_dir)
        _replace_generated_tree(candidate_dir)

    print(f"Generated Python protobuf and gRPC bindings in {OUT_DIR}")


if __name__ == "__main__":
    main()
