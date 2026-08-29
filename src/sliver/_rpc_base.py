"""Typed Pydantic adapters for the four asynchronous gRPC call shapes."""

from __future__ import annotations

from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Iterable,
    Sequence,
)
from typing import Generic, Protocol, TypeVar, cast

import grpc
from google.protobuf.message import Message as _Message
from grpc.aio._typing import EOFType as _EOFType

from .errors import RPCError
from .models import ProtobufModel, _model_to_protobuf, _protobuf_to_pydantic

_Metadata = Sequence[tuple[str, str | bytes]]

_RequestT = TypeVar("_RequestT", bound=ProtobufModel)
_ResponseT = TypeVar("_ResponseT", bound=ProtobufModel)
_CallT = TypeVar("_CallT", bound="_CallBase")


class _RawCommonCall(Protocol):
    def add_done_callback(self, callback: Callable[[object], None]) -> None: ...

    def cancel(self) -> bool: ...

    def cancelled(self) -> bool: ...

    def done(self) -> bool: ...

    def time_remaining(self) -> float | None: ...

    async def initial_metadata(self) -> grpc.aio.Metadata: ...

    async def trailing_metadata(self) -> grpc.aio.Metadata: ...

    async def code(self) -> grpc.StatusCode: ...

    async def details(self) -> str: ...

    async def wait_for_connection(self) -> None: ...


class _RawReadableCall(Protocol):
    async def read(self) -> object: ...


class _RawWritableCall(Protocol):
    async def write(self, request: _Message) -> None: ...

    async def done_writing(self) -> None: ...


class _CallBase:
    """Common lifecycle operations exposed by every converted call."""

    def __init__(self, call: object, operation: str = "RPC") -> None:
        self.__call = call
        self.operation = operation

    @property
    def _raw_call(self) -> object:
        return self.__call

    def add_done_callback(self: _CallT, callback: Callable[[_CallT], None]) -> None:
        """Invoke ``callback`` with this converted call, never the wire call."""

        raw = cast(_RawCommonCall, self.__call)
        raw.add_done_callback(lambda _raw_call: callback(self))

    def cancel(self) -> bool:
        return cast(_RawCommonCall, self.__call).cancel()

    def cancelled(self) -> bool:
        return cast(_RawCommonCall, self.__call).cancelled()

    def done(self) -> bool:
        return cast(_RawCommonCall, self.__call).done()

    def time_remaining(self) -> float | None:
        return cast(_RawCommonCall, self.__call).time_remaining()

    async def initial_metadata(self) -> grpc.aio.Metadata:
        return await cast(_RawCommonCall, self.__call).initial_metadata()

    async def trailing_metadata(self) -> grpc.aio.Metadata:
        return await cast(_RawCommonCall, self.__call).trailing_metadata()

    async def code(self) -> grpc.StatusCode:
        return await cast(_RawCommonCall, self.__call).code()

    async def details(self) -> str:
        return await cast(_RawCommonCall, self.__call).details()

    async def wait_for_connection(self) -> None:
        try:
            await cast(_RawCommonCall, self.__call).wait_for_connection()
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error


class UnaryUnaryCall(_CallBase, Generic[_ResponseT]):
    """Awaitable call for one request and one Pydantic response."""

    def __init__(
        self,
        call: object,
        response_type: type[_ResponseT],
        operation: str = "RPC",
    ) -> None:
        super().__init__(call, operation)
        self.response_type = response_type

    def __await__(self) -> Generator[object, None, _ResponseT]:
        async def wait_for_result() -> _ResponseT:
            try:
                response = await cast(Awaitable[object], self._raw_call)
            except grpc.aio.AioRpcError as error:
                raise _translate_rpc_error(self.operation, error) from error
            return _convert_response(response, self.response_type)

        return wait_for_result().__await__()


