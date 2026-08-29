from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar, cast
from unittest.mock import AsyncMock

import pytest

from sliver import InteractiveBeacon, InteractiveSession, models
from sliver._protocols import RequestRoutedModel
from sliver._rpc import PydanticSliverRPCStub
from sliver.enums import GOOS, LogonType, RegistryHive
from sliver.interactive import BaseInteractiveCommands
from sliver.models import ProtobufModel

_RequestT = TypeVar("_RequestT", bound=RequestRoutedModel)
_ResultT = TypeVar("_ResultT", bound=ProtobufModel)
_Command = Callable[..., Awaitable[ProtobufModel]]


class _RecordingInteractive(BaseInteractiveCommands):
    timeout = 60

    def __init__(self) -> None:
        self.calls: list[tuple[str, ProtobufModel]] = []

    def _request(self, model: _RequestT) -> _RequestT:
        return model

    async def _execute(
        self,
        rpc_name: str,
        request: RequestRoutedModel,
        result_type: type[_ResultT],
    ) -> _ResultT:
        assert isinstance(request, ProtobufModel)
        self.calls.append((rpc_name, request))
        return result_type()


@pytest.mark.parametrize(
    ("primary", "compatibility", "arguments"),
    [
        ("procdump", "process_dump", (42,)),
        ("rev2self", "revert_to_self", ()),
        (
            "msf_inject",
            "msf_remote",
            ("meterpreter_reverse_https", "127.0.0.1", 4444, "", 1, 1234),
        ),
        ("env", "get_env", ("PATH",)),
        ("env_set", "set_env", ("NAME", "value")),
        ("env_unset", "unset_env", ("NAME",)),
        ("wasm_ls", "wasm_list", ()),
    ],
)
async def test_command_and_compatibility_spellings_produce_the_same_request(
    primary: str,
    compatibility: str,
    arguments: tuple[object, ...],
) -> None:
    interactive = _RecordingInteractive()
    primary_method = cast(_Command, getattr(interactive, primary))
    compatibility_method = cast(_Command, getattr(interactive, compatibility))

    await primary_method(*arguments)
    primary_call = interactive.calls.pop()
    await compatibility_method(*arguments)
    compatibility_call = interactive.calls.pop()

    assert compatibility_call[0] == primary_call[0]
    assert type(compatibility_call[1]) is type(primary_call[1])
    assert compatibility_call[1].model_dump() == primary_call[1].model_dump()


async def test_ping_and_ps_forward_optional_command_values() -> None:
    interactive = _RecordingInteractive()

    ping = await interactive.ping(8675309)
    rpc_name, ping_request = interactive.calls.pop()
    assert rpc_name == "Ping"
    assert isinstance(ping, models.sliverpb.Ping)
    assert isinstance(ping_request, models.sliverpb.Ping)
    assert ping_request.nonce == 8675309

    processes = await interactive.ps(full_info=True)
    rpc_name, ps_request = interactive.calls.pop()
    assert rpc_name == "Ps"
    assert isinstance(processes, models.sliverpb.Ps)
    assert isinstance(ps_request, models.sliverpb.PsReq)
    assert ps_request.full_info is True


async def test_portable_filesystem_commands_build_complete_requests() -> None:
    interactive = _RecordingInteractive()

    moved = await interactive.mv("old.txt", "moved.txt")
    rpc_name, move_request = interactive.calls.pop()
    assert rpc_name == "Mv"
    assert isinstance(moved, models.sliverpb.Mv)
    assert isinstance(move_request, models.sliverpb.MvReq)
    assert (move_request.src, move_request.dst) == ("old.txt", "moved.txt")

    copied = await interactive.cp("moved.txt", "copy.txt")
    rpc_name, copy_request = interactive.calls.pop()
    assert rpc_name == "Cp"
    assert isinstance(copied, models.sliverpb.Cp)
    assert isinstance(copy_request, models.sliverpb.CpReq)
    assert (copy_request.src, copy_request.dst) == ("moved.txt", "copy.txt")

    matches = await interactive.grep(
        "needle.*",
        "data",
        recursive=True,
        lines_before=2,
        lines_after=3,
    )
    rpc_name, grep_request = interactive.calls.pop()
    assert rpc_name == "Grep"
    assert isinstance(matches, models.sliverpb.Grep)
    assert isinstance(grep_request, models.sliverpb.GrepReq)
    assert grep_request.search_pattern == "needle.*"
    assert grep_request.path == "data"
    assert grep_request.recursive is True
    assert grep_request.lines_before == 2
    assert grep_request.lines_after == 3

    changed = await interactive.chtimes("copy.txt", 1_700_000_000, 1_700_000_001)
    rpc_name, chtimes_request = interactive.calls.pop()
    assert rpc_name == "Chtimes"
    assert isinstance(changed, models.sliverpb.Chtimes)
    assert isinstance(chtimes_request, models.sliverpb.ChtimesReq)
    assert chtimes_request.path == "copy.txt"
    assert chtimes_request.a_time == 1_700_000_000
    assert chtimes_request.m_time == 1_700_000_001

    mounts = await interactive.mount()
    rpc_name, mount_request = interactive.calls.pop()
    assert rpc_name == "Mount"
    assert isinstance(mounts, models.sliverpb.Mount)
    assert isinstance(mount_request, models.sliverpb.MountReq)


