"""Typed constants used by the handwritten Sliver API.

The protobuf schema already defines several enums.  Those types are re-exported
here so the Python API has one discoverable enum surface without creating
look-alike values that cannot be passed to generated Pydantic models.
"""

from __future__ import annotations

from enum import Enum, IntEnum

from .models.clientpb import FileType, OutputFormat, ShellcodeEncoder, StageProtocol
from .models.sliverpb import ImplantCapability, PivotType, RegistryType


class _StringEnum(str, Enum):
    """Python 3.10-compatible equivalent of :class:`enum.StrEnum`."""

    def __str__(self) -> str:
        return self.value


class GOOS(_StringEnum):
    """Operating systems supported by Sliver's implant compiler."""

    DARWIN = "darwin"
    LINUX = "linux"
    WINDOWS = "windows"


class GOARCH(_StringEnum):
    """CPU architectures supported by Sliver's implant compiler."""

    I386 = "386"
    AMD64 = "amd64"
    ARM64 = "arm64"


class ConnectionStrategy(_StringEnum):
    """How an implant selects its next configured C2 endpoint."""

    RANDOM = "r"
    RANDOM_DOMAIN = "rd"
    SEQUENTIAL = "s"


class C2Protocol(_StringEnum):
    """Schemes accepted in an implant C2 URL."""

    MTLS = "mtls"
    WIREGUARD = "wg"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    NAMED_PIPE = "namedpipe"
    TCP_PIVOT = "tcppivot"


class TargetKind(_StringEnum):
    """Kinds of interactive Sliver targets."""

    SESSION = "session"
    BEACON = "beacon"


class EventType(_StringEnum):
    """Event names published by Sliver's event stream."""

    UPDATE = "update"
    VERSION = "version"
    EVENT = "event"
    SERVER_ERROR = "server-error"
    SESSION_CONNECTED = "session-connected"
    SESSION_DISCONNECTED = "session-disconnected"
    SESSION_UPDATED = "session-updated"
    CLIENT_JOINED = "client-joined"
    CLIENT_LEFT = "client-left"
    CANARY = "canary"
    WATCHTOWER = "watchtower"
    JOB_STARTED = "job-started"
    JOB_STOPPED = "job-stopped"
    BUILD = "build"
    BUILD_COMPLETED = "build-completed"
    PROFILE = "profile"
    WEBSITE = "website"
    LOOT_ADDED = "loot-added"
    LOOT_REMOVED = "loot-removed"
    BEACON_REGISTERED = "beacon-registered"
    BEACON_TASK_RESULT = "beacon-taskresult"
    EXTERNAL_BUILD = "external-build"
    EXTERNAL_ACKNOWLEDGE = "external-acknowledge"
    EXTERNAL_BUILD_FAILED = "external-build-failed"
    EXTERNAL_BUILD_COMPLETED = "external-build-completed"
    TRAFFIC_ENCODER_TEST_PROGRESS = "traffic-encoder-test-progress"
    CRACKSTATION_CONNECTED = "crackstation-connected"
    CRACKSTATION_DISCONNECTED = "crackstation-disconnected"
    CRACK_BENCHMARK = "crack-benchmark"
    CRACK_STATUS = "crack-status"
    WIREGUARD_NEW_PEER = "wireguard-newpeer"
    MULTIPLAYER_WIREGUARD_NEW_PEER = "multiplayer-wireguard-newpeer"
    MULTIPLAYER_WIREGUARD_REMOVED = "multiplayer-wireguard-removed"
    AI_CONVERSATION = "ai-conversation"
    CLIENT_TOAST = "client-toast"


class RegistryHive(_StringEnum):
    """Windows registry hives accepted by Sliver registry commands."""

    CLASSES_ROOT = "HKCR"
    CURRENT_USER = "HKCU"
    LOCAL_MACHINE = "HKLM"
    PERFORMANCE_DATA = "HKPD"
    USERS = "HKU"
    CURRENT_CONFIG = "HKCC"


class BeaconTaskState(_StringEnum):
    """Server-side lifecycle states for an asynchronous beacon task."""

    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    CANCELED = "canceled"


class JobProtocol(_StringEnum):
    """Network protocol reported for a Sliver listener job."""

    TCP = "tcp"
    UDP = "udp"


class PortForwardProtocol(IntEnum):
    """Wire values used by Sliver's port-forward requests."""

    UNSPECIFIED = 0
    TCP = 1
    UDP = 2


class LogonType(IntEnum):
    """Windows logon types accepted by Sliver's ``make-token`` command."""

    UNSPECIFIED = 0
    INTERACTIVE = 2
    NETWORK = 3
    BATCH = 4
    SERVICE = 5
    UNLOCK = 7
    NETWORK_CLEARTEXT = 8
    NEW_CREDENTIALS = 9


class ShellcodeEntropy(IntEnum):
    """Donut entropy modes exposed by Sliver shellcode generation."""

    UNSPECIFIED = 0
    NONE = 1
    RANDOM_NAMES = 2
    RANDOM_NAMES_AND_ENCRYPTION = 3


class ShellcodeCompression(IntEnum):
    """Compression choices exposed by Sliver's shellcode configuration."""

    UNSPECIFIED = 0
    NONE = 1
    APLIB = 2


class ShellcodeExitOption(IntEnum):
    """Behavior after a Donut payload finishes execution."""

    UNSPECIFIED = 0
    EXIT_THREAD = 1
    EXIT_PROCESS = 2
    BLOCK = 3


class ShellcodeBypass(IntEnum):
    """Behavior when Donut's AMSI/WLDP bypass fails."""

    UNSPECIFIED = 0
    NONE = 1
    ABORT_ON_FAILURE = 2
    CONTINUE_ON_FAILURE = 3


class ShellcodeHeaders(IntEnum):
    """How Donut treats PE headers after loading a payload."""

    UNSPECIFIED = 0
    OVERWRITE = 1
    KEEP = 2


__all__ = [
    "BeaconTaskState",
    "C2Protocol",
    "ConnectionStrategy",
    "EventType",
    "FileType",
    "GOARCH",
    "GOOS",
    "ImplantCapability",
    "JobProtocol",
    "LogonType",
    "OutputFormat",
    "PivotType",
    "PortForwardProtocol",
    "RegistryHive",
    "RegistryType",
    "ShellcodeBypass",
    "ShellcodeCompression",
    "ShellcodeEncoder",
    "ShellcodeEntropy",
    "ShellcodeExitOption",
    "ShellcodeHeaders",
    "StageProtocol",
    "TargetKind",
]
