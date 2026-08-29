"""Reusable, isolated Sliver end-to-end test harness.

The GitHub Actions workflow is responsible for checking out the pinned Sliver
submodule, downloading its build assets, and compiling ``sliver-server``. This
module only manages the resulting native server and implant processes.

All construction and startup paths are deliberately gated on ``SLIVER_E2E=1``
because the harness executes generated Sliver implants on the current host.
"""

from __future__ import annotations

import asyncio
import contextlib
import ctypes
import errno
import inspect
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
from collections.abc import Awaitable, Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from sliver import Client, SliverClientConfig, models

LOOPBACK_HOST = "127.0.0.1"
E2E_GATE_ENV = "SLIVER_E2E"
PORT_BIND_ATTEMPTS = 3

_SUPPORTED_TARGETS = {
    ("darwin", "arm64"),
    ("linux", "amd64"),
    ("windows", "amd64"),
}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [^-\r\n]*PRIVATE KEY-----.*?"
    r"-----END [^-\r\n]*PRIVATE KEY-----",
    re.DOTALL,
)
_SENSITIVE_FIELD = re.compile(
    r'(?i)("?(?:token|private_key|client_private_key)"?\s*[:=]\s*)'
    r'("(?:[^"\\]|\\.)*"|\S+)',
)
_BIND_CONFLICT = re.compile(
    r"(?i)(?:address already in use|eaddrinuse|wsaeaddrinuse|"
    r"only one usage of each socket address)"
)

_ResultT = TypeVar("_ResultT")


class E2EHarnessError(RuntimeError):
    """A sanitized end-to-end harness failure."""


class E2EDisabledError(E2EHarnessError):
    """Raised when native E2E execution has not been explicitly enabled."""


