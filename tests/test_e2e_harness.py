from __future__ import annotations

import errno
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from sliver import models
from tests.e2e import conftest as e2e_conftest
from tests.e2e import harness
from tests.e2e.harness import (
    E2EDisabledError,
    E2EHarnessError,
    E2ESettings,
    free_loopback_port,
    is_bind_conflict,
    read_log_tail,
    retry_bind_conflicts,
    sanitized_implant_env,
)


def test_e2e_settings_require_an_explicit_execution_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("SLIVER_E2E", raising=False)

    with pytest.raises(E2EDisabledError, match="SLIVER_E2E=1"):
        E2ESettings(
            repo_root=tmp_path,
            sliver_root=tmp_path,
            server_path=tmp_path / "sliver-server",
            results_root=tmp_path / "results",
            work_root=tmp_path / "work",
            target_os="linux",
            target_arch="amd64",
        )


def test_e2e_settings_keep_private_state_out_of_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SLIVER_E2E", "1")
    (tmp_path / "pyproject.toml").touch()
    sliver_root = tmp_path / "sliver"
    sliver_root.mkdir()
    (sliver_root / "go.mod").touch()
    server_path = sliver_root / "sliver-server"
    server_path.touch(mode=0o700)
    target_os, target_arch = harness._runtime_target()
    if (target_os, target_arch) not in harness._SUPPORTED_TARGETS:
        pytest.skip("host is outside the managed E2E target matrix")
    shared_root = tmp_path / "shared"

    with pytest.raises(E2EHarnessError, match="must be disjoint"):
        E2ESettings(
            repo_root=tmp_path,
            sliver_root=sliver_root,
            server_path=server_path,
            results_root=shared_root,
            work_root=shared_root,
            target_os=target_os,
            target_arch=target_arch,
        )


def test_implant_environment_is_allowlisted_and_isolated(tmp_path: Path) -> None:
    environment = sanitized_implant_env(
        home_root=tmp_path / "home",
        temp_root=tmp_path / "tmp",
        marker="unit-test",
        host_env={
            "PATH": "/safe/path",
            "SYSTEMROOT": "C:\\Windows",
            "GITHUB_TOKEN": "must-not-leak",
            "HTTPS_PROXY": "must-not-leak",
        },
    )

    assert environment["PATH"] == "/safe/path"
    assert environment["HOME"] == str(tmp_path / "home")
    assert environment["TMP"] == str(tmp_path / "tmp")
    assert environment["SLIVER_E2E_MARKER"] == "unit-test"
    assert "GITHUB_TOKEN" not in environment
    assert "HTTPS_PROXY" not in environment
    assert "must-not-leak" not in environment.values()


def test_diagnostic_log_tail_redacts_credentials(tmp_path: Path) -> None:
    log_path = tmp_path / "server.log"
    log_path.write_text(
        'token="operator-token"\n'
        "-----BEGIN PRIVATE KEY-----\nprivate-material\n"
        "-----END PRIVATE KEY-----\n",
        encoding="utf-8",
    )

    contents = read_log_tail(log_path, redactions=("operator-token",))

    assert "operator-token" not in contents
    assert "private-material" not in contents
    assert "[REDACTED]" in contents


def test_loopback_port_retries_the_value_sliver_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = iter((65535, 31337))

    class FakeSocket:
        def __enter__(self) -> FakeSocket:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def bind(self, address: tuple[str, int]) -> None:
            assert address == ("127.0.0.1", 0)

        def listen(self, backlog: int) -> None:
            assert backlog == 1

        def getsockname(self) -> tuple[str, int]:
            return "127.0.0.1", next(ports)

    monkeypatch.setattr(harness.socket, "socket", lambda *args: FakeSocket())

    port = free_loopback_port()

    assert port == 31337


def test_loopback_port_excludes_ports_used_by_prior_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = iter((31337, 31338))

    class FakeSocket:
        def __enter__(self) -> FakeSocket:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def bind(self, address: tuple[str, int]) -> None:
            assert address == ("127.0.0.1", 0)

        def listen(self, backlog: int) -> None:
            assert backlog == 1

        def getsockname(self) -> tuple[str, int]:
            return "127.0.0.1", next(ports)

    monkeypatch.setattr(harness.socket, "socket", lambda *args: FakeSocket())

    port = free_loopback_port(exclude={31337})

    assert port == 31338


@pytest.mark.parametrize(
    "error",
    [
        OSError(errno.EADDRINUSE, "port is occupied"),
        RuntimeError("listen tcp 127.0.0.1:4444: bind: address already in use"),
        RuntimeError(
            "Only one usage of each socket address is normally permitted"
        ),
    ],
)
def test_bind_conflict_requires_explicit_platform_evidence(
    error: BaseException,
) -> None:
    assert is_bind_conflict(error)
    assert not is_bind_conflict(RuntimeError("listener failed to start"))


def test_bind_conflict_does_not_recover_a_suppressed_internal_context() -> None:
    try:
        raise OSError(errno.EADDRINUSE, "port is occupied")
    except OSError:
        try:
            raise RuntimeError("sanitized listener failure") from None
        except RuntimeError as error:
            assert not is_bind_conflict(error)


