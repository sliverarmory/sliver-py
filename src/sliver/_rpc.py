"""Pydantic-aware adapters around the generated gRPC client stub."""

from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterator
from typing import Any

from .models import protobuf_to_pydantic, pydantic_to_protobuf
from .pb.rpcpb.services_pb2_grpc import SliverRPCStub


class _ConvertedCall:
    """Preserve the gRPC call API while converting returned messages."""

    def __init__(self, call: Any):
        self._call = call

    def __await__(self):
        async def wait_for_result() -> Any:
            return protobuf_to_pydantic(await self._call)

        return wait_for_result().__await__()

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[Any]:
        async for message in self._call:
            yield protobuf_to_pydantic(message)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._call, name)


class _ConvertedMultiCallable:
    def __init__(self, call: Callable[..., Any]):
        self._call = call

    def __call__(self, request: Any, *args: Any, **kwargs: Any) -> _ConvertedCall:
        protobuf_request = _convert_request(request)
        return _ConvertedCall(self._call(protobuf_request, *args, **kwargs))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._call, name)


def _convert_request(request: Any) -> Any:
    if isinstance(request, AsyncIterable):
        return _convert_async_requests(request)
    if isinstance(request, Iterator):
        return (pydantic_to_protobuf(item) for item in request)
    return pydantic_to_protobuf(request)


async def _convert_async_requests(request: AsyncIterable[Any]) -> AsyncIterator[Any]:
    async for item in request:
        yield pydantic_to_protobuf(item)


class PydanticSliverRPCStub:
    """Convert Pydantic requests and protobuf responses at the RPC boundary."""

    def __init__(self, channel: Any):
        self.raw = SliverRPCStub(channel)
        self._methods: dict[str, _ConvertedMultiCallable] = {}

    def __getattr__(self, name: str) -> Any:
        method = getattr(self.raw, name)
        if not callable(method):
            return method
        if name not in self._methods:
            self._methods[name] = _ConvertedMultiCallable(method)
        return self._methods[name]