async def test_execute_preserves_defaults_and_supports_background_options() -> None:
    interactive = _RecordingInteractive()

    await interactive.execute("echo", ["hello"])
    rpc_name, default_request = interactive.calls.pop()
    assert rpc_name == "Execute"
    assert isinstance(default_request, models.sliverpb.ExecuteReq)
    assert default_request.path == "echo"
    assert default_request.args == ["hello"]
    assert default_request.output is True
    assert default_request.background is False
    assert default_request.stdout == ""
    assert default_request.stderr == ""
    assert default_request.env == {}
    assert default_request.env_inheritance is False

    environment = {"SLIVER_TEST": "present"}
    executed = await interactive.execute(
        "worker",
        output=False,
        background=True,
        stdout="worker.stdout",
        stderr="worker.stderr",
        env=environment,
        env_inheritance=True,
    )
    environment["SLIVER_TEST"] = "changed"
    rpc_name, extended_request = interactive.calls.pop()
    assert rpc_name == "Execute"
    assert isinstance(executed, models.sliverpb.Execute)
    assert isinstance(extended_request, models.sliverpb.ExecuteReq)
    assert extended_request.args == []
    assert extended_request.output is False
    assert extended_request.background is True
    assert extended_request.stdout == "worker.stdout"
    assert extended_request.stderr == "worker.stderr"
    assert extended_request.env == {"SLIVER_TEST": "present"}
    assert extended_request.env_inheritance is True


async def test_execute_children_and_wasm_ls_use_command_rpc_names() -> None:
    interactive = _RecordingInteractive()

    children = await interactive.execute_children()
    rpc_name, children_request = interactive.calls.pop()
    assert rpc_name == "ExecuteChildren"
    assert isinstance(children, models.sliverpb.ExecuteChildren)
    assert isinstance(children_request, models.sliverpb.ExecuteChildrenReq)

    extensions = await interactive.wasm_ls()
    rpc_name, wasm_request = interactive.calls.pop()
    assert rpc_name == "ListWasmExtensions"
    assert isinstance(extensions, models.sliverpb.ListWasmExtensions)
    assert isinstance(wasm_request, models.sliverpb.ListWasmExtensionsReq)


async def test_runas_matches_sliver_options_and_preserves_run_as_defaults() -> None:
    interactive = _RecordingInteractive()

    await interactive.runas(
        "alice",
        "cmd.exe",
        "/c whoami",
        domain="EXAMPLE",
        password="secret",
        show_window=False,
        net_only=True,
    )
    _, request = interactive.calls.pop()
    assert isinstance(request, models.sliverpb.RunAsReq)
    assert request.domain == "EXAMPLE"
    assert request.password == "secret"
    assert request.hide_window is True
    assert request.net_only is True

    await interactive.run_as("alice", "cmd.exe", "/c whoami")
    _, compatibility_request = interactive.calls.pop()
    assert isinstance(compatibility_request, models.sliverpb.RunAsReq)
    assert compatibility_request.hide_window is False


async def test_spawndll_uses_cli_defaults_and_positive_keep_alive() -> None:
    interactive = _RecordingInteractive()

    await interactive.spawndll(
        b"dll",
        keep_alive=True,
        parent_pid=42,
        process_arguments=["--host-argument"],
    )
    _, request = interactive.calls.pop()
    assert isinstance(request, models.sliverpb.InvokeSpawnDllReq)
    assert request.process_name == r"c:\windows\system32\notepad.exe"
    assert request.entry_point == "ReflectiveLoader"
    assert request.kill is False
    assert request.p_pid == 42
    assert request.process_args == ["--host-argument"]

    await interactive.spawn_dll(b"dll", "host.exe", ["arg"], "Run", True)
    _, compatibility_request = interactive.calls.pop()
    assert isinstance(compatibility_request, models.sliverpb.InvokeSpawnDllReq)
    assert compatibility_request.kill is True


async def test_make_token_uses_typed_logon_defaults_and_override() -> None:
    interactive = _RecordingInteractive()

    await interactive.make_token("alice", "secret")
    _, default_request = interactive.calls.pop()
    assert isinstance(default_request, models.sliverpb.MakeTokenReq)
    assert default_request.domain == "."
    assert default_request.logon_type == int(LogonType.NEW_CREDENTIALS)

    await interactive.make_token(
        "alice",
        "secret",
        "EXAMPLE",
        logon_type=LogonType.INTERACTIVE,
    )
    _, explicit_request = interactive.calls.pop()
    assert isinstance(explicit_request, models.sliverpb.MakeTokenReq)
    assert explicit_request.domain == "EXAMPLE"
    assert explicit_request.logon_type == int(LogonType.INTERACTIVE)