def _require_e2e_enabled() -> None:
    if os.environ.get(E2E_GATE_ENV) != "1":
        raise E2EDisabledError("native Sliver E2E execution requires SLIVER_E2E=1")


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _resolve_path(value: str | os.PathLike[str], base: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _positive_float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        raise E2EHarnessError(f"{name} must be a number") from None
    if parsed <= 0:
        raise E2EHarnessError(f"{name} must be greater than zero")
    return parsed


def _positive_int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        raise E2EHarnessError(f"{name} must be an integer") from None
    if parsed <= 0:
        raise E2EHarnessError(f"{name} must be greater than zero")
    return parsed


def _runtime_target() -> tuple[str, str]:
    if sys.platform == "darwin":
        target_os = "darwin"
    elif sys.platform.startswith("linux"):
        target_os = "linux"
    elif sys.platform == "win32":
        target_os = "windows"
    else:
        raise E2EHarnessError(f"unsupported E2E host operating system {sys.platform!r}")

    machine = platform.machine().strip().lower()
    if machine in {"amd64", "x86_64", "x64"}:
        target_arch = "amd64"
    elif machine in {"arm64", "aarch64"}:
        target_arch = "arm64"
    elif machine in {"386", "i386", "i686", "x86"}:
        target_arch = "386"
    else:
        raise E2EHarnessError(f"unsupported E2E host architecture {machine!r}")
    return target_os, target_arch


@dataclass(frozen=True, slots=True)
class E2ESettings:
    """Validated paths and native target settings loaded from the environment."""

    repo_root: Path
    sliver_root: Path
    server_path: Path
    results_root: Path
    work_root: Path
    target_os: str
    target_arch: str
    startup_timeout: float = 600.0
    connect_timeout: float = 300.0
    operator_timeout: float = 120.0
    process_grace_timeout: float = 2.0
    process_kill_timeout: float = 10.0
    log_tail_bytes: int = 64 * 1024

    def __post_init__(self) -> None:
        _require_e2e_enabled()

        for field_name in (
            "repo_root",
            "sliver_root",
            "server_path",
            "results_root",
            "work_root",
        ):
            path = Path(getattr(self, field_name)).expanduser().resolve()
            object.__setattr__(self, field_name, path)

        object.__setattr__(self, "target_os", self.target_os.strip().lower())
        object.__setattr__(self, "target_arch", self.target_arch.strip().lower())
        self._validate()

    @classmethod
    def from_env(cls) -> E2ESettings:
        """Load the workflow contract from environment variables.

        Canonical variables are ``SLIVER_E2E_REPO_ROOT``,
        ``SLIVER_E2E_SLIVER_ROOT``, ``SLIVER_E2E_SERVER``,
        ``SLIVER_E2E_RESULTS_ROOT``, ``SLIVER_E2E_WORK_ROOT``,
        ``SLIVER_E2E_TARGET_OS``, and ``SLIVER_E2E_TARGET_ARCH``.
        A few older spelling aliases remain accepted to keep local invocations
        straightforward.
        """

        _require_e2e_enabled()
        default_repo = Path(__file__).resolve().parents[2]
        repo_value = _first_env("SLIVER_E2E_REPO_ROOT", "SLIVER_E2E_REPO")
        repo_root = _resolve_path(repo_value or default_repo, Path.cwd())

        sliver_value = _first_env("SLIVER_E2E_SLIVER_ROOT")
        sliver_root = _resolve_path(sliver_value or "sliver", repo_root)

        runtime_os, runtime_arch = _runtime_target()
        target_os = _first_env("SLIVER_E2E_TARGET_OS", "SLIVER_E2E_GOOS") or runtime_os
        target_arch = (
            _first_env("SLIVER_E2E_TARGET_ARCH", "SLIVER_E2E_GOARCH") or runtime_arch
        )
        target_os = target_os.strip().lower()
        target_arch = target_arch.strip().lower()

        server_value = _first_env("SLIVER_E2E_SERVER", "SLIVER_SERVER_PATH")
        server_name = "sliver-server.exe" if target_os == "windows" else "sliver-server"
        server_path = _resolve_path(server_value or server_name, sliver_root)

        results_value = _first_env("SLIVER_E2E_RESULTS_ROOT", "SLIVER_E2E_ARTIFACT_DIR")
        results_root = _resolve_path(results_value or "e2e-results", repo_root)

        work_value = _first_env("SLIVER_E2E_WORK_ROOT", "SLIVER_E2E_WORK")
        default_work = (
            Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "sliver-py-e2e"
        )
        work_root = _resolve_path(work_value or default_work, repo_root)

        return cls(
            repo_root=repo_root,
            sliver_root=sliver_root,
            server_path=server_path,
            results_root=results_root,
            work_root=work_root,
            target_os=target_os,
            target_arch=target_arch,
            startup_timeout=_positive_float_env("SLIVER_E2E_STARTUP_TIMEOUT", 600.0),
            connect_timeout=_positive_float_env("SLIVER_E2E_CONNECT_TIMEOUT", 300.0),
            operator_timeout=_positive_float_env("SLIVER_E2E_OPERATOR_TIMEOUT", 120.0),
            process_grace_timeout=_positive_float_env(
                "SLIVER_E2E_PROCESS_GRACE_TIMEOUT", 2.0
            ),
            process_kill_timeout=_positive_float_env(
                "SLIVER_E2E_PROCESS_KILL_TIMEOUT", 10.0
            ),
            log_tail_bytes=_positive_int_env("SLIVER_E2E_LOG_TAIL_BYTES", 64 * 1024),
        )

    def _validate(self) -> None:
        runtime_target = _runtime_target()
        target = (self.target_os, self.target_arch)
        if target not in _SUPPORTED_TARGETS:
            supported = ", ".join(
                f"{os_name}/{arch}" for os_name, arch in sorted(_SUPPORTED_TARGETS)
            )
            raise E2EHarnessError(
                f"unsupported E2E target {self.target_os}/{self.target_arch}; "
                f"expected one of {supported}"
            )
        if target != runtime_target:
            raise E2EHarnessError(
                "native E2E target must match the current runner: "
                f"target is {self.target_os}/{self.target_arch}, "
                f"runner is {runtime_target[0]}/{runtime_target[1]}"
            )
        if (
            not self.repo_root.is_dir()
            or not (self.repo_root / "pyproject.toml").is_file()
        ):
            raise E2EHarnessError("SLIVER_E2E_REPO_ROOT is not a sliver-py checkout")
        if not self.sliver_root.is_dir() or not (self.sliver_root / "go.mod").is_file():
            raise E2EHarnessError("SLIVER_E2E_SLIVER_ROOT is not a Sliver checkout")
        if not self.server_path.is_file():
            raise E2EHarnessError(
                "compiled Sliver server is missing; the workflow must build it first"
            )
        if os.name != "nt" and not os.access(self.server_path, os.X_OK):
            raise E2EHarnessError("compiled Sliver server is not executable")
        for name in (
            "startup_timeout",
            "connect_timeout",
            "operator_timeout",
            "process_grace_timeout",
            "process_kill_timeout",
        ):
            if getattr(self, name) <= 0:
                raise E2EHarnessError(f"{name} must be greater than zero")
        if self.log_tail_bytes <= 0:
            raise E2EHarnessError("log_tail_bytes must be greater than zero")
        if (
            self.work_root == self.results_root
            or self.work_root.is_relative_to(self.results_root)
            or self.results_root.is_relative_to(self.work_root)
        ):
            raise E2EHarnessError(
                "private E2E work and artifact result roots must be disjoint"
            )


def _mkdir_private(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)


def _redact_text(text: str, redactions: Sequence[str] = ()) -> str:
    result = _PRIVATE_KEY.sub("[REDACTED PRIVATE KEY]", text)
    result = _SENSITIVE_FIELD.sub(r"\1[REDACTED]", result)
    for secret in redactions:
        if secret:
            result = result.replace(secret, "[REDACTED]")
    return result


def read_log_tail(
    path: str | os.PathLike[str],
    *,
    max_bytes: int = 64 * 1024,
    redactions: Sequence[str] = (),
) -> str:
    """Read and sanitize the final ``max_bytes`` of a process log."""

    log_path = Path(path)
    if max_bytes <= 0:
        return "(log tail disabled)"
    try:
        with log_path.open("rb") as log_file:
            log_file.seek(0, os.SEEK_END)
            size = log_file.tell()
            log_file.seek(max(0, size - max_bytes), os.SEEK_SET)
            data = log_file.read(max_bytes)
    except OSError:
        return "(log unavailable)"
    text = data.decode("utf-8", errors="replace").strip()
    return _redact_text(text, redactions) if text else "(log empty)"


def _open_private_log(path: Path):
    _mkdir_private(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    return os.fdopen(descriptor, "wb", buffering=0)


def _close_windows_handle(handle: int | None) -> None:
    if os.name != "nt" or not handle:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    kernel32.CloseHandle(ctypes.c_void_p(handle))


def _create_windows_kill_job(pid: int) -> int | None:
    """Attach one exact process to a kill-on-close Windows Job Object."""

    if os.name != "nt":
        return None

    from ctypes import wintypes

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")

    try:
        info = ExtendedLimitInformation()
        info.BasicLimitInformation.LimitFlags = 0x00002000
        configured = kernel32.SetInformationJobObject(
            job,
            9,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not configured:
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject failed")

        process_handle = kernel32.OpenProcess(0x0100 | 0x0001, False, pid)
        if not process_handle:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")
        try:
            if not kernel32.AssignProcessToJobObject(job, process_handle):
                raise OSError(
                    ctypes.get_last_error(), "AssignProcessToJobObject failed"
                )
        finally:
            _close_windows_handle(int(process_handle))
    except Exception:
        _close_windows_handle(int(job))
        raise
    return int(job)


def _terminate_windows_job(handle: int | None) -> None:
    if os.name != "nt" or not handle:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel32.TerminateJobObject.restype = ctypes.c_int
    kernel32.TerminateJobObject(ctypes.c_void_p(handle), 1)


def _taskkill(pid: int, *, force: bool, timeout: float) -> None:
    if os.name != "nt":
        return
    command = ["taskkill.exe", "/PID", str(pid), "/T"]
    if force:
        command.append("/F")
    with contextlib.suppress(OSError, subprocess.TimeoutExpired):
        subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=max(timeout, 0.1),
        )


@dataclass(eq=False, slots=True)
class ManagedProcess:
    """A native child contained for deterministic process-tree cleanup."""

    label: str
    process: subprocess.Popen[bytes]
    log_path: Path
    _windows_job: int | None = field(default=None, repr=False)
    _stopped: bool = field(default=False, init=False, repr=False)
    _stop_lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False
    )

    @classmethod
    def launch(
        cls,
        executable: str | os.PathLike[str],
        args: Sequence[str] = (),
        *,
        cwd: str | os.PathLike[str],
        env: Mapping[str, str],
        log_path: str | os.PathLike[str],
        label: str,
    ) -> ManagedProcess:
        safe_label = label if _SAFE_NAME.fullmatch(label) else "managed-process"
        output_path = Path(log_path).resolve()
        log_file = _open_private_log(output_path)
        creationflags = 0
        start_new_session = os.name != "nt"
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        try:
            process = subprocess.Popen(
                [str(executable), *args],
                cwd=Path(cwd),
                env=dict(env),
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=start_new_session,
                creationflags=creationflags,
            )
        except (OSError, ValueError):
            raise E2EHarnessError(f"failed to start {safe_label}") from None
        finally:
            log_file.close()

        windows_job = None
        if os.name == "nt":
            try:
                windows_job = _create_windows_kill_job(process.pid)
            except OSError:
                _taskkill(process.pid, force=True, timeout=5.0)
                with contextlib.suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=5.0)
                raise E2EHarnessError(
                    f"failed to contain {safe_label} process tree"
                ) from None

        return cls(
            label=safe_label,
            process=process,
            log_path=output_path,
            _windows_job=windows_job,
        )

    @property
    def pid(self) -> int:
        return self.process.pid

    @property
    def returncode(self) -> int | None:
        return self.process.poll()

    @property
    def running(self) -> bool:
        return self.returncode is None

    def wait(self, timeout: float | None = None) -> int:
        try:
            return self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise E2EHarnessError(f"timed out waiting for {self.label}") from None

    async def await_exit(self, timeout: float | None = None) -> int:
        return await asyncio.to_thread(self.wait, timeout)

    def diagnostics(
        self,
        *,
        redactions: Sequence[str] = (),
        max_bytes: int = 64 * 1024,
    ) -> str:
        status = (
            "still running"
            if self.returncode is None
            else f"exited with status {self.returncode}"
        )
        tail = read_log_tail(
            self.log_path,
            max_bytes=max_bytes,
            redactions=redactions,
        )
        return f"{self.label} {status}\nlog tail:\n{tail}"

    def stop(
        self,
        grace_timeout: float = 2.0,
        kill_timeout: float = 10.0,
    ) -> None:
        """Stop this exact process tree; repeated calls are safe."""

        with self._stop_lock:
            if self._stopped:
                return
            try:
                if os.name == "nt":
                    self._stop_windows(grace_timeout, kill_timeout)
                else:
                    self._stop_unix(grace_timeout, kill_timeout)
            except Exception:
                # Preserve the containment handle and allow teardown to retry.
                raise
            else:
                if os.name == "nt":
                    _close_windows_handle(self._windows_job)
                    self._windows_job = None
                self._stopped = True

    async def astop(
        self,
        grace_timeout: float = 2.0,
        kill_timeout: float = 10.0,
    ) -> None:
        await asyncio.to_thread(self.stop, grace_timeout, kill_timeout)

    def _stop_unix(self, grace_timeout: float, kill_timeout: float) -> None:
        if self.returncode is None:
            self._signal_process_group(signal.SIGTERM)
            try:
                self.process.wait(timeout=grace_timeout)
            except subprocess.TimeoutExpired:
                self._signal_process_group(signal.SIGKILL)
                try:
                    self.process.wait(timeout=kill_timeout)
                except subprocess.TimeoutExpired:
                    raise E2EHarnessError(
                        f"{self.label} remained alive after forced termination"
                    ) from None

        # The leader may exit while a compiler or helper remains in its group.
        self._signal_process_group(signal.SIGKILL)

    def _signal_process_group(self, process_signal: signal.Signals) -> None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(self.pid, process_signal)

    def _stop_windows(self, grace_timeout: float, kill_timeout: float) -> None:
        if self.returncode is None:
            _taskkill(self.pid, force=False, timeout=grace_timeout)
            try:
                self.process.wait(timeout=grace_timeout)
            except subprocess.TimeoutExpired:
                if self._windows_job:
                    _terminate_windows_job(self._windows_job)
                else:
                    _taskkill(self.pid, force=True, timeout=kill_timeout)
                try:
                    self.process.wait(timeout=kill_timeout)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    try:
                        self.process.wait(timeout=kill_timeout)
                    except subprocess.TimeoutExpired:
                        raise E2EHarnessError(
                            f"{self.label} remained alive after forced termination"
                        ) from None


