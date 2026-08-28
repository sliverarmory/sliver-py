from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

import grpc
import pytest

from sliver import models
from sliver._pb.clientpb import client_pb2
from sliver._pb.commonpb import common_pb2
from sliver._rpc import (
    StreamStreamCall,
    StreamStreamMultiCallable,
    StreamUnaryCall,
    StreamUnaryMultiCallable,
    UnaryStreamCall,
    UnaryStreamMultiCallable,
    UnaryUnaryCall,
    UnaryUnaryMultiCallable,
)


class _RawCall:
    def __init__(
        self,
        *,
        unary_response: Any = None,
        stream_responses: list[Any] | None = None,
    ) -> None:
        self.unary_response = unary_response
        self.stream_responses = list(stream_responses or [])
        self.writes: list[Any] = []
        self.finished_writing = False
        self.cancel_requested = False

    def __await__(self):
        async def receive_response() -> Any:
            return self.unary_response

        return receive_response().__await__()

    async def __aiter__(self) -> AsyncIterator[Any]:
        for response in self.stream_responses:
            yield response

    async def read(self) -> Any:
        if not self.stream_responses:
            return grpc.aio.EOF
        return self.stream_responses.pop(0)

    async def write(self, request: Any) -> None:
        self.writes.append(request)

    async def done_writing(self) -> None:
        self.finished_writing = True

    def add_done_callback(self, callback: Any) -> None:
        callback(self)

    def cancel(self) -> bool:
        self.cancel_requested = True
        return True

    def cancelled(self) -> bool:
        return self.cancel_requested

    def done(self) -> bool:
        return True

    def time_remaining(self) -> float:
        return 12.5

    async def initial_metadata(self) -> tuple[tuple[str, str], ...]:
        return (("phase", "initial"),)

    async def trailing_metadata(self) -> tuple[tuple[str, str], ...]:
        return (("phase", "trailing"),)

    async def code(self) -> grpc.StatusCode:
        return grpc.StatusCode.OK

    async def details(self) -> str:
        return "complete"

    async def wait_for_connection(self) -> None:
        return None


class _RecordingCallable:
    def __init__(self, call: _RawCall):
        self.call = call
        self.request: Any = None
        self.kwargs: dict[str, Any] = {}

    def __call__(self, request: Any, **kwargs: Any) -> _RawCall:
        self.request = request
        self.kwargs = kwargs
        return self.call


async def test_unary_unary_converts_request_response_and_call_options() -> None:
    raw_call = _RawCall(unary_response=client_pb2.Version(Major=1, Minor=2, Patch=3))
    raw_callable = _RecordingCallable(raw_call)
    rpc = UnaryUnaryMultiCallable(
        raw_callable, models.commonpb.Empty, models.clientpb.Version
    )

    response = await rpc(
        models.commonpb.Empty(),
        timeout=15,
        metadata=(("operator", "alice"),),
        wait_for_ready=True,
    )

    assert isinstance(raw_callable.request, common_pb2.Empty)
    assert raw_callable.kwargs["timeout"] == 15
    assert raw_callable.kwargs["metadata"] == (("operator", "alice"),)
    assert raw_callable.kwargs["wait_for_ready"] is True
    assert isinstance(response, models.clientpb.Version)
    assert (response.major, response.minor, response.patch) == (1, 2, 3)
    assert isinstance(rpc(models.commonpb.Empty()), UnaryUnaryCall)


async def test_unary_stream_converts_iteration_and_read_responses() -> None:
    raw_call = _RawCall(
        stream_responses=[
            client_pb2.Event(EventType="first"),
            client_pb2.Event(EventType="second"),
        ]
    )
    raw_callable = _RecordingCallable(raw_call)
    rpc = UnaryStreamMultiCallable(
        raw_callable, models.commonpb.Empty, models.clientpb.Event
    )

    converted_call = rpc(models.commonpb.Empty())
    responses = [response async for response in converted_call]

    assert isinstance(raw_callable.request, common_pb2.Empty)
    assert all(isinstance(response, models.clientpb.Event) for response in responses)
    assert [response.event_type for response in responses] == ["first", "second"]

    read_call = _RawCall(stream_responses=[client_pb2.Event(EventType="read")])
    converted_read_call = UnaryStreamMultiCallable(
        _RecordingCallable(read_call),
        models.commonpb.Empty,
        models.clientpb.Event,
    )(models.commonpb.Empty())
    response = await converted_read_call.read()

    assert isinstance(response, models.clientpb.Event)
    assert response.event_type == "read"
    assert await converted_read_call.read() is grpc.aio.EOF
    assert isinstance(converted_read_call, UnaryStreamCall)


