from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import cast
from unittest.mock import AsyncMock

import grpc
import pytest

import sliver.client as client_module
from sliver import (
    GOARCH,
    GOOS,
    C2Endpoint,
    CleanupError,
    Client,
    EventType,
    GeneratedImplant,
    ImplantSpec,
    Inventory,
    OperatorConfig,
    ResourceNotFoundError,
    SliverClient,
    SliverClientConfig,
    SliverTimeoutError,
    Target,
    models,
)
from sliver._rpc import PydanticSliverRPCStub
from sliver.beacon import BaseBeacon
from sliver.errors import CommandError


def _config() -> OperatorConfig:
    return OperatorConfig(
        operator="facade-test",
        lhost="127.0.0.1",
        lport=31337,
        ca_certificate="ca",
        certificate="certificate",
        private_key="private-key",
        token="token",
    )


def _generated(name: str = "quiet-river") -> models.clientpb.Generate:
    return models.clientpb.Generate(
        file=models.commonpb.File(name=f"{name}.bin", data=b"implant"),
        implant_name=name,
        implant_build_id="build-id",
    )


def test_preferred_client_and_operator_config_are_compatible_facade_types() -> None:
    config = _config()
    client = Client(config)

    assert isinstance(config, SliverClientConfig)
    assert isinstance(client, SliverClient)
    assert client.config is config


async def test_client_context_preserves_concrete_type_and_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    connect = AsyncMock(return_value=models.clientpb.Version(major=1))
    close = AsyncMock()
    monkeypatch.setattr(client, "connect", connect)
    monkeypatch.setattr(client, "close", close)

    async with client as entered:
        assert entered is client
        assert isinstance(entered, Client)

    connect.assert_awaited_once_with()
    close.assert_awaited_once_with()


async def test_connect_and_close_are_serialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    channel = AsyncMock(spec=grpc.aio.Channel)
    stub = AsyncMock(spec=PydanticSliverRPCStub)
    version_started = asyncio.Event()
    release_version = asyncio.Event()

    def secure_channel(**kwargs: object) -> grpc.aio.Channel:
        return cast(grpc.aio.Channel, channel)

    async def version(timeout: int = client_module.TIMEOUT) -> models.clientpb.Version:
        assert timeout == 17
        version_started.set()
        await release_version.wait()
        return models.clientpb.Version(major=1)

    monkeypatch.setattr(client_module.grpc.aio, "secure_channel", secure_channel)
    monkeypatch.setattr(client_module, "PydanticSliverRPCStub", lambda channel: stub)
    monkeypatch.setattr(client, "version", version)

    connect_task = asyncio.create_task(client.connect(timeout=17))
    await asyncio.wait_for(version_started.wait(), timeout=1)
    close_task = asyncio.create_task(client.close())
    await asyncio.sleep(0)
    close_waited_for_connect = not close_task.done() and client.is_connected()

    release_version.set()
    assert (await connect_task).major == 1
    await close_task

    assert close_waited_for_connect
    channel.close.assert_awaited_once_with()
    assert not client.is_connected()


async def test_failed_existing_connection_probe_clears_stale_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    channel = AsyncMock(spec=grpc.aio.Channel)
    broker = AsyncMock()
    client._channel = channel
    client._stub = AsyncMock()
    client._event_broker = broker
    monkeypatch.setattr(
        client,
        "version",
        AsyncMock(side_effect=RuntimeError("connection is unavailable")),
    )

    with pytest.raises(RuntimeError, match="connection is unavailable"):
        await client.connect(timeout=17)

    broker.close.assert_awaited_once_with()
    channel.close.assert_awaited_once_with()
    assert not client.is_connected()


async def test_inventory_returns_one_pydantic_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    version = models.clientpb.Version(major=1, minor=2, patch=3)
    session = models.clientpb.Session(id="session-id")
    beacon = models.clientpb.Beacon(id="beacon-id")
    job = models.clientpb.Job(id=7)
    operator = models.clientpb.Operator(name="alice")
    methods = {
        "version": AsyncMock(return_value=version),
        "sessions": AsyncMock(return_value=[session]),
        "beacons": AsyncMock(return_value=[beacon]),
        "jobs": AsyncMock(return_value=[job]),
        "operators": AsyncMock(return_value=[operator]),
    }
    for name, method in methods.items():
        monkeypatch.setattr(client, name, method)

    result = await client.inventory(timeout=17)

    assert result == Inventory(
        version=version,
        sessions=[session],
        beacons=[beacon],
        jobs=[job],
        operators=[operator],
    )
    for method in methods.values():
        method.assert_awaited_once_with(timeout=17)


@pytest.mark.parametrize(
    ("method_name", "resource", "identifier"),
    [
        ("get_session", "session", "missing-session"),
        ("get_beacon", "beacon", "missing-beacon"),
        ("get_job", "job", 7331),
    ],
)
async def test_get_helpers_raise_typed_not_found_errors(
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
    resource: str,
    identifier: str | int,
) -> None:
    client = Client(_config())
    monkeypatch.setattr(client, f"find_{resource}", AsyncMock(return_value=None))

    with pytest.raises(ResourceNotFoundError) as raised:
        await getattr(client, method_name)(identifier, timeout=17)

    assert raised.value.resource == resource
    assert raised.value.identifier == identifier


