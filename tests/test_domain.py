from __future__ import annotations

import platform
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from sliver.domain import (
    BeaconOptions,
    C2Endpoint,
    GeneratedImplant,
    ImplantSpec,
    Inventory,
    ShellcodeOptions,
    Target,
)
from sliver.enums import (
    GOARCH,
    GOOS,
    C2Protocol,
    ConnectionStrategy,
    EventType,
    LogonType,
    OutputFormat,
    PortForwardProtocol,
    RegistryHive,
    RegistryType,
    ShellcodeBypass,
    ShellcodeCompression,
    ShellcodeEncoder,
    ShellcodeEntropy,
    ShellcodeExitOption,
    ShellcodeHeaders,
)
from sliver.errors import CommandError, UnsupportedTargetError, raise_for_command_error
from sliver.models import clientpb, commonpb, sliverpb


def test_generated_enums_are_reexported_instead_of_duplicated() -> None:
    assert OutputFormat is clientpb.OutputFormat
    assert ShellcodeEncoder is clientpb.ShellcodeEncoder
    assert RegistryType is sliverpb.RegistryType


def test_canonical_enum_values() -> None:
    assert GOOS.WINDOWS == "windows"
    assert GOARCH.I386 == "386"
    assert ConnectionStrategy.RANDOM_DOMAIN == "rd"
    assert C2Protocol.NAMED_PIPE == "namedpipe"
    assert C2Protocol.TCP_PIVOT == "tcppivot"
    assert EventType.UPDATE == "update"
    assert EventType.BEACON_TASK_RESULT == "beacon-taskresult"
    assert RegistryHive.CURRENT_USER == "HKCU"
    assert PortForwardProtocol.UNSPECIFIED == 0
    assert PortForwardProtocol.UDP == 2
    assert LogonType.NEW_CREDENTIALS == 9
    assert ShellcodeEntropy.RANDOM_NAMES_AND_ENCRYPTION == 3
    assert ShellcodeCompression.APLIB == 2
    assert ShellcodeExitOption.BLOCK == 3
    assert ShellcodeBypass.CONTINUE_ON_FAILURE == 3
    assert ShellcodeHeaders.KEEP == 2


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Darwin", "arm64", Target(os=GOOS.DARWIN, arch=GOARCH.ARM64)),
        ("Linux", "x86_64", Target(os=GOOS.LINUX, arch=GOARCH.AMD64)),
        ("Windows", "i686", Target(os=GOOS.WINDOWS, arch=GOARCH.I386)),
    ],
)
def test_target_current_maps_host_names(
    monkeypatch: pytest.MonkeyPatch,
    system: str,
    machine: str,
    expected: Target,
) -> None:
    monkeypatch.setattr(platform, "system", lambda: system)
    monkeypatch.setattr(platform, "machine", lambda: machine)

    assert Target.current() == expected


def test_target_current_rejects_unknown_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Plan9")
    monkeypatch.setattr(platform, "machine", lambda: "mips")

    with pytest.raises(UnsupportedTargetError, match="plan9/mips"):
        Target.current()


def test_target_accepts_go_field_aliases_for_compatibility() -> None:
    target = Target(goos=GOOS.LINUX, goarch=GOARCH.ARM64)

    assert target.os is GOOS.LINUX
    assert target.arch is GOARCH.ARM64
    assert target.goos is target.os
    assert target.goarch is target.arch


def test_c2_factories_emit_canonical_urls_and_support_ipv6() -> None:
    assert C2Endpoint.mtls("c2.example").url == "mtls://c2.example:8888"
    assert C2Endpoint.wireguard("c2.example").url == "wg://c2.example:53"
    assert C2Endpoint.http("c2.example").url == "http://c2.example:80"
    assert C2Endpoint.https("c2.example").url == "https://c2.example:443"
    assert C2Endpoint.dns("c2.example").url == "dns://c2.example"
    assert (
        C2Endpoint.named_pipe(".", "demo pipe").url == "namedpipe://./pipe/demo%20pipe"
    )
    assert C2Endpoint.tcp_pivot("::1").url == "tcppivot://[::1]:9898"


def test_c2_from_url_adds_sliver_default_ports() -> None:
    endpoint = C2Endpoint.from_url("mtls://c2.example")

    assert endpoint.protocol is C2Protocol.MTLS
    assert endpoint.url == "mtls://c2.example:8888"


def test_c2_validation_rejects_noncanonical_or_mismatched_schemes() -> None:
    with pytest.raises(ValueError, match="unsupported C2 URL scheme"):
        C2Endpoint.from_url("named-pipe://./pipe/demo")
    with pytest.raises(ValidationError, match="does not match"):
        C2Endpoint(protocol=C2Protocol.MTLS, url="https://c2.example")


def test_implant_spec_converts_defaults_and_list_priorities() -> None:
    spec = ImplantSpec(
        target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
        c2=[
            C2Endpoint.mtls("one.example"),
            C2Endpoint.https("two.example"),
            C2Endpoint.dns("three.example", priority=17),
        ],
        beacon=BeaconOptions(),
        canary_domains=["canary.example"],
    )

    config = spec.to_implant_config()

    assert isinstance(config, clientpb.ImplantConfig)
    assert config.goos == "linux"
    assert config.goarch == "amd64"
    assert config.is_beacon is True
    assert config.beacon_interval == 60_000_000_000
    assert config.beacon_jitter == 30_000_000_000
    assert [endpoint.priority for endpoint in config.c2] == [0, 1, 17]
    assert config.connection_strategy == "s"
    assert config.reconnect_interval == 60_000_000_000
    assert config.poll_timeout == 360_000_000_000
    assert config.include_mtls is True
    assert config.include_http is True
    assert config.include_dns is True
    assert config.include_wg is False
    assert config.canary_domains == ["canary.example."]
    assert config.format is OutputFormat.EXECUTABLE
    assert config.httpc2_config_name == "default"
    assert config.net_go_enabled is False