async def test_stream_unary_converts_sync_and_async_request_iterators() -> None:
    raw_call = _RawCall(unary_response=common_pb2.Empty())
    raw_callable = _RecordingCallable(raw_call)
    rpc = StreamUnaryMultiCallable(
        raw_callable,
        models.clientpb.ClientLogData,
        models.commonpb.Empty,
    )
    requests: Iterator[models.clientpb.ClientLogData] = iter(
        [
            models.clientpb.ClientLogData(stream="stdout", data=b"one"),
            models.clientpb.ClientLogData(stream="stderr", data=b"two"),
        ]
    )

    response_call = rpc(requests)
    converted_requests = list(raw_callable.request)
    response = await response_call

    assert all(
        isinstance(item, client_pb2.ClientLogData) for item in converted_requests
    )
    assert [(item.Stream, item.Data) for item in converted_requests] == [
        ("stdout", b"one"),
        ("stderr", b"two"),
    ]
    assert isinstance(response, models.commonpb.Empty)

    async def async_requests() -> AsyncIterator[models.clientpb.ClientLogData]:
        yield models.clientpb.ClientLogData(stream="stdout", data=b"async")

    async_raw_callable = _RecordingCallable(_RawCall(unary_response=common_pb2.Empty()))
    async_rpc = StreamUnaryMultiCallable(
        async_raw_callable,
        models.clientpb.ClientLogData,
        models.commonpb.Empty,
    )

    async_response_call = async_rpc(async_requests())
    async_converted = [item async for item in async_raw_callable.request]
    async_response = await async_response_call

    assert len(async_converted) == 1
    assert isinstance(async_converted[0], client_pb2.ClientLogData)
    assert async_converted[0].Data == b"async"
    assert isinstance(async_response, models.commonpb.Empty)
    assert isinstance(async_response_call, StreamUnaryCall)


async def test_stream_stream_converts_write_read_and_callback_boundaries() -> None:
    raw_call = _RawCall(stream_responses=[client_pb2.Event(EventType="bidirectional")])
    raw_callable = _RecordingCallable(raw_call)
    rpc = StreamStreamMultiCallable(
        raw_callable,
        models.clientpb.ClientLogData,
        models.clientpb.Event,
    )

    call = rpc()
    assert isinstance(call, StreamStreamCall)
    assert raw_callable.request is None

    await call.write(models.clientpb.ClientLogData(stream="stdout", data=b"data"))
    response = await call.read()
    await call.done_writing()
    callbacks: list[
        StreamStreamCall[models.clientpb.ClientLogData, models.clientpb.Event]
    ] = []
    call.add_done_callback(callbacks.append)

    assert len(raw_call.writes) == 1
    assert isinstance(raw_call.writes[0], client_pb2.ClientLogData)
    assert raw_call.writes[0].Data == b"data"
    assert isinstance(response, models.clientpb.Event)
    assert response.event_type == "bidirectional"
    assert callbacks == [call]
    assert raw_call.finished_writing
    assert await call.read() is grpc.aio.EOF

    assert call.done()
    assert not call.cancelled()
    assert call.time_remaining() == 12.5
    assert await call.initial_metadata() == (("phase", "initial"),)
    assert await call.trailing_metadata() == (("phase", "trailing"),)
    assert await call.code() is grpc.StatusCode.OK
    assert await call.details() == "complete"
    await call.wait_for_connection()
    assert call.cancel()
    assert call.cancelled()


async def test_rpc_boundary_rejects_raw_or_wrong_request_types() -> None:
    unary_rpc = UnaryUnaryMultiCallable(
        _RecordingCallable(_RawCall(unary_response=common_pb2.Empty())),
        models.commonpb.Empty,
        models.commonpb.Empty,
    )

    with pytest.raises(TypeError, match="RPC request must be Empty"):
        unary_rpc(common_pb2.Empty())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RPC request must be Empty"):
        unary_rpc(iter([models.commonpb.Empty()]))

    raw_callable = _RecordingCallable(_RawCall(unary_response=common_pb2.Empty()))
    streaming_rpc = StreamUnaryMultiCallable(
        raw_callable,
        models.clientpb.ClientLogData,
        models.commonpb.Empty,
    )
    streamed_call = streaming_rpc(iter([client_pb2.ClientLogData()]))  # type: ignore[list-item]
    with pytest.raises(TypeError, match="RPC request must be ClientLogData"):
        list(raw_callable.request)

    manual_call = streaming_rpc()
    with pytest.raises(TypeError, match="RPC request must be ClientLogData"):
        await manual_call.write(client_pb2.ClientLogData())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="requires a Pydantic request stream"):
        streaming_rpc(models.clientpb.ClientLogData())

    # gRPC-style stream conversion is intentionally lazy.
    assert isinstance(streamed_call, StreamUnaryCall)


async def test_rpc_boundary_never_returns_an_unexpected_wire_model() -> None:
    rpc = UnaryUnaryMultiCallable(
        _RecordingCallable(_RawCall(unary_response=common_pb2.Empty())),
        models.commonpb.Empty,
        models.clientpb.Version,
    )

    with pytest.raises(TypeError, match="RPC response must convert to Version"):
        await rpc(models.commonpb.Empty())