class UnaryStreamCall(_CallBase, Generic[_ResponseT]):
    """Async iterable/readable call for a server response stream."""

    def __init__(
        self,
        call: object,
        response_type: type[_ResponseT],
        operation: str = "RPC",
    ) -> None:
        super().__init__(call, operation)
        self.response_type = response_type

    def __aiter__(self) -> AsyncIterator[_ResponseT]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[_ResponseT]:
        try:
            async for response in cast(AsyncIterable[object], self._raw_call):
                yield _convert_response(response, self.response_type)
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error

    async def read(self) -> _ResponseT | _EOFType:
        try:
            response = await cast(_RawReadableCall, self._raw_call).read()
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error
        if response is grpc.aio.EOF:
            return grpc.aio.EOF
        return _convert_response(response, self.response_type)


class StreamUnaryCall(_CallBase, Generic[_RequestT, _ResponseT]):
    """Writable and awaitable call for a client request stream."""

    def __init__(
        self,
        call: object,
        request_type: type[_RequestT],
        response_type: type[_ResponseT],
        operation: str = "RPC",
    ) -> None:
        super().__init__(call, operation)
        self.request_type = request_type
        self.response_type = response_type

    def __await__(self) -> Generator[object, None, _ResponseT]:
        async def wait_for_result() -> _ResponseT:
            try:
                response = await cast(Awaitable[object], self._raw_call)
            except grpc.aio.AioRpcError as error:
                raise _translate_rpc_error(self.operation, error) from error
            return _convert_response(response, self.response_type)

        return wait_for_result().__await__()

    async def write(self, request: _RequestT) -> None:
        """Write one Pydantic request to the client stream."""

        protobuf_request = _convert_single_request(request, self.request_type)
        try:
            await cast(_RawWritableCall, self._raw_call).write(protobuf_request)
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error

    async def done_writing(self) -> None:
        try:
            await cast(_RawWritableCall, self._raw_call).done_writing()
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error


class StreamStreamCall(_CallBase, Generic[_RequestT, _ResponseT]):
    """Readable/writable call for bidirectional Pydantic streams."""

    def __init__(
        self,
        call: object,
        request_type: type[_RequestT],
        response_type: type[_ResponseT],
        operation: str = "RPC",
    ) -> None:
        super().__init__(call, operation)
        self.request_type = request_type
        self.response_type = response_type

    def __aiter__(self) -> AsyncIterator[_ResponseT]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[_ResponseT]:
        try:
            async for response in cast(AsyncIterable[object], self._raw_call):
                yield _convert_response(response, self.response_type)
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error

    async def read(self) -> _ResponseT | _EOFType:
        try:
            response = await cast(_RawReadableCall, self._raw_call).read()
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error
        if response is grpc.aio.EOF:
            return grpc.aio.EOF
        return _convert_response(response, self.response_type)

    async def write(self, request: _RequestT) -> None:
        """Write one Pydantic request to the client stream."""

        protobuf_request = _convert_single_request(request, self.request_type)
        try:
            await cast(_RawWritableCall, self._raw_call).write(protobuf_request)
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error

    async def done_writing(self) -> None:
        try:
            await cast(_RawWritableCall, self._raw_call).done_writing()
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error


class _MultiCallableBase(Generic[_RequestT, _ResponseT]):
    def __init__(
        self,
        call: Callable[..., object],
        request_type: type[_RequestT],
        response_type: type[_ResponseT],
        operation: str = "RPC",
    ) -> None:
        self.__call = call
        self.request_type = request_type
        self.response_type = response_type
        self.operation = operation

    def _invoke(
        self,
        request: object,
        *,
        timeout: float | None,
        metadata: _Metadata | None,
        credentials: grpc.CallCredentials | None,
        wait_for_ready: bool | None,
        compression: grpc.Compression | None,
    ) -> object:
        try:
            return self.__call(
                request,
                timeout=timeout,
                metadata=metadata,
                credentials=credentials,
                wait_for_ready=wait_for_ready,
                compression=compression,
            )
        except grpc.aio.AioRpcError as error:
            raise _translate_rpc_error(self.operation, error) from error


class UnaryUnaryMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    """Typed callable for a unary-request, unary-response RPC."""

    def __call__(
        self,
        request: _RequestT,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: grpc.CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: grpc.Compression | None = None,
    ) -> UnaryUnaryCall[_ResponseT]:
        protobuf_request = _convert_single_request(request, self.request_type)
        call = self._invoke(
            protobuf_request,
            timeout=timeout,
            metadata=metadata,
            credentials=credentials,
            wait_for_ready=wait_for_ready,
            compression=compression,
        )
        return UnaryUnaryCall(call, self.response_type, self.operation)


class UnaryStreamMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    """Typed callable for a unary-request, streaming-response RPC."""

    def __call__(
        self,
        request: _RequestT,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: grpc.CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: grpc.Compression | None = None,
    ) -> UnaryStreamCall[_ResponseT]:
        protobuf_request = _convert_single_request(request, self.request_type)
        call = self._invoke(
            protobuf_request,
            timeout=timeout,
            metadata=metadata,
            credentials=credentials,
            wait_for_ready=wait_for_ready,
            compression=compression,
        )
        return UnaryStreamCall(call, self.response_type, self.operation)


class StreamUnaryMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    """Typed callable for a streaming-request, unary-response RPC."""

    def __call__(
        self,
        request_iterator: Iterable[_RequestT] | AsyncIterable[_RequestT] | None = None,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: grpc.CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: grpc.Compression | None = None,
    ) -> StreamUnaryCall[_RequestT, _ResponseT]:
        protobuf_requests = _convert_request_stream(request_iterator, self.request_type)
        call = self._invoke(
            protobuf_requests,
            timeout=timeout,
            metadata=metadata,
            credentials=credentials,
            wait_for_ready=wait_for_ready,
            compression=compression,
        )
        return StreamUnaryCall(
            call, self.request_type, self.response_type, self.operation
        )


class StreamStreamMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    """Typed callable for a bidirectional streaming RPC."""

    def __call__(
        self,
        request_iterator: Iterable[_RequestT] | AsyncIterable[_RequestT] | None = None,
        timeout: float | None = None,
        metadata: _Metadata | None = None,
        credentials: grpc.CallCredentials | None = None,
        wait_for_ready: bool | None = None,
        compression: grpc.Compression | None = None,
    ) -> StreamStreamCall[_RequestT, _ResponseT]:
        protobuf_requests = _convert_request_stream(request_iterator, self.request_type)
        call = self._invoke(
            protobuf_requests,
            timeout=timeout,
            metadata=metadata,
            credentials=credentials,
            wait_for_ready=wait_for_ready,
            compression=compression,
        )
        return StreamStreamCall(
            call, self.request_type, self.response_type, self.operation
        )


def _translate_rpc_error(operation: str, error: grpc.aio.AioRpcError) -> RPCError:
    """Convert gRPC transport failures into the public error taxonomy."""

    status = error.code()
    status_name = status.name if isinstance(status, grpc.StatusCode) else str(status)
    details = error.details() or str(error)
    return RPCError(operation, details, status=status_name)


def _convert_request_stream(
    requests: Iterable[_RequestT] | AsyncIterable[_RequestT] | None,
    request_type: type[_RequestT],
) -> Iterable[_Message] | AsyncIterable[_Message] | None:
    if requests is None:
        return None
    if isinstance(requests, ProtobufModel):
        raise TypeError("this RPC requires a Pydantic request stream or write() calls")
    if isinstance(requests, AsyncIterable):
        return _convert_async_requests(requests, request_type)
    if isinstance(requests, Iterable):
        return (_convert_single_request(request, request_type) for request in requests)
    raise TypeError("this RPC requires a Pydantic request stream or write() calls")


def _convert_single_request(request: object, request_type: type[_RequestT]) -> _Message:
    if not isinstance(request, request_type):
        raise TypeError(
            f"RPC request must be {request_type.__name__}; got {type(request).__name__}"
        )
    return _model_to_protobuf(request)


async def _convert_async_requests(
    requests: AsyncIterable[_RequestT], request_type: type[_RequestT]
) -> AsyncIterator[_Message]:
    async for request in requests:
        yield _convert_single_request(request, request_type)


def _convert_response(response: object, response_type: type[_ResponseT]) -> _ResponseT:
    converted = _protobuf_to_pydantic(response)
    if not isinstance(converted, response_type):
        raise TypeError(
            f"RPC response must convert to {response_type.__name__}; "
            f"got {type(converted).__name__}"
        )
    return converted
