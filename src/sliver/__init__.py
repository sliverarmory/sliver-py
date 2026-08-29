"""Public API for the Sliver Python client."""

from importlib.metadata import PackageNotFoundError, version

from . import models
from .beacon import InteractiveBeacon
from .client import Client, SliverClient
from .config import OperatorConfig, SliverClientConfig, SliverWireGuardConfig
from .domain import (
    BeaconOptions,
    C2Endpoint,
    GeneratedImplant,
    ImplantSpec,
    Inventory,
    ShellcodeOptions,
    Target,
)
from .enums import (
    GOARCH,
    GOOS,
    BeaconTaskState,
    C2Protocol,
    ConnectionStrategy,
    EventType,
    FileType,
    ImplantCapability,
    JobProtocol,
    LogonType,
    OutputFormat,
    PivotType,
    PortForwardProtocol,
    RegistryHive,
    RegistryType,
    ShellcodeBypass,
    ShellcodeCompression,
    ShellcodeEncoder,
    ShellcodeEntropy,
    ShellcodeExitOption,
    ShellcodeHeaders,
    StageProtocol,
    TargetKind,
)
from .errors import (
    CleanupError,
    CommandError,
    NotConnectedError,
    ResourceNotFoundError,
    RPCError,
    SliverError,
    SliverTimeoutError,
    UnsupportedTargetError,
)
from .models import (
    ProtobufEnum,
    ProtobufModel,
    get_pydantic_model,
)
from .session import InteractiveSession

try:
    __version__ = version("sliver-py")
except PackageNotFoundError:  # pragma: no cover - source tree without installation
    __version__ = "0.1.0"

__all__ = [
    "BeaconOptions",
    "BeaconTaskState",
    "C2Endpoint",
    "C2Protocol",
    "Client",
    "CleanupError",
    "CommandError",
    "ConnectionStrategy",
    "EventType",
    "FileType",
    "GOARCH",
    "GOOS",
    "GeneratedImplant",
    "ImplantCapability",
    "ImplantSpec",
    "InteractiveBeacon",
    "InteractiveSession",
    "Inventory",
    "JobProtocol",
    "LogonType",
    "NotConnectedError",
    "OperatorConfig",
    "OutputFormat",
    "PivotType",
    "PortForwardProtocol",
    "ProtobufEnum",
    "ProtobufModel",
    "RPCError",
    "RegistryHive",
    "RegistryType",
    "ResourceNotFoundError",
    "ShellcodeBypass",
    "ShellcodeCompression",
    "ShellcodeEncoder",
    "ShellcodeEntropy",
    "ShellcodeExitOption",
    "ShellcodeHeaders",
    "ShellcodeOptions",
    "SliverClient",
    "SliverClientConfig",
    "SliverError",
    "SliverTimeoutError",
    "SliverWireGuardConfig",
    "StageProtocol",
    "Target",
    "TargetKind",
    "UnsupportedTargetError",
    "get_pydantic_model",
    "models",
]
