"""Pydantic-aware adapters around the generated gRPC client stub."""

from __future__ import annotations

from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Generator,
    Iterator,
    Sequence,
)
from typing import Any

import grpc

from ._pb.rpcpb import services_pb2 as _services_pb2
from ._pb.rpcpb.services_pb2_grpc import SliverRPCStub as _WireSliverRPCStub
from .models import (
    ProtobufModel,
    _get_pydantic_model,
    _model_to_protobuf,
    _protobuf_to_pydantic,
)

_Metadata = Sequence[tuple[str, str | bytes]]
_Request = ProtobufModel | Iterator[ProtobufModel] | AsyncIterable[ProtobufModel] | None


class _ConvertedCall:
    """Preserve the gRPC call API while converting returned messages."""

    def __init__(
        self,
        call: Any,
        request_type: type[ProtobufModel],
        response_type: type[ProtobufModel],
    ) -> None:
        self.__call = call
        self._request_type = request_type
        self._response_type = response_type

    def __await__(self) -> Generator[object, None, ProtobufModel]:
        async def wait_for_result() -> ProtobufModel:
            return _convert_response(await self.__call, self._response_type)

        return wait_for_result().__await__()

    def __aiter__(self) -> AsyncIterator[ProtobufModel]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[ProtobufModel]:
        async for message in self.__call:
            yield _convert_response(message, self._response_type)

    async def read(self) -> ProtobufModel | object:
        """Read one converted response from a streaming RPC."""

        response = await self.__call.read()
        if response is grpc.aio.EOF:
            return response
        return _convert_response(response, self._response_type)

    async def write(self, request: ProtobufModel) -> None:
        """Write one Pydantic request to a client-streaming RPC."""

        await self.__call.write(_convert_single_request(request, self._request_type))

    async def done_writing(self) -> None:
        await self.__call.done_writing()

    def add_done_callback(
        self, callback: Callable[[_ConvertedCall], None]
    ) -> None:
        """Invoke ``callback`` with this converted call, never the raw call."""

        self.__call.add_done_callback(lambda _raw_call: callback(self))

    def cancel(self) -> bool:
        return self.__call.cancel()

    def cancelled(self) -> bool:
        return self.__call.cancelled()

    def done(self) -> bool:
        return self.__call.done()

    def time_remaining(self) -> float | None:
        return self.__call.time_remaining()

    async def initial_metadata(self) -> grpc.aio.Metadata:
        return await self.__call.initial_metadata()

    async def trailing_metadata(self) -> grpc.aio.Metadata:
        return await self.__call.trailing_metadata()

    async def code(self) -> grpc.StatusCode:
        return await self.__call.code()

    async def details(self) -> str:
        return await self.__call.details()

    async def wait_for_connection(self) -> None:
        await self.__call.wait_for_connection()


class _ConvertedMultiCallable:
    def __init__(
        self,
        call: Callable[..., Any],
        request_type: type[ProtobufModel],
        response_type: type[ProtobufModel],
        *,
        client_streaming: bool = False,
    ) -> None:
        self.__call = call
        self.request_type = request_type
        self.response_type = response_type
        self._client_streaming = client_streaming

    def __call__(
        self,
        request: _Request = None,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: grpc.CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: grpc.Compression | None = None,
    ) -> _ConvertedCall:
        protobuf_request = _convert_request(
            request,
            self.request_type,
            client_streaming=self._client_streaming,
        )
        return _ConvertedCall(
            self.__call(
                protobuf_request,
                timeout=timeout,
                metadata=metadata,
                credentials=credentials,
                wait_for_ready=wait_for_ready,
                compression=compression,
            ),
            self.request_type,
            self.response_type,
        )


def _convert_request(
    request: _Request,
    request_type: type[ProtobufModel],
    *,
    client_streaming: bool,
) -> Any:
    if request is None:
        if client_streaming:
            return None
        raise TypeError(f"RPC request must be {request_type.__name__}; got None")
    if isinstance(request, AsyncIterable):
        if not client_streaming:
            raise TypeError("this RPC does not accept a request stream")
        return _convert_async_requests(request, request_type)
    if isinstance(request, Iterator):
        if not client_streaming:
            raise TypeError("this RPC does not accept a request stream")
        return (_convert_single_request(item, request_type) for item in request)
    if client_streaming:
        raise TypeError("this RPC requires a Pydantic request stream or write() calls")
    return _convert_single_request(request, request_type)


def _convert_single_request(
    request: object, request_type: type[ProtobufModel]
) -> Any:
    if not isinstance(request, request_type):
        raise TypeError(
            f"RPC request must be {request_type.__name__}; "
            f"got {type(request).__name__}"
        )
    return _model_to_protobuf(request)


async def _convert_async_requests(
    request: AsyncIterable[ProtobufModel],
    request_type: type[ProtobufModel],
) -> AsyncIterator[Any]:
    async for item in request:
        yield _convert_single_request(item, request_type)


def _convert_response(
    response: object, response_type: type[ProtobufModel]
) -> ProtobufModel:
    converted = _protobuf_to_pydantic(response)
    if not isinstance(converted, response_type):
        raise TypeError(
            f"RPC response must convert to {response_type.__name__}; "
            f"got {type(converted).__name__}"
        )
    return converted


class PydanticSliverRPCStub:
    """Convert Pydantic requests and protobuf responses at the RPC boundary."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        self.__raw = _WireSliverRPCStub(channel)
        self._methods: dict[str, _ConvertedMultiCallable] = {}

    def __dir__(self) -> list[str]:
        service = _services_pb2.DESCRIPTOR.services_by_name["SliverRPC"]
        return sorted({*super().__dir__(), *service.methods_by_name})

    def __getattr__(self, name: str) -> _ConvertedMultiCallable:
        method = getattr(self.__raw, name)
        if not callable(method):
            raise AttributeError(name)
        if name not in self._methods:
            service = _services_pb2.DESCRIPTOR.services_by_name["SliverRPC"]
            try:
                descriptor = service.methods_by_name[name]
            except KeyError as exc:
                raise AttributeError(name) from exc
            self._methods[name] = _ConvertedMultiCallable(
                method,
                _get_pydantic_model(descriptor.input_type),
                _get_pydantic_model(descriptor.output_type),
                client_streaming=descriptor.client_streaming,
            )
        return self._methods[name]