def is_bind_conflict(error: BaseException) -> bool:
    """Return whether an exception chain explicitly reports a port collision."""

    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, OSError) and current.errno in {
            errno.EADDRINUSE,
            10048,  # WSAEADDRINUSE
        }:
            return True
        if _BIND_CONFLICT.search(str(current)):
            return True
        if current.__cause__ is not None:
            current = current.__cause__
        elif not current.__suppress_context__:
            current = current.__context__
        else:
            current = None
    return False


def free_loopback_port(*, exclude: Collection[int] = ()) -> int:
    """Reserve and release an ephemeral IPv4 loopback TCP port."""

    excluded = set(exclude)
    for _ in range(32):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind((LOOPBACK_HOST, 0))
            listener.listen(1)
            port = int(listener.getsockname()[1])
        # Sliver treats 65535 as invalid even though the OS can allocate it.
        if port < 65535 and port not in excluded:
            return port
    raise E2EHarnessError("could not allocate a Sliver-compatible loopback port")


async def retry_bind_conflicts(
    operation: Callable[[int], Awaitable[_ResultT]],
    *,
    reset: Callable[[], Awaitable[None]] | None = None,
    attempts: int = PORT_BIND_ATTEMPTS,
) -> _ResultT:
    """Retry an entire loopback operation only after an evidenced bind conflict."""

    if attempts <= 0:
        raise ValueError("attempts must be greater than zero")

    attempted_ports: set[int] = set()
    for attempt in range(attempts):
        port = free_loopback_port(exclude=attempted_ports)
        attempted_ports.add(port)
        try:
            return await operation(port)
        except Exception as error:
            if attempt + 1 >= attempts or not is_bind_conflict(error):
                raise
            if reset is not None:
                try:
                    await reset()
                except Exception as cleanup_error:
                    raise E2EHarnessError(
                        "failed to clean up an address-in-use retry attempt"
                    ) from cleanup_error

    raise AssertionError("bind-conflict retry loop did not return or raise")


