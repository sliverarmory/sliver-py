from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from sliver import models
from sliver._rpc import _ConvertedMultiCallable
from sliver.pb.clientpb import client_pb2
from sliver.pb.commonpb import common_pb2


class _UnaryCall:
    def __init__(self, response: Any):
        self.response = response

    def __await__(self):
        async def receive_response() -> Any:
            return self.response

        return receive_response().__await__()


class _ServerStreamCall:
    def __init__(self, responses: list[Any]):
        self.responses = responses

    async def __aiter__(self) -> AsyncIterator[Any]:
        for response in self.responses:
            yield response


class _RecordingCallable:
    def __init__(self, call: Any):
        self.call = call
        self.request: Any = None
        self.args: tuple[Any, ...] = ()
        self.kwargs: dict[str, Any] = {}

    def __call__(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        self.request = request
        self.args = args
        self.kwargs = kwargs
        return self.call


async def test_rpc_adapter_converts_a_unary_request_and_response() -> None:
    raw_response = client_pb2.Version(Major=1, Minor=2, Patch=3)
    raw_callable = _RecordingCallable(_UnaryCall(raw_response))
    rpc = _ConvertedMultiCallable(raw_callable)

    response = await rpc(models.commonpb.Empty(), timeout=15)

    assert isinstance(raw_callable.request, common_pb2.Empty)
    assert raw_callable.kwargs == {"timeout": 15}
    assert isinstance(response, models.clientpb.Version)
    assert (response.major, response.minor, response.patch) == (1, 2, 3)


async def test_rpc_adapter_converts_each_server_stream_response() -> None:
    raw_callable = _RecordingCallable(
        _ServerStreamCall(
            [
                client_pb2.Event(EventType="first"),
                client_pb2.Event(EventType="second"),
            ]
        )
    )
    rpc = _ConvertedMultiCallable(raw_callable)

    responses = [response async for response in rpc(models.commonpb.Empty())]

    assert isinstance(raw_callable.request, common_pb2.Empty)
    assert all(isinstance(response, models.clientpb.Event) for response in responses)
    assert [response.event_type for response in responses] == ["first", "second"]


async def test_rpc_adapter_converts_a_synchronous_client_stream() -> None:
    raw_callable = _RecordingCallable(_UnaryCall(common_pb2.Empty()))
    rpc = _ConvertedMultiCallable(raw_callable)
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


async def test_rpc_adapter_converts_an_asynchronous_client_stream() -> None:
    async def requests() -> AsyncIterator[models.clientpb.ClientLogData]:
        yield models.clientpb.ClientLogData(stream="stdout", data=b"one")
        yield models.clientpb.ClientLogData(stream="stderr", data=b"two")

    raw_callable = _RecordingCallable(_UnaryCall(common_pb2.Empty()))
    rpc = _ConvertedMultiCallable(raw_callable)

    response_call = rpc(requests())
    converted_requests = [item async for item in raw_callable.request]
    response = await response_call

    assert all(
        isinstance(item, client_pb2.ClientLogData) for item in converted_requests
    )
    assert [(item.Stream, item.Data) for item in converted_requests] == [
        ("stdout", b"one"),
        ("stderr", b"two"),
    ]
    assert isinstance(response, models.commonpb.Empty)
