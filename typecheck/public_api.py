"""Static consumer contract for the public Pydantic API.

This module is checked by mypy in CI; it is not executed as a test.
"""

from __future__ import annotations

from datetime import timedelta

from typing_extensions import assert_type

from sliver import (
    GOARCH,
    GOOS,
    BeaconOptions,
    C2Endpoint,
    Client,
    EventType,
    GeneratedImplant,
    ImplantSpec,
    InteractiveBeacon,
    InteractiveSession,
    Inventory,
    OperatorConfig,
    SliverClient,
    SliverClientConfig,
    SliverWireGuardConfig,
    Target,
    get_pydantic_model,
)
from sliver._rpc import PydanticSliverRPCStub
from sliver.models.clientpb import (
    Beacon,
    BeaconTask,
    Event,
    Generate,
    GenerateStageReq,
    ImplantConfig,
    ImplantProfile,
    OutputFormat,
    Session,
    Version,
)
from sliver.models.commonpb import File
from sliver.models.sliverpb import (
    Execute,
    GetSystem,
    Ls,
    Ping,
    Pwd,
    ServiceInfo,
    SockTabEntry,
    SpawnDll,
)


def model_contract() -> None:
    session = Session(id="session-id", name="shell")
    event = Event(event_type="session-connected", session=session)
    generated = Generate(file=File(name="implant", data=b"payload"))
    config = ImplantConfig(format=OutputFormat.EXECUTABLE)
    goos: GOOS = GOOS.FREEBSD
    goarch: GOARCH = GOARCH.RISCV64

    assert_type(session, Session)
    assert_type(session.id, str)
    assert_type(event, Event)
    assert_type(event.event_type, str)
    assert_type(event.session, Session | None)
    assert_type(generated.file, File | None)
    assert_type(OutputFormat.EXECUTABLE, OutputFormat)
    assert_type(goos, GOOS)
    assert_type(goarch, GOARCH)
    assert_type(config.format, OutputFormat)
    assert_type(get_pydantic_model(Event), type[Event])

    address = SockTabEntry.SockAddr(ip="127.0.0.1", port=4444)
    assert_type(address, SockTabEntry.SockAddr)


def config_contract() -> None:
    wireguard = SliverWireGuardConfig(
        server_pub_key="server-public",
        client_private_key="client-private",
        client_pub_key="client-public",
        client_ip="127.0.0.2",
        server_ip="127.0.0.1",
    )
    config = SliverClientConfig(
        operator="operator",
        lhost="127.0.0.1",
        lport=31337,
        ca_certificate="ca",
        certificate="certificate",
        private_key="private-key",
        token="token",
        wg=wireguard,
    )

    assert_type(wireguard, SliverWireGuardConfig)
    assert_type(config, SliverClientConfig)
    assert_type(config.lhost, str)
    assert_type(config.lport, int)
    assert_type(config.wg, SliverWireGuardConfig | None)
    assert_type(OperatorConfig.from_file(), OperatorConfig)


async def client_contract(client: SliverClient, config: ImplantConfig) -> None:
    assert_type(await client.connect(), Version)
    assert_type(await client.sessions(), list[Session])
    assert_type(await client.beacons(), list[Beacon])
    assert_type(await client.generate_implant(config), Generate)

    async for event in client.events():
        assert_type(event, Event)


async def facade_contract(client: Client) -> None:
    spec = ImplantSpec(
        target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
        c2=[C2Endpoint.mtls("c2.example")],
        beacon=BeaconOptions(
            interval=timedelta(seconds=60),
            jitter=timedelta(seconds=30),
        ),
    )

    assert_type(Client.from_config_file(), Client)
    assert_type(client.rpc, PydanticSliverRPCStub)
    assert_type(await client.inventory(), Inventory)
    assert_type(await client.generate(spec), GeneratedImplant)
    assert_type(await client.tasks_fetch("task-id"), BeaconTask)
    assert_type(
        await client.profiles_new(ImplantProfile(name="profile")),
        ImplantProfile,
    )
    assert_type(await client.profiles_generate("profile"), GeneratedImplant)
    assert_type(
        await client.profiles_stage(GenerateStageReq(profile="profile")),
        GeneratedImplant,
    )
    assert_type(await client.use_session("session-id"), InteractiveSession)
    assert_type(await client.use_beacon("beacon-id"), InteractiveBeacon)
    assert_type(
        await client.collect_events(EventType.JOB_STARTED, limit=1),
        list[Event],
    )

    async with client as connected:
        assert_type(connected, Client)
    async with client.temporary_mtls() as listener:
        assert_type(listener.job_id, int)


async def interaction_contract(
    session: InteractiveSession, beacon: InteractiveBeacon
) -> None:
    assert_type(session.session, Session)
    assert_type(beacon.beacon, Beacon)
    assert_type(await session.ping(), Ping)
    assert_type(await session.pwd(), Pwd)
    assert_type(await session.ls(), Ls)
    assert_type(await session.execute("whoami"), Execute)
    assert_type(await session.getsystem("spoolsv.exe", ImplantConfig()), GetSystem)
    assert_type(await session.services_start("Spooler"), ServiceInfo)
    assert_type(await session.spawndll(b"dll", keep_alive=True), SpawnDll)
