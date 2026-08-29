"""Static boundary for the private Pydantic wire-conversion runtime."""

from __future__ import annotations

from collections.abc import Mapping
from enum import IntEnum
from typing import TypeVar, overload

from google.protobuf.descriptor import Descriptor as _Descriptor
from google.protobuf.message import Message as _Message
from pydantic import BaseModel

_ModelT = TypeVar("_ModelT", bound=ProtobufModel)

class ProtobufEnum(IntEnum): ...

class ProtobufModel(BaseModel):
    def _validate_oneofs(self) -> ProtobufModel: ...

MODEL_REGISTRY: Mapping[str, type[ProtobufModel]]
ENUM_REGISTRY: Mapping[str, type[ProtobufEnum]]

@overload
def get_pydantic_model(source: type[_ModelT]) -> type[_ModelT]: ...
@overload
def get_pydantic_model(source: str) -> type[ProtobufModel]: ...
def _get_pydantic_model(
    source: _Descriptor | type[_Message] | _Message,
) -> type[ProtobufModel]: ...
def _model_to_protobuf(model: ProtobufModel) -> _Message: ...
def _protobuf_to_pydantic(value: object) -> object: ...
def _model_from_bytes(
    model_class: type[_ModelT],
    serialized: bytes | bytearray | memoryview,
) -> _ModelT: ...
