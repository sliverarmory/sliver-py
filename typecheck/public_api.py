"""Static consumer contract for the public Pydantic API.

This module is checked by mypy in CI; it is not executed as a test.
"""

from __future__ import annotations

from typing_extensions import assert_type

from sliver import (
    InteractiveBeacon,
    InteractiveSession,
    SliverClient,
    SliverClientConfig,
    SliverWireGuardConfig,
    get_pydantic_model,
)
from sliver.models.clientpb import (
    Beacon,
    Event,
    Generate,
    ImplantConfig,
    OutputFormat,
    Session,
    Version,
)
from sliver.models.commonpb import File
from sliver.models.sliverpb import Execute, Ls, Ping, Pwd, SockTabEntry


def model_contract() -> None:
    session = Session(id="session-id", name="shell")
    event = Event(event_type="session-connected", session=session)
    generated = Generate(file=File(name="implant", data=b"payload"))
    config = ImplantConfig(format=OutputFormat.EXECUTABLE)

    assert_type(session, Session)
    assert_type(session.id, str)
    assert_type(event, Event)
    assert_type(event.event_type, str)
    assert_type(event.session, Session | None)
    assert_type(generated.file, File | None)
    assert_type(OutputFormat.EXECUTABLE, OutputFormat)
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


async def client_contract(client: SliverClient, config: ImplantConfig) -> None:
    assert_type(await client.connect(), Version)
    assert_type(await client.sessions(), list[Session])
    assert_type(await client.beacons(), list[Beacon])
    assert_type(await client.generate_implant(config), Generate)

    async for event in client.events():
        assert_type(event, Event)


async def interaction_contract(
    session: InteractiveSession, beacon: InteractiveBeacon
) -> None:
    assert_type(session.session, Session)
    assert_type(beacon.beacon, Beacon)
    assert_type(await session.ping(), Ping)
    assert_type(await session.pwd(), Pwd)
    assert_type(await session.ls(), Ls)
    assert_type(await session.execute("whoami"), Execute)
