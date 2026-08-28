"""Concrete Pydantic classes generated from the pinned Sliver API."""

from __future__ import annotations

from . import clientpb, commonpb, sliverpb
from ._runtime import (
    ENUM_REGISTRY,
    MODEL_REGISTRY,
    ProtobufEnum,
    ProtobufModel,
    _bind_wire_types,
    _rebuild_models,
    _register_package,
    get_pydantic_model,
)
from ._runtime import (
    _get_pydantic_model as _get_pydantic_model,
)
from ._runtime import (
    _model_from_bytes as _model_from_bytes,
)
from ._runtime import (
    _model_to_protobuf as _model_to_protobuf,
)
from ._runtime import (
    _protobuf_to_pydantic as _protobuf_to_pydantic,
)

_register_package("commonpb", commonpb)
_register_package("sliverpb", sliverpb)
_register_package("clientpb", clientpb)
_bind_wire_types()
_rebuild_models()

__all__ = [
    "ENUM_REGISTRY",
    "MODEL_REGISTRY",
    "ProtobufEnum",
    "ProtobufModel",
    "clientpb",
    "commonpb",
    "get_pydantic_model",
    "sliverpb",
]
