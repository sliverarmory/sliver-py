"""Small, idiomatic Pydantic types for common Sliver operations.

These models sit above the generated Pydantic schema.  Conversion methods
return generated Pydantic models; raw protobuf messages remain an internal
transport detail.
"""

from __future__ import annotations

import platform
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .enums import (
    GOARCH,
    GOOS,
    C2Protocol,
    ConnectionStrategy,
    OutputFormat,
    ShellcodeBypass,
    ShellcodeCompression,
    ShellcodeEncoder,
    ShellcodeEntropy,
    ShellcodeExitOption,
    ShellcodeHeaders,
)
from .errors import UnsupportedTargetError
from .models import clientpb, commonpb

_NANOSECONDS_PER_MICROSECOND = 1_000
_MICROSECONDS_PER_SECOND = 1_000_000
_SECONDS_PER_DAY = 86_400
_MAX_INT64 = 9_223_372_036_854_775_807
_MAX_UINT32 = 4_294_967_295

_DEFAULT_C2_PORTS: dict[C2Protocol, int] = {
    C2Protocol.MTLS: 8888,
    C2Protocol.WIREGUARD: 53,
    C2Protocol.TCP_PIVOT: 9898,
}

_SUPPORTED_TARGETS = frozenset(
    {
        (GOOS.DARWIN, GOARCH.AMD64),
        (GOOS.DARWIN, GOARCH.ARM64),
        (GOOS.LINUX, GOARCH.I386),
        (GOOS.LINUX, GOARCH.AMD64),
        (GOOS.LINUX, GOARCH.ARM64),
        (GOOS.WINDOWS, GOARCH.I386),
        (GOOS.WINDOWS, GOARCH.AMD64),
        (GOOS.WINDOWS, GOARCH.ARM64),
    }
)

_SHELLCODE_TARGETS = frozenset(
    {
        (GOOS.WINDOWS, GOARCH.I386),
        (GOOS.WINDOWS, GOARCH.AMD64),
        (GOOS.DARWIN, GOARCH.ARM64),
        (GOOS.LINUX, GOARCH.AMD64),
        (GOOS.LINUX, GOARCH.ARM64),
    }
)


class _DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _duration_nanoseconds(value: timedelta, *, field_name: str) -> int:
    total_microseconds = (
        value.days * _SECONDS_PER_DAY * _MICROSECONDS_PER_SECOND
        + value.seconds * _MICROSECONDS_PER_SECOND
        + value.microseconds
    )
    nanoseconds = total_microseconds * _NANOSECONDS_PER_MICROSECOND
    if nanoseconds < 0:
        raise ValueError(f"{field_name} cannot be negative")
    if nanoseconds > _MAX_INT64:
        raise ValueError(f"{field_name} exceeds Sliver's signed 64-bit duration")
    return nanoseconds


def _host_with_port(host: str, port: int) -> str:
    normalized = host.strip()
    if not normalized:
        raise ValueError("host cannot be empty")
    if any(character in normalized for character in "/?#@"):
        raise ValueError(
            "host must not contain a URL path, query, fragment, or userinfo"
        )
    if normalized.startswith("["):
        if not normalized.endswith("]"):
            raise ValueError("invalid bracketed IPv6 host")
        normalized = normalized[1:-1]
    if ":" in normalized:
        normalized = f"[{normalized}]"
    return f"{normalized}:{port}"


def _query_suffix(query: Mapping[str, str] | None) -> str:
    if query is None:
        return ""
    return f"?{urlencode(query)}" if query else ""


