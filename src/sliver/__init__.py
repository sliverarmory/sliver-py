"""Public API for the Sliver Python client."""

from importlib.metadata import PackageNotFoundError, version

from . import models
from .beacon import InteractiveBeacon
from .client import SliverClient
from .config import SliverClientConfig, SliverWireGuardConfig
from .models import (
    ProtobufEnum,
    ProtobufModel,
    get_pydantic_model,
    protobuf_to_pydantic,
    pydantic_to_protobuf,
)
from .protobuf import client_pb2, common_pb2, sliver_pb2
from .session import InteractiveSession

try:
    __version__ = version("sliver-py")
except PackageNotFoundError:  # pragma: no cover - source tree without installation
    __version__ = "0.1.0"

__all__ = [
    "InteractiveBeacon",
    "InteractiveSession",
    "ProtobufEnum",
    "ProtobufModel",
    "SliverClient",
    "SliverClientConfig",
    "SliverWireGuardConfig",
    "client_pb2",
    "common_pb2",
    "get_pydantic_model",
    "models",
    "protobuf_to_pydantic",
    "pydantic_to_protobuf",
    "sliver_pb2",
]
