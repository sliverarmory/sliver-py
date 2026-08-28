#!/usr/bin/env python3
"""Generate the statically typed Pydantic Sliver RPC method table."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path

from google.protobuf import descriptor_pb2
from grpc_tools import protoc

ROOT_DIR = Path(__file__).resolve().parents[1]
PROTO_DIR = ROOT_DIR / "sliver" / "protobuf"
SERVICE_PROTO = PROTO_DIR / "rpcpb" / "services.proto"
OUTPUT_FILE = ROOT_DIR / "src" / "sliver" / "_rpc_generated.py"

_CALL_TYPES = {
    (False, False): "UnaryUnaryMultiCallable",
    (False, True): "UnaryStreamMultiCallable",
    (True, False): "StreamUnaryMultiCallable",
    (True, True): "StreamStreamMultiCallable",
}
_MODEL_PACKAGES = {"clientpb", "commonpb", "sliverpb"}


def _service_descriptor() -> descriptor_pb2.ServiceDescriptorProto:
    with tempfile.TemporaryDirectory(prefix="sliver-py-rpc-") as temp_dir:
        descriptor_path = Path(temp_dir) / "services.pb"
        grpc_include = Path(str(files("grpc_tools") / "_proto"))
        result = protoc.main(
            [
                "grpc_tools.protoc",
                f"-I{grpc_include}",
                f"-I{PROTO_DIR}",
                f"--descriptor_set_out={descriptor_path}",
                "--include_imports",
                str(SERVICE_PROTO),
            ]
        )
        if result != 0:
            raise RuntimeError("protoc failed while loading the Sliver RPC service")
        descriptor_set = descriptor_pb2.FileDescriptorSet.FromString(
            descriptor_path.read_bytes()
        )

    services_file = next(
        (
            descriptor
            for descriptor in descriptor_set.file
            if descriptor.name == "rpcpb/services.proto"
        ),
        None,
    )
    if services_file is None:
        raise RuntimeError("descriptor set does not contain rpcpb/services.proto")
    service = next(
        (service for service in services_file.service if service.name == "SliverRPC"),
        None,
    )
    if service is None:
        raise RuntimeError("rpcpb/services.proto does not define SliverRPC")
    return service


def _model_expression(full_name: str) -> str:
    parts = full_name.removeprefix(".").split(".")
    if len(parts) < 2 or parts[0] not in _MODEL_PACKAGES:
        raise ValueError(f"unsupported Sliver RPC model {full_name!r}")
    return ".".join(parts)


def _render() -> str:
    methods = list(_service_descriptor().method)
    call_types = sorted(
        {
            _CALL_TYPES[(method.client_streaming, method.server_streaming)]
            for method in methods
        }
    )
    lines = [
        '"""Generated Pydantic RPC declarations. Do not edit manually."""',
        "",
        "from __future__ import annotations",
        "",
        "from ._pb.rpcpb.services_pb2_grpc import (",
        "    SliverRPCStub as _WireSliverRPCStub,",
        ")",
        "from ._rpc_base import (",
        *(f"    {call_type}," for call_type in call_types),
        ")",
        "from .models import clientpb, commonpb, sliverpb",
        "",
        "",
        "class GeneratedPydanticSliverRPCStub:",
        '    """Concrete Pydantic method declarations generated from SliverRPC."""',
        "",
    ]

    for method in methods:
        call_type = _CALL_TYPES[(method.client_streaming, method.server_streaming)]
        request_type = _model_expression(method.input_type)
        response_type = _model_expression(method.output_type)
        lines.append(f"    {method.name}: {call_type}[{request_type}, {response_type}]")

    lines.extend(
        [
            "",
            "    def _initialize_rpc_methods(",
            "        self, raw: _WireSliverRPCStub",
            "    ) -> None:",
        ]
    )
    for method in methods:
        call_type = _CALL_TYPES[(method.client_streaming, method.server_streaming)]
        request_type = _model_expression(method.input_type)
        response_type = _model_expression(method.output_type)
        lines.extend(
            [
                f"        self.{method.name} = {call_type}(",
                f"            raw.{method.name},",
                f"            {request_type},",
                f"            {response_type},",
                "        )",
            ]
        )

    lines.extend(["", f"RPC_METHOD_COUNT = {len(methods)}", ""])
    return "\n".join(lines)


def _format_source(source: str) -> str:
    ruff = shutil.which("ruff")
    if ruff is None:
        candidate = Path(sys.executable).with_name("ruff")
        if candidate.is_file():
            ruff = str(candidate)
    if ruff is None:
        raise RuntimeError("ruff is required to format the generated RPC surface")

    with tempfile.TemporaryDirectory(prefix="sliver-py-rpc-format-") as temp_dir:
        candidate_path = Path(temp_dir) / OUTPUT_FILE.name
        candidate_path.write_text(source)
        subprocess.run([ruff, "format", candidate_path], check=True)
        return candidate_path.read_text()


def generate_rpc_surface(*, check: bool = False) -> bool:
    generated = _format_source(_render())
    changed = not OUTPUT_FILE.is_file() or OUTPUT_FILE.read_text() != generated
    if check:
        if changed:
            print("Generated Pydantic RPC surface is stale")
            return False
        print("Generated Pydantic RPC surface is up to date")
        return True

    OUTPUT_FILE.write_text(generated)
    print(f"Generated Pydantic RPC surface in {OUTPUT_FILE}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the checked-in generated RPC surface is stale",
    )
    args = parser.parse_args()
    if not generate_rpc_surface(check=args.check):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
