from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import cast
from unittest.mock import AsyncMock

import grpc
import pytest

import sliver.beacon as beacon_module
from sliver import BeaconTaskState, SliverClient, SliverClientConfig, models
from sliver._rpc import PydanticSliverRPCStub
from sliver.beacon import BaseBeacon, _ClientEventBroker
from sliver.errors import CommandError, SliverTimeoutError
from sliver.models import ProtobufModel, _model_to_protobuf


def _config() -> SliverClientConfig:
    return SliverClientConfig(
        operator="broker-test",
        lhost="127.0.0.1",
        lport=31337,
        ca_certificate="ca",
        certificate="certificate",
        private_key="private-key",
        token="token",
    )


def _serialize(model: ProtobufModel) -> bytes:
    return _model_to_protobuf(model).SerializeToString()


class _EventStream(AsyncIterator[models.clientpb.Event]):
    def __init__(self) -> None:
        self._events: asyncio.Queue[models.clientpb.Event | None] = asyncio.Queue()

    def __aiter__(self) -> _EventStream:
        return self

    async def __anext__(self) -> models.clientpb.Event:
        event = await self._events.get()
        if event is None:
            raise StopAsyncIteration
        return event

    async def emit(self, task_id: str) -> None:
        await self._events.put(
            models.clientpb.Event(
                event_type="beacon-taskresult",
                data=_serialize(models.clientpb.BeaconTask(id=task_id)),
            )
        )

    async def emit_event(self, event_type: str) -> None:
        await self._events.put(models.clientpb.Event(event_type=event_type))

    async def finish(self) -> None:
        await self._events.put(None)


class _FakeBeaconStub:
    def __init__(self) -> None:
        self.stream = _EventStream()
        self.events_calls = 0
        self.contents: dict[str, models.clientpb.BeaconTask] = {}
        self.content_errors: dict[str, Exception] = {}
        self.content_calls: list[tuple[str, float | None]] = []
        self.cancelled: list[tuple[str, float | None]] = []

    def Events(self, request: models.commonpb.Empty) -> _EventStream:
        assert isinstance(request, models.commonpb.Empty)
        self.events_calls += 1
        return self.stream

    async def GetBeaconTaskContent(
        self,
        request: models.clientpb.BeaconTask,
        timeout: float | None = None,
    ) -> models.clientpb.BeaconTask:
        self.content_calls.append((request.id, timeout))
        error = self.content_errors.get(request.id)
        if error is not None:
            raise error
        return self.contents[request.id]

    async def CancelBeaconTask(
        self,
        request: models.clientpb.BeaconTask,
        timeout: float | None = None,
    ) -> models.clientpb.BeaconTask:
        self.cancelled.append((request.id, timeout))
        return request


class _ReconnectStub(_FakeBeaconStub):
    def __init__(self) -> None:
        super().__init__()
        self.reconnected_stream = _EventStream()

    def Events(self, request: models.commonpb.Empty) -> _EventStream:
        assert isinstance(request, models.commonpb.Empty)
        self.events_calls += 1
        if self.events_calls == 1:
            return self.stream
        return self.reconnected_stream


def _broker(fake: _FakeBeaconStub) -> _ClientEventBroker:
    return _ClientEventBroker(cast(PydanticSliverRPCStub, fake))


async def _wait_until(predicate: Callable[[], bool]) -> None:
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


async def test_broker_is_lazy_and_starts_only_one_event_stream() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)

    assert fake.events_calls == 0
    await asyncio.gather(broker.start(), broker.start(), broker.start())

    assert fake.events_calls == 1
    await broker.close()


async def test_broker_recovers_an_event_that_arrives_before_registration() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    task_id = "early-result"
    expected = models.sliverpb.Ping(nonce=7331)
    fake.contents[task_id] = models.clientpb.BeaconTask(
        id=task_id, response=_serialize(expected)
    )
    await broker.start()

    await fake.stream.emit(task_id)
    await _wait_until(lambda: task_id in broker._orphaned_results)

    result = await broker.wait_for_result(task_id, models.sliverpb.Ping, timeout=1)

    assert result == expected
    assert broker._pending == {}
    assert task_id not in broker._orphaned_results
    await broker.close()


async def test_beacon_execute_polls_completed_task_when_result_event_is_lost() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    broker._TASK_POLL_INTERVAL = 0
    task_id = "lost-result-event"
    expected = models.sliverpb.Ping(nonce=7331)
    fake.contents[task_id] = models.clientpb.BeaconTask(
        id=task_id,
        state=BeaconTaskState.COMPLETED.value,
        response=_serialize(expected),
    )
    fake.Ping = AsyncMock(
        return_value=models.sliverpb.Ping(
            response=models.commonpb.Response(task_id=task_id)
        )
    )
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon._closed = False
    beacon._event_broker = broker
    beacon._stub = fake
    beacon._beacon = models.clientpb.Beacon(id="beacon-id")
    beacon.timeout = 1

    try:
        result = await beacon._execute(
            "Ping", models.sliverpb.Ping(), models.sliverpb.Ping
        )
    finally:
        await broker.close()

    assert result == expected
    fake.Ping.assert_awaited_once_with(models.sliverpb.Ping(), timeout=1)
    assert len(fake.content_calls) == 1
    polled_task_id, poll_timeout = fake.content_calls[0]
    assert polled_task_id == task_id
    assert poll_timeout is not None
    assert 0 < poll_timeout <= beacon.timeout