def _normalize_c2_url(protocol: C2Protocol, value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("C2 URL cannot be empty")
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() != protocol.value:
        raise ValueError(
            f"C2 URL scheme {parsed.scheme!r} does not match {protocol.value!r}"
        )
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("C2 URLs cannot contain userinfo")
    if parsed.hostname is None:
        raise ValueError("C2 URL must include a host")
    if parsed.fragment:
        raise ValueError("C2 URLs cannot contain fragments")

    # Accessing ``port`` performs urllib's range and syntax validation.
    port = parsed.port
    if port is None and protocol in _DEFAULT_C2_PORTS:
        port = _DEFAULT_C2_PORTS[protocol]
        netloc = _host_with_port(parsed.hostname, port)
    else:
        netloc = parsed.netloc

    if protocol is C2Protocol.NAMED_PIPE and not parsed.path.startswith("/pipe/"):
        raise ValueError("named-pipe C2 URLs must use a /pipe/<name> path")
    return urlunsplit((protocol.value, netloc, parsed.path, parsed.query, ""))


class Target(_DomainModel):
    """A Sliver compiler target."""

    os: GOOS = Field(validation_alias=AliasChoices("os", "goos"))
    arch: GOARCH = Field(validation_alias=AliasChoices("arch", "goarch"))

    @model_validator(mode="after")
    def _validate_supported_pair(self) -> Target:
        if (self.os, self.arch) not in _SUPPORTED_TARGETS:
            raise ValueError(
                f"Sliver does not support compiler target {self.os}/{self.arch}"
            )
        return self

    @property
    def goos(self) -> GOOS:
        """Compatibility view of :attr:`os` using Go's conventional name."""

        return self.os

    @property
    def goarch(self) -> GOARCH:
        """Compatibility view of :attr:`arch` using Go's conventional name."""

        return self.arch

    @classmethod
    def current(cls) -> Target:
        """Infer a supported Sliver target from the current Python host."""

        system = platform.system().strip().lower()
        machine = platform.machine().strip().lower()
        goos = {
            "darwin": GOOS.DARWIN,
            "linux": GOOS.LINUX,
            "windows": GOOS.WINDOWS,
        }.get(system)
        goarch = {
            "386": GOARCH.I386,
            "aarch64": GOARCH.ARM64,
            "amd64": GOARCH.AMD64,
            "arm64": GOARCH.ARM64,
            "i386": GOARCH.I386,
            "i686": GOARCH.I386,
            "x86": GOARCH.I386,
            "x86_64": GOARCH.AMD64,
        }.get(machine)
        if goos is None or goarch is None:
            raise UnsupportedTargetError(system, machine)
        try:
            return cls(os=goos, arch=goarch)
        except ValueError as exc:
            raise UnsupportedTargetError(system, machine) from exc


class C2Endpoint(_DomainModel):
    """A validated Sliver C2 endpoint with conversion to ``ImplantC2``."""

    protocol: C2Protocol
    url: str
    priority: int | None = Field(default=None, ge=0, le=_MAX_UINT32)
    options: str = ""

    @model_validator(mode="after")
    def _normalize_url(self) -> C2Endpoint:
        object.__setattr__(self, "url", _normalize_c2_url(self.protocol, self.url))
        return self

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        priority: int | None = None,
        options: str = "",
    ) -> C2Endpoint:
        """Build an endpoint by inferring its protocol from a canonical URL."""

        scheme = urlsplit(url.strip()).scheme.lower()
        try:
            protocol = C2Protocol(scheme)
        except ValueError as exc:
            supported = ", ".join(item.value for item in C2Protocol)
            raise ValueError(
                f"unsupported C2 URL scheme {scheme!r}; expected one of: {supported}"
            ) from exc
        return cls(
            protocol=protocol,
            url=url,
            priority=priority,
            options=options,
        )

    @classmethod
    def mtls(
        cls,
        host: str,
        *,
        port: int = 8888,
        priority: int | None = None,
        options: str = "",
    ) -> C2Endpoint:
        """Build an mTLS C2 endpoint."""

        return cls(
            protocol=C2Protocol.MTLS,
            url=f"mtls://{_host_with_port(host, port)}",
            priority=priority,
            options=options,
        )

    @classmethod
    def wireguard(
        cls,
        host: str,
        *,
        port: int = 53,
        priority: int | None = None,
        options: str = "",
    ) -> C2Endpoint:
        """Build a WireGuard C2 endpoint."""

        return cls(
            protocol=C2Protocol.WIREGUARD,
            url=f"wg://{_host_with_port(host, port)}",
            priority=priority,
            options=options,
        )

    @classmethod
    def http(
        cls,
        host: str,
        *,
        port: int = 80,
        priority: int | None = None,
        options: str = "",
        query: Mapping[str, str] | None = None,
    ) -> C2Endpoint:
        """Build an HTTP C2 endpoint."""

        return cls(
            protocol=C2Protocol.HTTP,
            url=f"http://{_host_with_port(host, port)}{_query_suffix(query)}",
            priority=priority,
            options=options,
        )

    @classmethod
    def https(
        cls,
        host: str,
        *,
        port: int = 443,
        priority: int | None = None,
        options: str = "",
        query: Mapping[str, str] | None = None,
    ) -> C2Endpoint:
        """Build an HTTPS C2 endpoint."""

        return cls(
            protocol=C2Protocol.HTTPS,
            url=f"https://{_host_with_port(host, port)}{_query_suffix(query)}",
            priority=priority,
            options=options,
        )

    @classmethod
    def dns(
        cls,
        domain: str,
        *,
        priority: int | None = None,
        options: str = "",
        query: Mapping[str, str] | None = None,
    ) -> C2Endpoint:
        """Build a DNS C2 endpoint."""

        normalized = domain.strip()
        if not normalized or any(character in normalized for character in "/?#@"):
            raise ValueError("domain must be a DNS name without URL components")
        return cls(
            protocol=C2Protocol.DNS,
            url=f"dns://{normalized}{_query_suffix(query)}",
            priority=priority,
            options=options,
        )

    @classmethod
    def named_pipe(
        cls,
        host: str,
        pipe: str,
        *,
        priority: int | None = None,
        options: str = "",
        query: Mapping[str, str] | None = None,
    ) -> C2Endpoint:
        """Build a Windows named-pipe pivot C2 endpoint."""

        normalized_host = host.strip()
        if not normalized_host or any(
            character in normalized_host for character in "/?#@[]:"
        ):
            raise ValueError("named-pipe host must be a hostname or '.'")
        normalized_pipe = pipe.strip().replace("\\", "/").strip("/")
        if normalized_pipe.lower().startswith("pipe/"):
            normalized_pipe = normalized_pipe[5:]
        if not normalized_pipe:
            raise ValueError("pipe cannot be empty")
        encoded_pipe = "/".join(
            quote(component, safe="-._~") for component in normalized_pipe.split("/")
        )
        return cls(
            protocol=C2Protocol.NAMED_PIPE,
            url=(
                f"namedpipe://{normalized_host}/pipe/{encoded_pipe}"
                f"{_query_suffix(query)}"
            ),
            priority=priority,
            options=options,
        )

    @classmethod
    def tcp_pivot(
        cls,
        host: str,
        *,
        port: int = 9898,
        priority: int | None = None,
        options: str = "",
        query: Mapping[str, str] | None = None,
    ) -> C2Endpoint:
        """Build a TCP pivot C2 endpoint."""

        return cls(
            protocol=C2Protocol.TCP_PIVOT,
            url=(f"tcppivot://{_host_with_port(host, port)}{_query_suffix(query)}"),
            priority=priority,
            options=options,
        )

    def to_implant_c2(self, *, default_priority: int = 0) -> clientpb.ImplantC2:
        """Convert to Sliver's generated Pydantic ``ImplantC2`` model."""

        if default_priority < 0 or default_priority > _MAX_UINT32:
            raise ValueError("default_priority must fit in an unsigned 32-bit integer")
        return clientpb.ImplantC2(
            priority=self.priority if self.priority is not None else default_priority,
            url=self.url,
            options=self.options,
        )