def isolated_server_env(
    *,
    server_root: Path,
    client_root: Path,
    home_root: Path,
    temp_root: Path,
    host_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return Sliver's host environment with every state root isolated."""

    environment = dict(os.environ if host_env is None else host_env)
    environment.update(
        {
            "HOME": str(home_root),
            "USERPROFILE": str(home_root),
            "TMP": str(temp_root),
            "TEMP": str(temp_root),
            "TMPDIR": str(temp_root),
            "SLIVER_CLIENT_ROOT_DIR": str(client_root),
            "SLIVER_ROOT_DIR": str(server_root),
        }
    )
    return environment


def sanitized_implant_env(
    *,
    home_root: Path,
    temp_root: Path,
    marker: str,
    host_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build a minimal implant environment without host credentials or proxies."""

    if not marker or "\x00" in marker:
        raise E2EHarnessError("implant marker must be nonempty")
    source = os.environ if host_env is None else host_env
    allowed = {
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "WINDIR",
    }
    environment: dict[str, str] = {}
    for name, value in source.items():
        upper_name = name.upper()
        if upper_name in allowed:
            environment[upper_name] = value
    environment.update(
        {
            "HOME": str(home_root),
            "USERPROFILE": str(home_root),
            "TMP": str(temp_root),
            "TEMP": str(temp_root),
            "TMPDIR": str(temp_root),
            "SLIVER_E2E_PARENT_MARKER": marker,
            "SLIVER_E2E_MARKER": marker,
        }
    )
    return dict(sorted(environment.items()))


def launch_managed_implant(
    executable: str | os.PathLike[str],
    *,
    work_dir: str | os.PathLike[str],
    log_path: str | os.PathLike[str],
    marker: str,
    args: Sequence[str] = (),
    host_env: Mapping[str, str] | None = None,
) -> ManagedProcess:
    """Launch one implant with an allowlisted environment and managed tree."""

    _require_e2e_enabled()
    executable_path = Path(executable).expanduser().resolve()
    if not executable_path.is_file():
        raise E2EHarnessError("generated implant executable is missing")
    if os.name != "nt" and not os.access(executable_path, os.X_OK):
        raise E2EHarnessError("generated implant is not executable")

    process_root = Path(work_dir).expanduser().resolve()
    home_root = process_root / "home"
    temp_root = process_root / "tmp"
    for directory in (process_root, home_root, temp_root):
        _mkdir_private(directory)
    environment = sanitized_implant_env(
        home_root=home_root,
        temp_root=temp_root,
        marker=marker,
        host_env=host_env,
    )
    return ManagedProcess.launch(
        executable_path,
        args,
        cwd=process_root,
        env=environment,
        log_path=log_path,
        label=marker,
    )


class SliverServerHarness:
    """Own one isolated Sliver server, operator, client, and implant set."""

    operator_name = "sliverpy-e2e"

    def __init__(self, settings: E2ESettings, *, scenario: str = "suite"):
        _require_e2e_enabled()
        if not _SAFE_NAME.fullmatch(scenario):
            raise E2EHarnessError("E2E scenario name contains unsafe characters")
        self.settings = settings
        self.scenario = scenario
        _mkdir_private(settings.results_root)
        _mkdir_private(settings.work_root)
        self.run_root = Path(
            tempfile.mkdtemp(prefix="run-", dir=settings.work_root)
        ).resolve()
        if os.name != "nt":
            self.run_root.chmod(0o700)

        self.server_state_root = self.run_root / "server"
        self.client_state_root = self.run_root / "client"
        self.home_root = self.run_root / "home"
        self.temp_root = self.run_root / "tmp"
        self.implant_root = self.run_root / "implants"
        self.log_root = self.run_root / "logs"
        for directory in (
            self.server_state_root,
            self.client_state_root,
            self.home_root,
            self.temp_root,
            self.implant_root,
            self.log_root,
        ):
            _mkdir_private(directory)

        self.operator_config_path = self.run_root / "operator.cfg"
        self.server_log_path = self.log_root / (
            f"sliver-server-{scenario}-{settings.target_os}-{settings.target_arch}.log"
        )
        self.operator_log_path = self.log_root / (
            f"sliver-operator-{scenario}-{settings.target_os}-{settings.target_arch}.log"
        )
        self.console_log_path = self.server_state_root / "logs" / "console.log"
        self.server_env = isolated_server_env(
            server_root=self.server_state_root,
            client_root=self.client_state_root,
            home_root=self.home_root,
            temp_root=self.temp_root,
        )

        self.port: int | None = None
        self.operator_config: SliverClientConfig | None = None
        self.server_process: ManagedProcess | None = None
        self.client: Client | None = None
        self.version: models.clientpb.Version | None = None
        self._managed_processes: list[ManagedProcess] = []
        self._redactions: list[str] = []
        self._log_artifacts: dict[Path, Path] = {
            self.server_log_path: settings.results_root / self.server_log_path.name,
            self.operator_log_path: settings.results_root / self.operator_log_path.name,
            self.console_log_path: settings.results_root
            / (
                f"sliver-console-{scenario}-{settings.target_os}-"
                f"{settings.target_arch}.log"
            ),
        }
        self._started = False
        self._closed = False

    async def __aenter__(self) -> SliverServerHarness:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        try:
            await self.aclose()
        except E2EHarnessError as cleanup_error:
            if exc_type is None:
                raise
            raise E2EHarnessError(
                f"test body failed and E2E cleanup also failed: {cleanup_error}"
            ) from exc
        return False

    async def start(self) -> tuple[Client, models.clientpb.Version]:
        """Generate an operator, start the daemon, and connect SliverPy."""

        _require_e2e_enabled()
        if self._closed:
            raise E2EHarnessError("Sliver E2E harness is closed")
        if self._started or self.server_process is not None:
            raise E2EHarnessError("Sliver E2E harness has already been started")

        try:
            return await retry_bind_conflicts(
                self._start_once,
                reset=self._cleanup_start_attempt,
            )
        except E2EHarnessError:
            await self._cleanup_failed_start()
            raise
        except Exception:
            failure = self._server_failure("failed to start isolated Sliver server")
            await self._cleanup_failed_start()
            raise failure from None

    async def _start_once(
        self,
        port: int,
    ) -> tuple[Client, models.clientpb.Version]:
        """Run one complete operator, daemon, and client startup attempt."""

        self.port = port
        self.operator_config = await asyncio.to_thread(
            self._generate_operator_config,
            port,
        )
        self.server_process = ManagedProcess.launch(
            self.settings.server_path,
            (
                "daemon",
                "--lhost",
                LOOPBACK_HOST,
                "--lport",
                str(port),
                "--force",
                "--tailscale=false",
                "--enable-wg=false",
            ),
            cwd=self.settings.sliver_root,
            env=self.server_env,
            log_path=self.server_log_path,
            label="sliver-server",
        )
        await self._wait_for_tcp()

        client = Client.from_config_file(self.operator_config_path)
        try:
            version = await asyncio.wait_for(
                client.connect(), timeout=self.settings.connect_timeout
            )
        except Exception:
            await self._close_client(client)
            raise self._server_failure(
                "SliverPy could not authenticate to the local daemon"
            ) from None

        if (
            version.os != self.settings.target_os
            or version.arch != self.settings.target_arch
        ):
            await self._close_client(client)
            raise self._server_failure(
                "Sliver server target does not match the native E2E runner"
            )

        self.client = client
        self.version = version
        self._started = True
        return client, version

    def track_process(self, process: ManagedProcess) -> ManagedProcess:
        """Register a managed child for reverse-order harness cleanup."""

        if process not in self._managed_processes:
            self._managed_processes.append(process)
        return process

    def untrack_process(self, process: ManagedProcess) -> None:
        """Remove a process that a caller has already fully cleaned up."""

        self._managed_processes = [
            candidate
            for candidate in self._managed_processes
            if candidate is not process
        ]

    def launch_implant(
        self,
        executable: str | os.PathLike[str],
        *,
        name: str,
        args: Sequence[str] = (),
        work_dir: str | os.PathLike[str] | None = None,
    ) -> ManagedProcess:
        """Launch and track one generated implant inside this run root."""

        _require_e2e_enabled()
        if not self._started or self._closed:
            raise E2EHarnessError("Sliver server must be running before an implant")
        if not _SAFE_NAME.fullmatch(name):
            raise E2EHarnessError("implant name contains unsafe characters")
        process_root = (
            (self.implant_root / name).resolve()
            if work_dir is None
            else Path(work_dir).expanduser().resolve()
        )
        if not process_root.is_relative_to(self.run_root):
            raise E2EHarnessError("implant work directory must stay inside run_root")
        log_path = self.log_root / f"implant-{name}.log"
        process = launch_managed_implant(
            executable,
            work_dir=process_root,
            log_path=log_path,
            marker=name,
            args=args,
        )
        self._log_artifacts[log_path] = self.settings.results_root / log_path.name
        return self.track_process(process)

    async def aclose(self) -> None:
        """Close implants, the gRPC client, daemon, and private working tree."""

        if self._closed:
            return
        failures: list[str] = []

        for process in reversed(self._managed_processes):
            try:
                await process.astop(
                    self.settings.process_grace_timeout,
                    self.settings.process_kill_timeout,
                )
            except E2EHarnessError:
                failures.append(f"failed to stop {process.label}")
        self._managed_processes.clear()

        if self.client is not None:
            try:
                await self._close_client(self.client)
            except Exception:
                failures.append("failed to close SliverPy client")
            self.client = None

        if self.server_process is not None:
            try:
                await self.server_process.astop(
                    self.settings.process_grace_timeout,
                    self.settings.process_kill_timeout,
                )
            except E2EHarnessError:
                failures.append("failed to stop Sliver server")
            self.server_process = None

        self._export_diagnostic_logs()
        try:
            shutil.rmtree(self.run_root)
        except OSError:
            failures.append("failed to remove private Sliver E2E working state")
        self._closed = True
        self._started = False

        if failures:
            raise E2EHarnessError("; ".join(failures))

    def server_diagnostics(self) -> str:
        """Return a credential-sanitized server status and log tail."""

        if self.server_process is None:
            return "sliver-server was not started"
        return self.server_process.diagnostics(
            redactions=self._redactions,
            max_bytes=self.settings.log_tail_bytes,
        )

    def _generate_operator_config(self, port: int) -> SliverClientConfig:
        process = ManagedProcess.launch(
            self.settings.server_path,
            (
                "operator",
                "--name",
                self.operator_name,
                "--lhost",
                LOOPBACK_HOST,
                "--lport",
                str(port),
                "--permissions",
                "all",
                "--enable-wg=false",
                "--save",
                str(self.operator_config_path),
            ),
            cwd=self.settings.sliver_root,
            env=self.server_env,
            log_path=self.operator_log_path,
            label="sliver-operator",
        )
        try:
            returncode = process.wait(timeout=self.settings.operator_timeout)
        except E2EHarnessError:
            process.stop(
                self.settings.process_grace_timeout,
                self.settings.process_kill_timeout,
            )
            raise E2EHarnessError("Sliver operator generation timed out") from None
        finally:
            if not process.running:
                process.stop(
                    self.settings.process_grace_timeout,
                    self.settings.process_kill_timeout,
                )

        if returncode != 0 or not self.operator_config_path.is_file():
            raise E2EHarnessError(
                "Sliver operator command did not create a configuration file"
            )
        profile_stat = self.operator_config_path.stat()
        if profile_stat.st_size <= 0 or profile_stat.st_size > 1024 * 1024:
            raise E2EHarnessError("generated operator configuration has invalid size")
        if os.name != "nt" and profile_stat.st_mode & 0o077:
            raise E2EHarnessError("generated operator configuration is not private")

        try:
            config = SliverClientConfig.parse_config_file(self.operator_config_path)
        except Exception:
            raise E2EHarnessError(
                "generated operator configuration failed validation"
            ) from None

        self._redactions.extend([config.token, config.private_key, config.certificate])
        if config.wg is not None:
            self._redactions.append(config.wg.client_private_key)
        if (
            config.operator != self.operator_name
            or config.lhost != LOOPBACK_HOST
            or config.lport != port
            or config.wg is not None
        ):
            raise E2EHarnessError(
                "generated operator configuration does not match the local daemon"
            )
        return config

    async def _wait_for_tcp(self) -> None:
        if self.port is None or self.server_process is None:
            raise E2EHarnessError("Sliver daemon process is unavailable")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.settings.startup_timeout
        while True:
            if not self.server_process.running:
                raise self._server_failure(
                    "Sliver daemon exited before accepting local connections"
                )
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise self._server_failure(
                    "timed out waiting for the local Sliver daemon"
                )
            try:
                _reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(LOOPBACK_HOST, self.port),
                    timeout=min(0.5, remaining),
                )
            except (OSError, TimeoutError):
                await asyncio.sleep(min(0.25, max(remaining, 0.0)))
                continue
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()
            return

    async def _close_client(self, client: Client) -> None:
        close = getattr(client, "close", None)
        if callable(close):
            result = close()
            if inspect.isawaitable(result):
                await result
            return
        channel = getattr(client, "_channel", None)
        if channel is not None:
            await channel.close()

    def _server_failure(self, message: str) -> E2EHarnessError:
        return E2EHarnessError(f"{message}\n{self.server_diagnostics()}")

    def _export_diagnostic_logs(self) -> None:
        """Write only bounded, credential-redacted process logs to artifacts."""

        for source, destination in self._log_artifacts.items():
            contents = read_log_tail(
                source,
                max_bytes=self.settings.log_tail_bytes,
                redactions=self._redactions,
            )
            try:
                destination.write_text(f"{contents}\n", encoding="utf-8")
                if os.name != "nt":
                    destination.chmod(0o600)
            except OSError:
                continue

    async def _cleanup_start_attempt(self) -> None:
        """Reset partial startup state before trying a different loopback port."""

        failures: list[str] = []
        if self.client is not None:
            try:
                await self._close_client(self.client)
            except Exception:
                failures.append("failed to close partial SliverPy client")
            else:
                self.client = None

        if self.server_process is not None:
            try:
                await self.server_process.astop(
                    self.settings.process_grace_timeout,
                    self.settings.process_kill_timeout,
                )
            except E2EHarnessError:
                failures.append("failed to stop partial Sliver server")
            else:
                self.server_process = None

        if not failures:
            try:
                self.operator_config_path.unlink(missing_ok=True)
            except OSError:
                failures.append("failed to remove partial operator configuration")

        self.operator_config = None
        self.version = None
        self.port = None
        self._started = False
        if failures:
            raise E2EHarnessError("; ".join(failures))

    async def _cleanup_failed_start(self) -> None:
        with contextlib.suppress(Exception):
            await self.aclose()


__all__ = [
    "E2EDisabledError",
    "E2EHarnessError",
    "E2ESettings",
    "LOOPBACK_HOST",
    "ManagedProcess",
    "PORT_BIND_ATTEMPTS",
    "SliverServerHarness",
    "free_loopback_port",
    "is_bind_conflict",
    "isolated_server_env",
    "launch_managed_implant",
    "read_log_tail",
    "retry_bind_conflicts",
    "sanitized_implant_env",
]
