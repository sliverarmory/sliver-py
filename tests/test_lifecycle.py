from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sliver import NotConnectedError, SliverClient, SliverClientConfig, models
from sliver._pb.clientpb import client_pb2
from sliver.beacon import BaseBeacon
from sliver.session import BaseSession


def _config() -> SliverClientConfig:
    return SliverClientConfig(
        operator="lifecycle-test",
        lhost="127.0.0.1",
        lport=31337,
        ca_certificate="ca",
        certificate="certificate",
        private_key="private-key",
        token="token",
    )


async def test_client_close_releases_the_channel_and_is_idempotent() -> None:
    client = SliverClient(_config())
    close_order: list[str] = []
    channel = AsyncMock()
    channel.close.side_effect = lambda: close_order.append("channel")
    broker = AsyncMock()
    broker.close.side_effect = lambda: close_order.append("broker")
    client._channel = channel
    client._stub = AsyncMock()
    client._event_broker = broker

    await client.close()
    await client.close()

    broker.close.assert_awaited_once_with()
    channel.close.assert_awaited_once_with()
    assert close_order == ["broker", "channel"]
    assert not client.is_connected()
    with pytest.raises(NotConnectedError, match="client is not connected"):
        _ = client.pydantic_stub
    assert not hasattr(client, "raw_stub")


def test_public_stub_only_exposes_the_converted_rpc_interface() -> None:
    client = SliverClient(_config())
    converted_stub = AsyncMock()
    client._stub = converted_stub

    assert client.pydantic_stub is converted_stub
    assert not hasattr(client, "raw_stub")


async def test_kill_beacon_routes_kill_to_the_beacon() -> None:
    client = SliverClient(_config())
    converted_stub = AsyncMock()
    client._stub = converted_stub

    await client.kill_beacon("beacon-id", force=True, timeout=17)

    request = converted_stub.Kill.await_args.args[0]
    assert isinstance(request, models.sliverpb.KillReq)
    assert request.force
    assert request.request == models.commonpb.Request(
        beacon_id="beacon-id", timeout=17
    )
    converted_stub.Kill.assert_awaited_once_with(request, timeout=17)
    converted_stub.RmBeacon.assert_not_awaited()


async def test_rm_beacon_removes_only_the_server_record() -> None:
    client = SliverClient(_config())
    converted_stub = AsyncMock()
    client._stub = converted_stub

    await client.rm_beacon("beacon-id", timeout=17)

    request = converted_stub.RmBeacon.await_args.args[0]
    assert request == models.clientpb.Beacon(id="beacon-id")
    converted_stub.RmBeacon.assert_awaited_once_with(request, timeout=17)
    converted_stub.Kill.assert_not_awaited()


def test_public_constructors_reject_raw_protobuf_inputs() -> None:
    with pytest.raises(TypeError, match="SliverClientConfig Pydantic model"):
        SliverClient({"operator": "raw"})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Session Pydantic model"):
        BaseSession(client_pb2.Session(), object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Beacon Pydantic model"):
        BaseBeacon(client_pb2.Beacon(), object())  # type: ignore[arg-type]


async def test_direct_beacon_close_delegates_to_its_owned_broker() -> None:
    broker = AsyncMock()
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon._event_broker = broker
    beacon._owns_event_broker = True
    beacon._closed = False

    await beacon.close()
    await beacon.close()

    broker.close.assert_awaited_once_with()


async def test_client_owned_beacon_close_leaves_the_shared_broker_running() -> None:
    broker = AsyncMock()
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon._event_broker = broker
    beacon._owns_event_broker = False
    beacon._closed = False

    await beacon.close()

    broker.close.assert_not_awaited()