class BeaconOptions(_DomainModel):
    """Timing options for Sliver's ``generate beacon`` command."""

    interval: timedelta = timedelta(seconds=60)
    jitter: timedelta = timedelta(seconds=30)

    @field_validator("interval")
    @classmethod
    def _validate_interval(cls, value: timedelta) -> timedelta:
        if value <= timedelta():
            raise ValueError("beacon interval must be greater than zero")
        _duration_nanoseconds(value, field_name="interval")
        return value

    @field_validator("jitter")
    @classmethod
    def _validate_jitter(cls, value: timedelta) -> timedelta:
        _duration_nanoseconds(value, field_name="jitter")
        return value


class ShellcodeOptions(_DomainModel):
    """Numeric shellcode options accepted by Sliver's generation backend."""

    entropy: ShellcodeEntropy = ShellcodeEntropy.NONE
    compression: ShellcodeCompression = ShellcodeCompression.NONE
    exit_option: ShellcodeExitOption = ShellcodeExitOption.EXIT_THREAD
    bypass: ShellcodeBypass = ShellcodeBypass.CONTINUE_ON_FAILURE
    headers: ShellcodeHeaders = ShellcodeHeaders.OVERWRITE
    thread: bool = False
    unicode: bool = False
    original_entry_point: int = Field(default=0, ge=0, le=_MAX_UINT32)

    def _uses_windows_only_options(self) -> bool:
        """Return whether non-portable Donut options differ from their defaults."""

        return (
            self.entropy is not ShellcodeEntropy.NONE
            or self.exit_option is not ShellcodeExitOption.EXIT_THREAD
            or self.bypass is not ShellcodeBypass.CONTINUE_ON_FAILURE
            or self.headers is not ShellcodeHeaders.OVERWRITE
            or self.thread
            or self.unicode
            or self.original_entry_point != 0
        )

    def to_shellcode_config(self) -> clientpb.ShellcodeConfig:
        """Convert to Sliver's generated Pydantic shellcode configuration."""

        return clientpb.ShellcodeConfig(
            entropy=int(self.entropy),
            compress=int(self.compression),
            exit_opt=int(self.exit_option),
            bypass=int(self.bypass),
            headers=int(self.headers),
            thread=self.thread,
            unicode=self.unicode,
            oep=self.original_entry_point,
        )