async def test_string_enums_are_normalized_in_interactive_requests() -> None:
    interactive = _RecordingInteractive()

    await interactive.register_extension("demo", b"extension", GOOS.LINUX, "init")
    _, extension_request = interactive.calls.pop()
    assert isinstance(extension_request, models.sliverpb.RegisterExtensionReq)
    assert extension_request.os == "linux"

    await interactive.registry_read(
        RegistryHive.CURRENT_USER,
        "Software",
        "Value",
        "localhost",
    )
    _, read_request = interactive.calls.pop()
    assert isinstance(read_request, models.sliverpb.RegistryReadReq)
    assert read_request.hive == "HKCU"

    await interactive.registry_write(
        RegistryHive.LOCAL_MACHINE,
        "Software",
        "Value",
        "localhost",
        "data",
        b"",
        0,
        0,
        models.sliverpb.RegistryType.String,
    )
    _, write_request = interactive.calls.pop()
    assert isinstance(write_request, models.sliverpb.RegistryWriteReq)
    assert write_request.hive == "HKLM"

    await interactive.registry_create(
        "Software/Sliver",
        hive=RegistryHive.CLASSES_ROOT,
        hostname="localhost",
    )
    _, create_request = interactive.calls.pop()
    assert isinstance(create_request, models.sliverpb.RegistryCreateKeyReq)
    assert create_request.hive == "HKCR"
    assert create_request.path == "Software"
    assert create_request.key == "Sliver"

    with pytest.raises(ValueError, match="parent path"):
        await interactive.registry_create("Sliver")


async def test_session_only_command_names_delegate_to_retained_implementations() -> (
    None
):
    session = InteractiveSession.__new__(InteractiveSession)
    get_system = AsyncMock(return_value=models.sliverpb.GetSystem())
    list_extensions = AsyncMock(return_value=models.sliverpb.ListExtensions())
    session.get_system = get_system
    session.list_extensions = list_extensions
    config = models.clientpb.ImplantConfig()

    await session.getsystem("spoolsv.exe", config)
    await session.extensions_list()

    get_system.assert_awaited_once_with("spoolsv.exe", config)
    list_extensions.assert_awaited_once_with()


class _PivotStub:
    def __init__(self) -> None:
        self.requests: list[models.sliverpb.PivotListenersReq] = []

    async def PivotSessionListeners(
        self,
        request: models.sliverpb.PivotListenersReq,
        timeout: float | None = None,
    ) -> models.sliverpb.PivotListeners:
        assert timeout == 17
        self.requests.append(request)
        return models.sliverpb.PivotListeners(
            listeners=[models.sliverpb.PivotListener(id=7)]
        )


async def test_pivots_is_primary_and_pivot_listeners_remains_compatible() -> None:
    stub = _PivotStub()
    session = InteractiveSession.__new__(InteractiveSession)
    session._session = models.clientpb.Session(id="session-id")
    session._stub = cast(PydanticSliverRPCStub, stub)
    session.timeout = 17

    assert [pivot.id for pivot in await session.pivots()] == [7]
    assert [pivot.id for pivot in await session.pivot_listeners()] == [7]
    assert len(stub.requests) == 2
    assert all(
        request.request is not None and request.request.session_id == "session-id"
        for request in stub.requests
    )
    assert all(
        request.request is not None and request.request.timeout == 16_999_999_999
        for request in stub.requests
    )


def test_beacon_routing_uses_go_duration_and_async_tasking() -> None:
    beacon = InteractiveBeacon.__new__(InteractiveBeacon)
    beacon._beacon = models.clientpb.Beacon(id="beacon-id")
    beacon.timeout = 17

    request = beacon._request(models.sliverpb.Ping())

    assert request.request == models.commonpb.Request(
        beacon_id="beacon-id",
        timeout=16_999_999_999,
        async_=True,
    )


async def test_services_command_paths_use_current_sliver_requests() -> None:
    stub = AsyncMock()
    stub.StartServiceByName.return_value = models.sliverpb.ServiceInfo()
    stub.StopService.return_value = models.sliverpb.ServiceInfo()
    session = InteractiveSession.__new__(InteractiveSession)
    session._session = models.clientpb.Session(id="session-id")
    session._stub = stub
    session.timeout = 17

    await session.services_start("Spooler")
    start_request = stub.StartServiceByName.await_args.args[0]
    assert isinstance(start_request, models.sliverpb.StartServiceByNameReq)
    assert start_request.service_info == models.sliverpb.ServiceInfoReq(
        service_name="Spooler",
        hostname="localhost",
    )
    assert start_request.request == models.commonpb.Request(
        session_id="session-id",
        timeout=16_999_999_999,
    )

    await session.services_stop("Spooler", hostname="server.example")
    stop_request = stub.StopService.await_args.args[0]
    assert isinstance(stop_request, models.sliverpb.StopServiceReq)
    assert stop_request.service_info == models.sliverpb.ServiceInfoReq(
        service_name="Spooler",
        hostname="server.example",
    )