async def test_bind_conflict_retry_uses_a_new_port_and_resets_partial_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = iter((31337, 31338))
    observed: list[int] = []
    resets = 0

    def allocate(*, exclude: set[int]) -> int:
        port = next(ports)
        assert port not in exclude
        return port

    async def operation(port: int) -> str:
        observed.append(port)
        if len(observed) == 1:
            raise OSError(errno.EADDRINUSE, "port is occupied")
        return "started"

    async def reset() -> None:
        nonlocal resets
        resets += 1

    monkeypatch.setattr(harness, "free_loopback_port", allocate)

    result = await retry_bind_conflicts(operation, reset=reset)

    assert result == "started"
    assert observed == [31337, 31338]
    assert resets == 1


async def test_server_start_retries_the_complete_attempt_after_bind_conflict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SLIVER_E2E", "1")
    (tmp_path / "pyproject.toml").touch()
    sliver_root = tmp_path / "sliver"
    sliver_root.mkdir()
    (sliver_root / "go.mod").touch()
    server_path = sliver_root / "sliver-server"
    server_path.touch(mode=0o700)
    target_os, target_arch = harness._runtime_target()
    if (target_os, target_arch) not in harness._SUPPORTED_TARGETS:
        pytest.skip("host is outside the managed E2E target matrix")
    settings = E2ESettings(
        repo_root=tmp_path,
        sliver_root=sliver_root,
        server_path=server_path,
        results_root=tmp_path / "results",
        work_root=tmp_path / "work",
        target_os=target_os,
        target_arch=target_arch,
    )
    server = harness.SliverServerHarness(settings, scenario="retry-unit")
    ports = iter((31337, 31338))
    attempts: list[int] = []
    resets = 0
    expected_client = AsyncMock()
    expected_version = models.clientpb.Version(os=target_os, arch=target_arch)

    async def start_once(
        port: int,
    ) -> tuple[AsyncMock, models.clientpb.Version]:
        attempts.append(port)
        if len(attempts) == 1:
            raise E2EHarnessError("listen tcp: bind: address already in use")
        return expected_client, expected_version

    async def cleanup_attempt() -> None:
        nonlocal resets
        resets += 1

    monkeypatch.setattr(
        harness,
        "free_loopback_port",
        lambda *, exclude: next(ports),
    )
    monkeypatch.setattr(server, "_start_once", start_once)
    monkeypatch.setattr(server, "_cleanup_start_attempt", cleanup_attempt)

    try:
        client, version = await server.start()
    finally:
        await server.aclose()

    assert client is expected_client
    assert version is expected_version
    assert attempts == [31337, 31338]
    assert resets == 1


async def test_bind_conflict_retry_does_not_retry_an_unrelated_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def operation(port: int) -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError(f"listener startup failed on {port}")

    monkeypatch.setattr(
        harness,
        "free_loopback_port",
        lambda *, exclude: 31337,
    )

    with pytest.raises(RuntimeError, match="listener startup failed"):
        await retry_bind_conflicts(operation)

    assert calls == 1


async def test_listener_retry_cleans_a_partial_job_before_using_a_new_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ports = iter((31337, 31338))
    starts: list[int] = []
    readiness_checks = 0
    client = AsyncMock()
    client.kill_job.return_value = models.clientpb.KillJob(id=7, success=True)
    client.job_by_id.return_value = None

    async def start(port: int) -> models.clientpb.ListenerJob:
        starts.append(port)
        return models.clientpb.ListenerJob(job_id=6 + len(starts))

    async def wait_until_ready(port: int, timeout: float = 10.0) -> None:
        del port, timeout
        nonlocal readiness_checks
        readiness_checks += 1
        if readiness_checks == 1:
            raise RuntimeError("bind: address already in use")

    monkeypatch.setattr(
        harness,
        "free_loopback_port",
        lambda *, exclude: next(ports),
    )
    monkeypatch.setattr(
        e2e_conftest,
        "_wait_for_loopback_listener",
        wait_until_ready,
    )

    port, listener = await e2e_conftest._start_loopback_listener_with_retry(
        client,
        start,
    )

    assert port == 31338
    assert listener.job_id == 8
    assert starts == [31337, 31338]
    client.kill_job.assert_awaited_once_with(
        7,
        timeout=e2e_conftest.COMMAND_TIMEOUT,
    )
    client.job_by_id.assert_awaited_once()
    assert client.job_by_id.await_args.args == (7,)


async def test_listener_cleanup_failure_prevents_a_bind_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    starts = 0
    client = AsyncMock()
    client.kill_job.return_value = models.clientpb.KillJob(id=7, success=False)

    async def start(port: int) -> models.clientpb.ListenerJob:
        del port
        nonlocal starts
        starts += 1
        return models.clientpb.ListenerJob(job_id=7)

    async def wait_until_ready(port: int, timeout: float = 10.0) -> None:
        del port, timeout
        raise RuntimeError("bind: address already in use")

    monkeypatch.setattr(
        harness,
        "free_loopback_port",
        lambda *, exclude: 31337,
    )
    monkeypatch.setattr(
        e2e_conftest,
        "_wait_for_loopback_listener",
        wait_until_ready,
    )

    with pytest.raises(RuntimeError, match="partial listener start"):
        await e2e_conftest._start_loopback_listener_with_retry(client, start)

    assert starts == 1
