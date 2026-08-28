from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from sliver import SliverClient, SliverClientConfig
from sliver.beacon import BaseBeacon


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
    channel = AsyncMock()
    client._channel = channel
    client._stub = AsyncMock()

    await client.close()
    await client.close()

    channel.close.assert_awaited_once_with()
    assert not client.is_connected()
    with pytest.raises(RuntimeError, match="client is not connected"):
        _ = client.raw_stub


async def test_beacon_close_cancels_the_watcher_and_pending_commands() -> None:
    blocker = asyncio.Event()
    watcher = asyncio.create_task(blocker.wait())
    pending = asyncio.get_running_loop().create_future()
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon.beacon_tasks = {"task-id": (pending, None)}
    beacon._taskresult_watcher = watcher
    beacon._closed = False

    await beacon.close()
    await beacon.close()

    assert watcher.cancelled()
    assert pending.cancelled()
    assert beacon.beacon_tasks == {}


async def test_beacon_commands_wait_for_the_result_stream() -> None:
    blocker = asyncio.Event()
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon.beacon_tasks = {}
    beacon._closed = False
    beacon._taskresult_error = None
    beacon._taskresult_ready = asyncio.Event()
    beacon._taskresult_watcher = asyncio.create_task(blocker.wait())

    waiting = asyncio.create_task(beacon._wait_for_taskresult_watcher())
    await asyncio.sleep(0)
    assert not waiting.done()

    beacon._taskresult_ready.set()
    await waiting
    await beacon.close()
