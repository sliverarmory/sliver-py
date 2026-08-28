from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e import harness
from tests.e2e.harness import (
    E2EDisabledError,
    E2EHarnessError,
    E2ESettings,
    free_loopback_port,
    read_log_tail,
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