async def test_use_dispatches_detached_pydantic_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    use_session = AsyncMock(return_value=object())
    use_beacon = AsyncMock(return_value=object())
    monkeypatch.setattr(client, "use_session", use_session)
    monkeypatch.setattr(client, "use_beacon", use_beacon)

    await client.use(models.clientpb.Session(id="session-id"), timeout=17)
    await client.use(models.clientpb.Beacon(id="beacon-id"), timeout=19)

    use_session.assert_awaited_once_with("session-id", timeout=17)
    use_beacon.assert_awaited_once_with("beacon-id", timeout=19)
    with pytest.raises(TypeError, match="Pydantic Session or Beacon"):
        await client.use("beacon-id", timeout=17)  # type: ignore[arg-type]


async def test_generate_returns_a_rich_result_and_sends_a_pydantic_request() -> None:
    client = Client(_config())
    stub = AsyncMock()
    stub.generate.return_value = _generated()
    client._stub = stub
    spec = ImplantSpec(
        target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
        c2=[C2Endpoint.mtls("c2.example")],
    )

    result = await client.generate(spec, name="quiet-river", timeout=17)

    assert result == GeneratedImplant.from_generate(_generated())
    request = stub.generate.await_args.args[0]
    assert isinstance(request, models.clientpb.GenerateReq)
    assert request.name == "quiet-river"
    assert request.config is not None
    assert request.config.goos == "linux"
    stub.generate.assert_awaited_once_with(request, timeout=17)


async def test_regenerate_returns_the_same_rich_result_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    regenerate_implant = AsyncMock(return_value=_generated("stored-build"))
    monkeypatch.setattr(client, "regenerate_implant", regenerate_implant)

    result = await client.regenerate("stored-build", timeout=17)

    assert isinstance(result, GeneratedImplant)
    assert result.implant_name == "stored-build"
    regenerate_implant.assert_awaited_once_with("stored-build", timeout=17)


async def test_profile_generation_methods_return_rich_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    profile = models.clientpb.ImplantProfile(
        name="linux-session",
        config=models.clientpb.ImplantConfig(goos="linux", goarch="amd64"),
    )
    monkeypatch.setattr(client, "profiles", AsyncMock(return_value=[profile]))
    stub = AsyncMock()
    stub.generate.return_value = _generated("from-profile")
    client._stub = stub

    result = await client.profiles_generate(
        "linux-session",
        name="from-profile",
        timeout=17,
    )

    assert isinstance(result, GeneratedImplant)
    request = stub.generate.await_args.args[0]
    assert request.config is not profile.config
    assert request.config == profile.config
    assert request.name == "from-profile"
    stub.generate.assert_awaited_once_with(request, timeout=17)


async def test_profile_generation_reports_missing_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    monkeypatch.setattr(client, "profiles", AsyncMock(return_value=[]))

    with pytest.raises(ResourceNotFoundError) as raised:
        await client.profiles_generate("missing", timeout=17)

    assert raised.value.resource == "implant profile"
    assert raised.value.identifier == "missing"


async def test_profile_stage_returns_a_rich_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    generate_stage = AsyncMock(return_value=_generated("stage"))
    monkeypatch.setattr(client, "generate_stage", generate_stage)
    request = models.clientpb.GenerateStageReq(profile="linux-session")

    result = await client.profiles_stage(request, timeout=17)

    assert isinstance(result, GeneratedImplant)
    generate_stage.assert_awaited_once_with(request, timeout=17)


async def test_wireguard_listener_forwards_timeout_to_ip_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    generate_wg_ip = AsyncMock(return_value=models.clientpb.UniqueWGIP(ip="100.64.0.9"))
    monkeypatch.setattr(client, "generate_wg_ip", generate_wg_ip)
    stub = AsyncMock()
    stub.StartWGListener.return_value = models.clientpb.ListenerJob(job_id=7)
    client._stub = stub

    listener = await client.wg(timeout=17)

    assert listener.job_id == 7
    generate_wg_ip.assert_awaited_once_with(timeout=17)
    request = stub.StartWGListener.await_args.args[0]
    assert request.tun_ip == "100.64.0.9"
    stub.StartWGListener.assert_awaited_once_with(request, timeout=17)


@pytest.mark.parametrize("domains", [[], [""]])
async def test_dns_listener_rejects_empty_domains(domains: list[str]) -> None:
    client = Client(_config())

    with pytest.raises(ValueError, match="DNS name"):
        await client.dns(domains)


@pytest.mark.parametrize("method_name", ["http", "https"])
async def test_http_listener_defaults_match_sliver_security_and_duration_defaults(
    method_name: str,
) -> None:
    client = Client(_config())
    stub = AsyncMock()
    stub.StartHTTPListener.return_value = models.clientpb.ListenerJob(job_id=7)
    stub.StartHTTPSListener.return_value = models.clientpb.ListenerJob(job_id=8)
    client._stub = stub

    await getattr(client, method_name)(timeout=17)

    rpc = stub.StartHTTPListener if method_name == "http" else stub.StartHTTPSListener
    request = rpc.await_args.args[0]
    assert request.enforce_otp is True
    assert request.long_poll_timeout == 1_000_000_000
    assert request.long_poll_jitter == 2_000_000_000
    rpc.assert_awaited_once_with(request, timeout=17)