def test_beacon_options_accept_fast_positive_intervals_without_magic_floor() -> None:
    options = BeaconOptions(interval=timedelta(seconds=1), jitter=timedelta())

    assert options.interval == timedelta(seconds=1)
    with pytest.raises(ValidationError, match="greater than zero"):
        BeaconOptions(interval=timedelta(), jitter=timedelta())


def test_implant_spec_preserves_unmanaged_base_fields() -> None:
    base = clientpb.ImplantConfig(
        extension=".custom",
        traffic_encoders_enabled=True,
        traffic_encoders=["encoder-a"],
    )
    spec = ImplantSpec(
        target=Target(os=GOOS.LINUX, arch=GOARCH.ARM64),
        c2=[C2Endpoint.https("c2.example")],
    )

    converted = spec.to_implant_config(base=base)

    assert converted is not base
    assert converted.extension == ".custom"
    assert converted.traffic_encoders_enabled is True
    assert converted.traffic_encoders == ["encoder-a"]
    assert base.goos == ""


def test_implant_spec_converts_shellcode_options_and_generate_request() -> None:
    spec = ImplantSpec(
        target=Target(os=GOOS.WINDOWS, arch=GOARCH.AMD64),
        c2=[C2Endpoint.mtls("c2.example")],
        output_format=OutputFormat.SHELLCODE,
        shellcode=ShellcodeOptions(
            entropy=ShellcodeEntropy.RANDOM_NAMES_AND_ENCRYPTION,
            compression=ShellcodeCompression.APLIB,
            bypass=ShellcodeBypass.ABORT_ON_FAILURE,
        ),
        shellcode_encoder=ShellcodeEncoder.XOR,
    )

    request = spec.to_generate_request(name="quiet-river")

    assert isinstance(request, clientpb.GenerateReq)
    assert request.name == "quiet-river"
    assert request.config is not None
    assert request.config.is_shellcode is True
    assert request.config.shellcode_config is not None
    assert request.config.shellcode_config.entropy == 3
    assert request.config.shellcode_config.compress == 2
    assert request.config.shellcode_config.bypass == 2
    assert request.config.shellcode_encoder is ShellcodeEncoder.XOR


def test_non_windows_shellcode_emits_only_the_supported_compression_option() -> None:
    spec = ImplantSpec(
        target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
        c2=[C2Endpoint.mtls("c2.example")],
        output_format=OutputFormat.SHELLCODE,
        shellcode=ShellcodeOptions(compression=ShellcodeCompression.APLIB),
    )

    config = spec.to_implant_config()

    assert config.shellcode_config == clientpb.ShellcodeConfig(compress=2)


def test_implant_spec_rejects_incompatible_options() -> None:
    linux = Target(os=GOOS.LINUX, arch=GOARCH.AMD64)
    with pytest.raises(ValidationError, match="named-pipe"):
        ImplantSpec(
            target=linux,
            c2=[C2Endpoint.named_pipe(".", "demo")],
        )
    with pytest.raises(ValidationError, match="named-pipe"):
        ImplantSpec(
            target=linux,
            c2=[C2Endpoint.mtls("c2.example")],
            include_protocols={C2Protocol.NAMED_PIPE},
        )
    with pytest.raises(ValidationError, match="shellcode options"):
        ImplantSpec(
            target=linux,
            c2=[C2Endpoint.mtls("c2.example")],
            shellcode=ShellcodeOptions(),
        )
    with pytest.raises(ValidationError, match="only support the compression"):
        ImplantSpec(
            target=linux,
            c2=[C2Endpoint.mtls("c2.example")],
            output_format=OutputFormat.SHELLCODE,
            shellcode=ShellcodeOptions(thread=True),
        )


def test_generated_implant_round_trip_and_exclusive_save(tmp_path: Path) -> None:
    generated = clientpb.Generate(
        file=commonpb.File(name="../../payload.bin", data=b"payload"),
        implant_name="quiet-river",
        implant_build_id="build-id",
    )
    result = GeneratedImplant.from_generate(generated)

    destination = result.save(tmp_path)

    assert isinstance(result, BaseModel)
    assert destination == tmp_path / "payload.bin"
    assert destination.read_bytes() == b"payload"
    assert destination.stat().st_mode & 0o777 == 0o700
    assert result.to_generate() == generated
    with pytest.raises(FileExistsError):
        result.save(destination)


def test_inventory_is_a_pydantic_aggregate() -> None:
    inventory = Inventory(
        version=clientpb.Version(major=1),
        sessions=[clientpb.Session(id="session-id")],
        beacons=[clientpb.Beacon(id="beacon-id")],
        jobs=[clientpb.Job(id=1)],
        operators=[clientpb.Operator(name="operator")],
    )

    assert isinstance(inventory, BaseModel)
    assert inventory.sessions[0].id == "session-id"
    assert inventory.beacons[0].id == "beacon-id"


def test_raise_for_command_error_returns_the_original_typed_model() -> None:
    result = sliverpb.Ping(nonce=7, response=commonpb.Response())

    assert (
        raise_for_command_error(result, operation="ping", target_id="target") is result
    )


def test_raise_for_command_error_exposes_operation_target_and_result() -> None:
    result = sliverpb.Ping(
        nonce=7,
        response=commonpb.Response(err="implant rejected the command"),
    )

    with pytest.raises(CommandError, match="implant rejected") as raised:
        raise_for_command_error(result, operation="ping", target_id="target")

    assert raised.value.operation == "ping"
    assert raised.value.target_id == "target"
    assert raised.value.result is result