async def test_broker_polling_waits_for_a_completed_task_state() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    broker._TASK_POLL_INTERVAL = 0
    task_id = "eventually-completed"
    expected = models.sliverpb.Ping(nonce=31337)
    fake.contents[task_id] = models.clientpb.BeaconTask(
        id=task_id,
        state=BeaconTaskState.SENT.value,
    )
    waiter = asyncio.create_task(
        broker.wait_for_result(task_id, models.sliverpb.Ping, timeout=1)
    )

    await _wait_until(lambda: bool(fake.content_calls))
    assert not waiter.done()
    fake.contents[task_id] = models.clientpb.BeaconTask(
        id=task_id,
        state=BeaconTaskState.COMPLETED.value,
        response=_serialize(expected),
    )

    assert await waiter == expected
    assert len(fake.content_calls) >= 2
    assert broker._pending == {}
    assert broker._pollers == {}
    await broker.close()


async def test_broker_polling_fails_a_terminal_non_completed_task() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    broker._TASK_POLL_INTERVAL = 0
    task_id = "canceled-task"
    fake.contents[task_id] = models.clientpb.BeaconTask(
        id=task_id,
        state=BeaconTaskState.CANCELED.value,
    )

    with pytest.raises(RuntimeError, match="ended in state 'canceled'"):
        await broker.wait_for_result(task_id, models.sliverpb.Ping, timeout=1)

    assert broker._pending == {}
    assert broker._pollers == {}
    await broker.close()


async def test_broker_bounds_unclaimed_result_events() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    await broker.start()

    for index in range(broker._MAX_ORPHANED_RESULTS + 1):
        await fake.stream.emit(f"task-{index}")
    last_task = f"task-{broker._MAX_ORPHANED_RESULTS}"
    await _wait_until(lambda: last_task in broker._orphaned_results)

    assert len(broker._orphaned_results) == broker._MAX_ORPHANED_RESULTS
    assert "task-0" not in broker._orphaned_results
    await broker.close()


async def test_public_event_subscribers_share_the_broker_and_clean_up() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    client = SliverClient(_config())
    client._stub = cast(PydanticSliverRPCStub, fake)
    client._event_broker = broker

    all_events = client.events()
    job_events = client.on("job-started")
    next_all = asyncio.create_task(anext(all_events))
    next_job = asyncio.create_task(anext(job_events))
    await _wait_until(lambda: len(broker._subscribers) == 2)

    await fake.stream.emit_event("session-connected")
    await fake.stream.emit_event("job-started")

    assert (await next_all).event_type == "session-connected"
    assert (await next_job).event_type == "job-started"
    assert fake.events_calls == 1

    await all_events.aclose()
    await job_events.aclose()
    await _wait_until(lambda: not broker._subscribers)
    await broker.close()


async def test_subscriber_queues_are_bounded() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    events = broker.subscribe()
    first_event = asyncio.create_task(anext(events))
    await _wait_until(lambda: len(broker._subscribers) == 1)

    event_count = broker._SUBSCRIBER_QUEUE_SIZE + 2
    for index in range(event_count):
        await fake.stream.emit_event(f"event-{index}")
    await _wait_until(
        lambda: next(iter(broker._subscribers.values()))[0].qsize()
        == broker._SUBSCRIBER_QUEUE_SIZE
    )

    assert (await first_event).event_type == "event-2"
    queue, _ = next(iter(broker._subscribers.values()))
    assert queue.qsize() == broker._SUBSCRIBER_QUEUE_SIZE - 1
    await events.aclose()
    assert broker._subscribers == {}
    await broker.close()


async def test_broker_reconnects_after_an_unexpected_stream_end() -> None:
    fake = _ReconnectStub()
    broker = _broker(fake)
    broker._INITIAL_RECONNECT_DELAY = 0
    broker._MAX_RECONNECT_DELAY = 0
    events = broker.subscribe()
    next_event = asyncio.create_task(anext(events))
    await _wait_until(lambda: fake.events_calls == 1)

    await fake.stream.finish()
    await _wait_until(lambda: fake.events_calls == 2)
    await fake.reconnected_stream.emit_event("reconnected")

    assert (await next_event).event_type == "reconnected"
    await events.aclose()
    await broker.close()