class ImplantSpec(_DomainModel):
    """Concise inputs for Sliver's ``generate`` command."""

    c2: list[C2Endpoint] = Field(min_length=1)
    target: Target = Field(default_factory=Target.current)
    beacon: BeaconOptions | None = None
    output_format: OutputFormat = OutputFormat.EXECUTABLE
    connection_strategy: ConnectionStrategy = ConnectionStrategy.SEQUENTIAL
    reconnect_interval: timedelta = timedelta(seconds=60)
    poll_timeout: timedelta = timedelta(seconds=360)
    max_connection_errors: int = Field(default=1000, ge=0, le=_MAX_UINT32)
    template_name: str = Field(default="sliver", min_length=1)
    http_c2_profile: str = Field(default="default", min_length=1)
    net_go_enabled: bool = False
    debug: bool = False
    evasion: bool = False
    obfuscate_symbols: bool = True
    canary_domains: list[str] = Field(default_factory=list)
    include_protocols: set[C2Protocol] = Field(default_factory=set)
    run_at_load: bool = False
    exports: list[str] = Field(
        default_factory=lambda: [
            "StartW",
            "VoidFunc",
            "DllInstall",
            "DllRegisterServer",
            "DllUnregisterServer",
        ]
    )
    shellcode: ShellcodeOptions | None = None
    shellcode_encoder: ShellcodeEncoder = ShellcodeEncoder.NONE
    wg_peer_tun_ip: str = ""
    wg_key_exchange_port: int = Field(default=1337, ge=1, le=65535)
    wg_tcp_comms_port: int = Field(default=8888, ge=1, le=65535)
    limit_domain_joined: bool = False
    limit_datetime: str = ""
    limit_hostname: str = ""
    limit_username: str = ""
    limit_file_exists: str = ""
    limit_locale: str = ""

    @field_validator("reconnect_interval", "poll_timeout")
    @classmethod
    def _validate_duration(cls, value: timedelta) -> timedelta:
        _duration_nanoseconds(value, field_name="duration")
        return value

    @field_validator("canary_domains")
    @classmethod
    def _normalize_canary_domains(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            domain = value.strip()
            if not domain:
                raise ValueError("canary domains cannot be empty")
            normalized.append(domain if domain.endswith(".") else f"{domain}.")
        return normalized

    @model_validator(mode="after")
    def _validate_compatible_options(self) -> ImplantSpec:
        protocols = {endpoint.protocol for endpoint in self.c2}
        enabled_protocols = protocols | self.include_protocols
        if (
            C2Protocol.NAMED_PIPE in enabled_protocols
            and self.target.os is not GOOS.WINDOWS
        ):
            raise ValueError("named-pipe C2 is only supported by Windows implants")

        is_shellcode = self.output_format is OutputFormat.SHELLCODE
        if (
            is_shellcode
            and (self.target.os, self.target.arch) not in _SHELLCODE_TARGETS
        ):
            raise ValueError(
                "shellcode output is not supported for "
                f"{self.target.os}/{self.target.arch}"
            )
        if not is_shellcode and self.shellcode is not None:
            raise ValueError("shellcode options require shellcode output format")
        if not is_shellcode and self.shellcode_encoder is not ShellcodeEncoder.NONE:
            raise ValueError("shellcode_encoder requires shellcode output format")
        if (
            is_shellcode
            and self.target.os is not GOOS.WINDOWS
            and self.shellcode is not None
            and self.shellcode._uses_windows_only_options()
        ):
            raise ValueError(
                "macOS and Linux shellcode only support the compression option"
            )
        if self.run_at_load and self.output_format is not OutputFormat.SHARED_LIB:
            raise ValueError("run_at_load requires shared-library output format")
        return self

    def to_implant_config(
        self,
        *,
        base: clientpb.ImplantConfig | None = None,
    ) -> clientpb.ImplantConfig:
        """Convert to Sliver's generated Pydantic ``ImplantConfig`` model.

        ``base`` is useful for advanced generated fields not represented by the
        concise spec.  The fields represented by this model always take
        precedence.
        """

        config = (
            base.model_copy(deep=True) if base is not None else clientpb.ImplantConfig()
        )
        config.is_beacon = self.beacon is not None
        config.beacon_interval = (
            _duration_nanoseconds(self.beacon.interval, field_name="beacon interval")
            if self.beacon is not None
            else 0
        )
        config.beacon_jitter = (
            _duration_nanoseconds(self.beacon.jitter, field_name="beacon jitter")
            if self.beacon is not None
            else 0
        )
        config.goos = self.target.os.value
        config.goarch = self.target.arch.value
        config.debug = self.debug
        config.evasion = self.evasion
        config.obfuscate_symbols = self.obfuscate_symbols
        config.template_name = self.template_name
        config.c2 = [
            endpoint.to_implant_c2(default_priority=index)
            for index, endpoint in enumerate(self.c2)
        ]
        config.connection_strategy = self.connection_strategy.value
        config.reconnect_interval = _duration_nanoseconds(
            self.reconnect_interval,
            field_name="reconnect interval",
        )
        config.poll_timeout = _duration_nanoseconds(
            self.poll_timeout,
            field_name="poll timeout",
        )
        config.max_connection_errors = self.max_connection_errors
        config.canary_domains = list(self.canary_domains)
        config.format = self.output_format
        config.is_shared_lib = self.output_format in {
            OutputFormat.SHARED_LIB,
            OutputFormat.GO_ARCHIVE,
        }
        config.is_service = self.output_format is OutputFormat.SERVICE
        config.is_shellcode = self.output_format is OutputFormat.SHELLCODE
        config.run_at_load = self.run_at_load
        config.exports = list(self.exports)
        if config.is_shellcode:
            shellcode = self.shellcode or ShellcodeOptions()
            if self.target.os is GOOS.WINDOWS:
                config.shellcode_config = shellcode.to_shellcode_config()
            else:
                # This mirrors Sliver's client: macOS and Linux shellcode only
                # consume the compression setting, not Donut's Windows fields.
                config.shellcode_config = clientpb.ShellcodeConfig(
                    compress=int(shellcode.compression)
                )
        else:
            config.shellcode_config = None
        config.shellcode_encoder = self.shellcode_encoder
        config.sgn_enabled = self.shellcode_encoder is ShellcodeEncoder.SHIKATA_GA_NAI
        config.httpc2_config_name = self.http_c2_profile
        config.net_go_enabled = self.net_go_enabled
        config.wg_peer_tun_ip = self.wg_peer_tun_ip
        config.wg_key_exchange_port = self.wg_key_exchange_port
        config.wg_tcp_comms_port = self.wg_tcp_comms_port
        config.limit_domain_joined = self.limit_domain_joined
        config.limit_datetime = self.limit_datetime
        config.limit_hostname = self.limit_hostname
        config.limit_username = self.limit_username
        config.limit_file_exists = self.limit_file_exists
        config.limit_locale = self.limit_locale

        protocols = {endpoint.protocol for endpoint in self.c2}
        protocols.update(self.include_protocols)
        config.include_mtls = C2Protocol.MTLS in protocols
        config.include_http = bool(
            {C2Protocol.HTTP, C2Protocol.HTTPS}.intersection(protocols)
        )
        config.include_wg = C2Protocol.WIREGUARD in protocols
        config.include_dns = C2Protocol.DNS in protocols
        config.include_name_pipe = C2Protocol.NAMED_PIPE in protocols
        config.include_tcp = C2Protocol.TCP_PIVOT in protocols
        return config

    def to_generate_request(
        self,
        *,
        name: str = "",
        base: clientpb.ImplantConfig | None = None,
    ) -> clientpb.GenerateReq:
        """Convert to the Pydantic request consumed by Sliver's ``Generate`` RPC."""

        return clientpb.GenerateReq(
            config=self.to_implant_config(base=base),
            name=name,
        )


class GeneratedImplant(_DomainModel):
    """A validated ``Generate`` result with safe local persistence."""

    file: commonpb.File
    implant_name: str = ""
    implant_build_id: str = ""

    @model_validator(mode="after")
    def _validate_file(self) -> GeneratedImplant:
        if not self.file.data:
            raise ValueError("Sliver's Generate result contains no file data")
        if not self.filename:
            raise ValueError("Sliver's Generate result contains no file name")
        return self

    @property
    def filename(self) -> str:
        """A basename safe to use as the default local file name."""

        candidate = self.file.name.replace("\\", "/").rsplit("/", 1)[-1]
        if candidate in {"", ".", ".."}:
            candidate = self.implant_name.replace("\\", "/").rsplit("/", 1)[-1]
        return "" if candidate in {"", ".", ".."} else candidate

    @classmethod
    def from_generate(cls, result: clientpb.Generate) -> GeneratedImplant:
        """Create a rich result from Sliver's generated Pydantic response."""

        if result.file is None:
            raise ValueError("Sliver's Generate result contains no file")
        return cls(
            file=result.file.model_copy(deep=True),
            implant_name=result.implant_name,
            implant_build_id=result.implant_build_id,
        )

    def to_generate(self) -> clientpb.Generate:
        """Convert back to Sliver's generated Pydantic ``Generate`` model."""

        return clientpb.Generate(
            file=self.file.model_copy(deep=True),
            implant_name=self.implant_name,
            implant_build_id=self.implant_build_id,
        )

    def save(
        self,
        destination: str | Path | None = None,
        *,
        overwrite: bool = False,
        mode: int | None = 0o700,
        create_parents: bool = True,
    ) -> Path:
        """Write the generated implant and return its resolved destination.

        Files are created exclusively by default.  Passing an existing
        directory appends :attr:`filename`; passing a file path uses it as-is.
        """

        if mode is not None and (mode < 0 or mode > 0o7777):
            raise ValueError("mode must be between 0 and 0o7777")
        path = Path(self.filename) if destination is None else Path(destination)
        path = path.expanduser()
        if path.is_dir():
            path /= self.filename
        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb" if overwrite else "xb") as output:
            output.write(self.file.data)
        if mode is not None:
            path.chmod(mode)
        return path


class Inventory(_DomainModel):
    """A typed snapshot assembled from Sliver's inventory commands."""

    version: clientpb.Version
    sessions: list[clientpb.Session] = Field(default_factory=list)
    beacons: list[clientpb.Beacon] = Field(default_factory=list)
    jobs: list[clientpb.Job] = Field(default_factory=list)
    operators: list[clientpb.Operator] = Field(default_factory=list)


__all__ = [
    "BeaconOptions",
    "C2Endpoint",
    "GeneratedImplant",
    "ImplantSpec",
    "Inventory",
    "ShellcodeOptions",
    "Target",
]
