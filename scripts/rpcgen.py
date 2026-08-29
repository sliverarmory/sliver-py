#!/usr/bin/env python3
"""Generate the statically typed Pydantic Sliver RPC method table."""

from __future__ import annotations

import argparse
import keyword
import re
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
OUTPUT_IMPLEMENTATION_FILE = ROOT_DIR / "src" / "sliver" / "_rpc_generated.py"
OUTPUT_STUB_FILE = ROOT_DIR / "src" / "sliver" / "_rpc_generated.pyi"

_CALL_TYPES = {
    (False, False): "UnaryUnaryMultiCallable",
    (False, True): "UnaryStreamMultiCallable",
    (True, False): "StreamUnaryMultiCallable",
    (True, True): "StreamStreamMultiCallable",
}
_MODEL_PACKAGES = {"clientpb", "commonpb", "sliverpb"}
_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_ACRONYM_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")


def _python_method_name(rpc_name: str) -> str:
    """Convert an upstream RPC name to its public Python spelling."""

    name = _CAMEL_BOUNDARY.sub(r"\1_\2", rpc_name)
    name = _ACRONYM_BOUNDARY.sub(r"\1_\2", name).lower()
    return f"{name}_" if keyword.iskeyword(name) else name


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


def _render_implementation(
    methods: list[descriptor_pb2.MethodDescriptorProto],
) -> str:
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
        python_name = _python_method_name(method.name)
        lines.append(f"    {python_name}: {call_type}[{request_type}, {response_type}]")
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
        python_name = _python_method_name(method.name)
        lines.extend(
            [
                f"        self.{python_name} = {call_type}(",
                f"            raw.{method.name},",
                f"            {request_type},",
                f"            {response_type},",
                f'            "{method.name}",',
                "        )",
                f"        self.{method.name} = self.{python_name}",
            ]
        )

    lines.extend(["", f"RPC_METHOD_COUNT = {len(methods)}", ""])
    return "\n".join(lines)


def _render_stub(methods: list[descriptor_pb2.MethodDescriptorProto]) -> str:
    call_types = sorted(
        {
            _CALL_TYPES[(method.client_streaming, method.server_streaming)]
            for method in methods
        }
    )
    lines = [
        '"""Generated static Pydantic RPC declarations. Do not edit manually."""',
        "",
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
        python_name = _python_method_name(method.name)
        lines.append(f"    {python_name}: {call_type}[{request_type}, {response_type}]")
        lines.append(f"    {method.name}: {call_type}[{request_type}, {response_type}]")

    lines.extend(
        [
            "",
            "    def _initialize_rpc_methods(self, raw: object) -> None: ...",
            "",
            "",
            "RPC_METHOD_COUNT: int",
            "",
        ]
    )
    return "\n".join(lines)


def _format_source(source: str, output_file: Path) -> str:
    ruff = shutil.which("ruff")
    if ruff is None:
        candidate = Path(sys.executable).with_name("ruff")
        if candidate.is_file():
            ruff = str(candidate)
    if ruff is None:
        raise RuntimeError("ruff is required to format the generated RPC surface")

    with tempfile.TemporaryDirectory(prefix="sliver-py-rpc-format-") as temp_dir:
        candidate_path = Path(temp_dir) / output_file.name
        candidate_path.write_text(source)
        subprocess.run([ruff, "format", candidate_path], check=True)
        return candidate_path.read_text()


def generate_rpc_surface(*, check: bool = False) -> bool:
    methods = list(_service_descriptor().method)
    generated_files = {
        OUTPUT_IMPLEMENTATION_FILE: _format_source(
            _render_implementation(methods), OUTPUT_IMPLEMENTATION_FILE
        ),
        OUTPUT_STUB_FILE: _format_source(_render_stub(methods), OUTPUT_STUB_FILE),
    }
    stale_files = [
        output_file
        for output_file, generated in generated_files.items()
        if not output_file.is_file() or output_file.read_text() != generated
    ]
    if check:
        if stale_files:
            stale_names = ", ".join(path.name for path in stale_files)
            print(f"Generated Pydantic RPC surface is stale: {stale_names}")
            return False
        print("Generated Pydantic RPC surface is up to date")
        return True

    for output_file, generated in generated_files.items():
        output_file.write_text(generated)
    output_names = ", ".join(path.name for path in generated_files)
    print(f"Generated Pydantic RPC surface in {output_names}")
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