async def test_client_close_stops_event_subscribers() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    client = SliverClient(_config())
    channel = AsyncMock(spec=grpc.aio.Channel)
    client._channel = channel
    client._stub = cast(PydanticSliverRPCStub, fake)
    client._event_broker = broker
    events = client.events()
    next_event = asyncio.create_task(anext(events))
    await _wait_until(lambda: len(broker._subscribers) == 1)

    await client.close()

    with pytest.raises(StopAsyncIteration):
        await next_event
    assert broker._subscribers == {}
    channel.close.assert_awaited_once_with()


async def test_broker_close_cleans_and_cancels_pending_remote_tasks() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    waiter = asyncio.create_task(
        broker.wait_for_result("client-closing", models.sliverpb.Ping, timeout=1)
    )
    await _wait_until(lambda: "client-closing" in broker._pending)

    await broker.close()

    with pytest.raises(RuntimeError, match="client event broker is closed"):
        await waiter
    assert broker._pending == {}
    assert fake.cancelled == [("client-closing", 1)]


async def test_broker_recovers_when_the_event_result_fetch_is_transient() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    broker._TASK_POLL_INTERVAL = 0.01
    task_id = "failed-result"
    expected = models.sliverpb.Ping(nonce=91210)
    fake.contents[task_id] = models.clientpb.BeaconTask(
        id=task_id,
        state=BeaconTaskState.COMPLETED.value,
        response=_serialize(expected),
    )
    fake.content_errors[task_id] = RuntimeError("content unavailable")
    waiter = asyncio.create_task(
        broker.wait_for_result(task_id, models.sliverpb.Ping, timeout=1)
    )
    await _wait_until(lambda: task_id in broker._pending)

    await fake.stream.emit(task_id)
    await _wait_until(lambda: bool(fake.content_calls))
    fake.content_errors.pop(task_id)

    assert await waiter == expected
    assert len(fake.content_calls) >= 2
    assert broker._pending == {}
    assert broker._resolvers == {}
    assert broker._pollers == {}
    await broker.close()


async def test_broker_timeout_cleans_the_future_and_cancels_the_remote_task() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)

    with pytest.raises(SliverTimeoutError) as raised:
        await broker.wait_for_result(
            "timed-out", models.sliverpb.Ping, timeout=0.01
        )

    assert raised.value.operation == "beacon task timed-out"
    assert raised.value.timeout == 0.01
    assert broker._pending == {}
    assert fake.cancelled == [("timed-out", 0.01)]
    await broker.close()


async def test_broker_cancellation_cleans_and_cancels_the_remote_task() -> None:
    fake = _FakeBeaconStub()
    broker = _broker(fake)
    waiter = asyncio.create_task(
        broker.wait_for_result("cancelled", models.sliverpb.Ping, timeout=1)
    )
    await _wait_until(lambda: "cancelled" in broker._pending)

    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter

    assert broker._pending == {}
    assert fake.cancelled == [("cancelled", 1)]
    await broker.close()


async def test_beacon_execute_raises_for_a_command_result_error() -> None:
    broker = AsyncMock()
    broker.wait_for_result.return_value = models.sliverpb.Ping(
        response=models.commonpb.Response(err="implant rejected command")
    )
    stub = AsyncMock()
    stub.Ping.return_value = models.sliverpb.Ping(
        response=models.commonpb.Response(task_id="task-id")
    )
    beacon = BaseBeacon.__new__(BaseBeacon)
    beacon._closed = False
    beacon._event_broker = broker
    beacon._stub = stub
    beacon._beacon = models.clientpb.Beacon(id="beacon-id")
    beacon.timeout = 17

    with pytest.raises(CommandError) as raised:
        await beacon._execute(
            "Ping", models.sliverpb.Ping(), models.sliverpb.Ping
        )

    assert raised.value.operation == "Ping"
    assert raised.value.target_id == "beacon-id"
    assert raised.value.message == "implant rejected command"


async def test_client_attaches_one_broker_to_all_beacon_wrappers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeBeaconStub()
    shared_broker = _broker(fake)
    client = SliverClient(_config())
    channel = AsyncMock(spec=grpc.aio.Channel)
    client._channel = channel
    client._stub = cast(PydanticSliverRPCStub, fake)
    client._event_broker = shared_broker
    monkeypatch.setattr(
        client,
        "beacon_by_id",
        AsyncMock(side_effect=lambda beacon_id, timeout: models.clientpb.Beacon(id=beacon_id)),
    )
    monkeypatch.setattr(
        beacon_module,
        "PydanticSliverRPCStub",
        lambda channel: cast(PydanticSliverRPCStub, fake),
    )

    first = await client.interact_beacon("beacon-one")
    second = await client.interact_beacon("beacon-two")

    assert first is not None
    assert second is not None
    assert first._event_broker is shared_broker
    assert second._event_broker is shared_broker
    assert fake.events_calls == 0
    await first.close()
    assert not shared_broker._closed

    await client.close()
    assert shared_broker._closed
    channel.close.assert_awaited_once_with()
