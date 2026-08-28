"""Static Pydantic adapters for the four asynchronous gRPC call shapes."""

from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Collection,
    Generator,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Sequence,
    ValuesView,
)
from enum import Enum
from typing import Generic, TypeVar

from .models import ProtobufModel

_Metadata = Sequence[tuple[str, str | bytes]]

_RequestT = TypeVar("_RequestT", bound=ProtobufModel)
_ResponseT = TypeVar("_ResponseT", bound=ProtobufModel)
_CallT = TypeVar("_CallT", bound="_CallBase")

class _EOFType: ...

class _MetadataResult(Collection[tuple[str, str | bytes]]):
    def __iter__(self) -> Iterator[tuple[str, str | bytes]]: ...
    def __len__(self) -> int: ...
    def __contains__(self, key: object) -> bool: ...
    def add(self, key: str, value: str | bytes) -> None: ...
    def delete_all(self, key: str) -> None: ...
    def get(
        self, key: str, default: str | bytes | None = ...
    ) -> str | bytes | None: ...
    def get_all(self, key: str) -> list[str | bytes]: ...
    def items(self) -> ItemsView[str, str | bytes]: ...
    def keys(self) -> KeysView[str]: ...
    def set_all(self, key: str, values: list[str | bytes]) -> None: ...
    def values(self) -> ValuesView[str | bytes]: ...

class _CallBase:
    def __init__(self, call: object) -> None: ...
    @property
    def _raw_call(self) -> object: ...
    def add_done_callback(self: _CallT, callback: Callable[[_CallT], None]) -> None: ...
    def cancel(self) -> bool: ...
    def cancelled(self) -> bool: ...
    def done(self) -> bool: ...
    def time_remaining(self) -> float | None: ...
    async def initial_metadata(self) -> _MetadataResult: ...
    async def trailing_metadata(self) -> _MetadataResult: ...
    async def code(self) -> Enum: ...
    async def details(self) -> str: ...
    async def wait_for_connection(self) -> None: ...

class UnaryUnaryCall(_CallBase, Generic[_ResponseT]):
    response_type: type[_ResponseT]
    def __init__(self, call: object, response_type: type[_ResponseT]) -> None: ...
    def __await__(self) -> Generator[object, None, _ResponseT]: ...

class UnaryStreamCall(_CallBase, Generic[_ResponseT]):
    response_type: type[_ResponseT]
    def __init__(self, call: object, response_type: type[_ResponseT]) -> None: ...
    def __aiter__(self) -> AsyncIterator[_ResponseT]: ...
    async def read(self) -> _ResponseT | _EOFType: ...

class StreamUnaryCall(_CallBase, Generic[_RequestT, _ResponseT]):
    request_type: type[_RequestT]
    response_type: type[_ResponseT]
    def __init__(
        self,
        call: object,
        request_type: type[_RequestT],
        response_type: type[_ResponseT],
    ) -> None: ...
    def __await__(self) -> Generator[object, None, _ResponseT]: ...
    async def write(self, request: _RequestT) -> None: ...
    async def done_writing(self) -> None: ...

class StreamStreamCall(_CallBase, Generic[_RequestT, _ResponseT]):
    request_type: type[_RequestT]
    response_type: type[_ResponseT]
    def __init__(
        self,
        call: object,
        request_type: type[_RequestT],
        response_type: type[_ResponseT],
    ) -> None: ...
    def __aiter__(self) -> AsyncIterator[_ResponseT]: ...
    async def read(self) -> _ResponseT | _EOFType: ...
    async def write(self, request: _RequestT) -> None: ...
    async def done_writing(self) -> None: ...

class _MultiCallableBase(Generic[_RequestT, _ResponseT]):
    request_type: type[_RequestT]
    response_type: type[_ResponseT]
    def __init__(
        self,
        call: object,
        request_type: type[_RequestT],
        response_type: type[_ResponseT],
    ) -> None: ...

class UnaryUnaryMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    def __call__(
        self,
        request: _RequestT,
        timeout: float | None = ...,
        metadata: _Metadata | None = ...,
        credentials: object | None = ...,
        wait_for_ready: bool | None = ...,
        compression: Enum | None = ...,
    ) -> UnaryUnaryCall[_ResponseT]: ...

class UnaryStreamMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    def __call__(
        self,
        request: _RequestT,
        timeout: float | None = ...,
        metadata: _Metadata | None = ...,
        credentials: object | None = ...,
        wait_for_ready: bool | None = ...,
        compression: Enum | None = ...,
    ) -> UnaryStreamCall[_ResponseT]: ...

class StreamUnaryMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    def __call__(
        self,
        request_iterator: Iterable[_RequestT] | AsyncIterable[_RequestT] | None = ...,
        timeout: float | None = ...,
        metadata: _Metadata | None = ...,
        credentials: object | None = ...,
        wait_for_ready: bool | None = ...,
        compression: Enum | None = ...,
    ) -> StreamUnaryCall[_RequestT, _ResponseT]: ...

class StreamStreamMultiCallable(_MultiCallableBase[_RequestT, _ResponseT]):
    def __call__(
        self,
        request_iterator: Iterable[_RequestT] | AsyncIterable[_RequestT] | None = ...,
        timeout: float | None = ...,
        metadata: _Metadata | None = ...,
        credentials: object | None = ...,
        wait_for_ready: bool | None = ...,
        compression: Enum | None = ...,
    ) -> StreamStreamCall[_RequestT, _ResponseT]: ...