async def test_temporary_listener_is_stopped_after_context_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    listener = models.clientpb.ListenerJob(job_id=7)
    mtls = AsyncMock(return_value=listener)
    kill_job = AsyncMock(return_value=models.clientpb.KillJob(id=7, success=True))
    monkeypatch.setattr(client, "mtls", mtls)
    monkeypatch.setattr(client, "kill_job", kill_job)

    async with client.temporary_mtls(host="127.0.0.1", port=4444, timeout=17) as job:
        assert job is listener

    mtls.assert_awaited_once_with(host="127.0.0.1", port=4444, timeout=17)
    kill_job.assert_awaited_once_with(7, timeout=17)


async def test_temporary_listener_reports_cleanup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    monkeypatch.setattr(
        client,
        "mtls",
        AsyncMock(return_value=models.clientpb.ListenerJob(job_id=7)),
    )
    monkeypatch.setattr(
        client,
        "kill_job",
        AsyncMock(return_value=models.clientpb.KillJob(id=7, success=False)),
    )

    with pytest.raises(CleanupError) as raised:
        async with client.temporary_mtls():
            pass

    assert raised.value.operation == "temporary mTLS listener"
    assert len(raised.value.failures) == 1


async def test_collect_events_is_bounded_and_closes_its_subscription(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())
    closed = False

    async def events(
        event_types: object = None,
    ) -> AsyncGenerator[models.clientpb.Event, None]:
        nonlocal closed
        assert event_types == (EventType.JOB_STARTED,)
        try:
            for index in range(3):
                yield models.clientpb.Event(
                    event_type=EventType.JOB_STARTED.value,
                    data=str(index).encode(),
                )
        finally:
            closed = True

    monkeypatch.setattr(client, "events", events)

    result = await client.collect_events(EventType.JOB_STARTED, limit=2)

    assert [event.data for event in result] == [b"0", b"1"]
    assert closed


async def test_collect_events_translates_asyncio_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(_config())

    async def events(
        event_types: object = None,
    ) -> AsyncGenerator[models.clientpb.Event, None]:
        await asyncio.Event().wait()
        yield models.clientpb.Event()  # pragma: no cover

    monkeypatch.setattr(client, "events", events)

    with pytest.raises(SliverTimeoutError) as raised:
        await client.collect_events(limit=1, timeout=0.01)

    assert raised.value.operation == "collect events"
    assert raised.value.timeout == 0.01


@pytest.mark.parametrize(
    ("alias", "implementation", "args"),
    [
        ("beacons_rm", "rm_beacon", ("beacon-id",)),
        ("tasks_fetch", "fetch_task", ("task-id",)),
        ("tasks_cancel", "cancel_task", ("task-id",)),
        ("stage_listener", "start_tcp_stager_listener", ("127.0.0.1", 4444, b"stage")),
        ("implants_rm", "rm_implant", ("implant",)),
        ("profiles_rm", "rm_profile", ("profile",)),
        (
            "profiles_new",
            "new_profile",
            (models.clientpb.ImplantProfile(name="profile"),),
        ),
        ("show_website", "website", ("demo",)),
        ("websites_show", "show_website", ("demo",)),
        ("rm_website", "remove_website", ("demo",)),
        ("websites_rm", "rm_website", ("demo",)),
        ("rm_website_content", "remove_website_content", ("demo", ["/index"])),
        (
            "websites_rm_content",
            "rm_website_content",
            ("demo", ["/index"]),
        ),
    ],
)
async def test_command_path_aliases_delegate_once(
    monkeypatch: pytest.MonkeyPatch,
    alias: str,
    implementation: str,
    args: tuple[object, ...],
) -> None:
    client = Client(_config())
    delegated = AsyncMock(return_value=models.clientpb.Website(name="demo"))
    monkeypatch.setattr(client, implementation, delegated)

    await getattr(client, alias)(*args, timeout=17)

    delegated.assert_awaited_once_with(*args, timeout=17)


async def test_beacon_queue_error_raises_before_waiting_for_a_task_result() -> None:
    broker = AsyncMock()
    stub = AsyncMock()
    stub.Ping.return_value = models.sliverpb.Ping(
        response=models.commonpb.Response(err="queue rejected command")
    )
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon._closed = False
    beacon._event_broker = broker
    beacon._stub = stub
    beacon._beacon = models.clientpb.Beacon(id="beacon-id")
    beacon.timeout = 17

    with pytest.raises(CommandError) as raised:
        await beacon._execute("Ping", models.sliverpb.Ping(), models.sliverpb.Ping)

    assert raised.value.operation == "Ping"
    assert raised.value.target_id == "beacon-id"
    assert raised.value.message == "queue rejected command"
    broker.wait_for_result.assert_not_awaited()
