from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import pytest
import pytest_asyncio

from sliver import (
    InteractiveBeacon,
    InteractiveSession,
    SliverClient,
    models,
)

from .harness import (
    E2ESettings,
    ManagedProcess,
    SliverServerHarness,
    free_loopback_port,
)

NANOSECOND = 1_000_000_000
GENERATE_TIMEOUT = 15 * 60
REGISTRATION_TIMEOUT = 3 * 60
COMMAND_TIMEOUT = 2 * 60
POLL_INTERVAL = 0.25


@dataclass(frozen=True, slots=True)
class MTLSListener:
    """The one loopback-only C2 listener shared by the native implants."""

    port: int
    job_id: int

    @property
    def c2_url(self) -> str:
        return f"mtls://127.0.0.1:{self.port}"


@dataclass(frozen=True, slots=True)
class LiveSession:
    generated: models.clientpb.Generate
    executable: Path
    process: ManagedProcess
    target: models.clientpb.Session
    interactive: InteractiveSession


@dataclass(frozen=True, slots=True)
class LiveBeacon:
    generated: models.clientpb.Generate
    executable: Path
    process: ManagedProcess
    target: models.clientpb.Beacon
    interactive: InteractiveBeacon


ImplantConfigFactory: TypeAlias = Callable[..., models.clientpb.ImplantConfig]


def _raise_cleanup_failures(
    owner: str,
    failures: list[tuple[str, Exception]],
) -> None:
    if not failures:
        return
    summary = "; ".join(
        f"{step}: {type(error).__name__}: {error}" for step, error in failures
    )
    raise RuntimeError(f"failed to clean up {owner}: {summary}") from failures[0][1]


async def _wait_for_loopback_listener(port: int, timeout: float = 10.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port),
                timeout=min(1.0, deadline - loop.time()),
            )
        except (OSError, asyncio.TimeoutError):
            await asyncio.sleep(POLL_INTERVAL)
            continue
        writer.close()
        with suppress(OSError):
            await writer.wait_closed()
        return
    raise TimeoutError(f"mTLS listener on 127.0.0.1:{port} did not become ready")


async def _wait_for_job_removal(
    client: SliverClient,
    job_id: int,
    timeout: float = 10.0,
) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if await client.job_by_id(job_id, timeout=COMMAND_TIMEOUT) is None:
            return
        await asyncio.sleep(POLL_INTERVAL)
    raise TimeoutError(f"listener job {job_id} was not removed")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Keep these expensive tests inert unless the caller explicitly opts in."""

    if os.environ.get("SLIVER_E2E") == "1":
        return

    e2e_root = Path(__file__).parent.resolve()
    skip = pytest.mark.skip(reason="set SLIVER_E2E=1 to run managed E2E tests")
    for item in items:
        if Path(str(item.path)).resolve().is_relative_to(e2e_root):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def e2e_settings() -> E2ESettings:
    if os.environ.get("SLIVER_E2E") != "1":
        pytest.skip("set SLIVER_E2E=1 to run managed E2E tests")
    return E2ESettings.from_env()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def e2e_harness(
    e2e_settings: E2ESettings,
) -> AsyncIterator[SliverServerHarness]:
    harness = SliverServerHarness(e2e_settings)
    await harness.start()
    try:
        yield harness
    finally:
        await harness.aclose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def sliver_client(e2e_harness: SliverServerHarness) -> SliverClient:
    client = e2e_harness.client
    if client is None:
        raise RuntimeError("the E2E harness did not create a Sliver client")
    return client


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def mtls_listener(
    sliver_client: SliverClient,
) -> AsyncIterator[MTLSListener]:
    # The listener request and readiness probe both use the IPv4 loopback
    # interface; the listener RPC itself is the authoritative bind.
    port = free_loopback_port()
    listener = await sliver_client.start_mtls_listener(
        host="127.0.0.1",
        port=port,
        timeout=COMMAND_TIMEOUT,
    )
    assert isinstance(listener, models.clientpb.ListenerJob)
    assert listener.job_id > 0
    value = MTLSListener(port=port, job_id=listener.job_id)
    try:
        await _wait_for_loopback_listener(port)
        yield value
    finally:
        try:
            stopped = await asyncio.wait_for(
                sliver_client.kill_job(value.job_id, timeout=COMMAND_TIMEOUT),
                timeout=COMMAND_TIMEOUT,
            )
            assert stopped.success
            await _wait_for_job_removal(sliver_client, value.job_id)
        except Exception as error:
            raise RuntimeError("failed to stop the shared mTLS listener") from error


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def implant_config_factory(
    e2e_settings: E2ESettings,
    mtls_listener: MTLSListener,
) -> ImplantConfigFactory:
    def create(*, is_beacon: bool) -> models.clientpb.ImplantConfig:
        return models.clientpb.ImplantConfig(
            is_beacon=is_beacon,
            beacon_interval=5 * NANOSECOND if is_beacon else 0,
            beacon_jitter=0,
            goos=e2e_settings.target_os,
            goarch=e2e_settings.target_arch,
            debug=False,
            obfuscate_symbols=False,
            template_name="sliver",
            include_mtls=True,
            include_http=False,
            include_wg=False,
            include_dns=False,
            include_name_pipe=False,
            include_tcp=False,
            reconnect_interval=NANOSECOND,
            max_connection_errors=20,
            poll_timeout=NANOSECOND,
            c2=[
                models.clientpb.ImplantC2(
                    priority=0,
                    url=mtls_listener.c2_url,
                )
            ],
            connection_strategy="s",
            format=models.clientpb.OutputFormat.EXECUTABLE,
            is_shared_lib=False,
            is_service=False,
            is_shellcode=False,
            run_at_load=False,
            httpc2_config_name="default",
            net_go_enabled=True,
        )

    return create


def _save_generated_implant(
    harness: SliverServerHarness,
    generated: models.clientpb.Generate,
    *,
    kind: str,
) -> Path:
    assert generated.implant_name
    assert generated.file is not None
    assert generated.file.data

    filename = Path(generated.file.name).name
    if not filename:
        suffix = ".exe" if os.name == "nt" else ""
        filename = f"{generated.implant_name}{suffix}"

    destination = harness.implant_root / kind / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(generated.file.data)
    destination.chmod(0o700)
    return destination


async def _wait_for_session(
    client: SliverClient,
    process: ManagedProcess,
    *,
    previous_ids: set[str],
    implant_name: str,
) -> models.clientpb.Session:
    deadline = asyncio.get_running_loop().time() + REGISTRATION_TIMEOUT
    last_seen: list[models.clientpb.Session] = []
    while asyncio.get_running_loop().time() < deadline:
        if process.returncode is not None:
            raise RuntimeError(
                f"native session exited before registration: {process.diagnostics()}"
            )
        last_seen = await client.sessions(timeout=COMMAND_TIMEOUT)
        for session in last_seen:
            if (
                session.id not in previous_ids
                and session.name == implant_name
                and session.pid == process.pid
            ):
                return session
        await asyncio.sleep(POLL_INTERVAL)

    observed = [(item.id, item.name, item.pid) for item in last_seen]
    raise TimeoutError(
        "native session did not register before the timeout; "
        f"expected name={implant_name!r} pid={process.pid}, observed={observed!r}"
    )


async def _wait_for_beacon(
    client: SliverClient,
    process: ManagedProcess,
    *,
    previous_ids: set[str],
    implant_name: str,
) -> models.clientpb.Beacon:
    deadline = asyncio.get_running_loop().time() + REGISTRATION_TIMEOUT
    last_seen: list[models.clientpb.Beacon] = []
    while asyncio.get_running_loop().time() < deadline:
        if process.returncode is not None:
            raise RuntimeError(
                f"native beacon exited before registration: {process.diagnostics()}"
            )
        last_seen = await client.beacons(timeout=COMMAND_TIMEOUT)
        for beacon in last_seen:
            if (
                beacon.id not in previous_ids
                and beacon.name == implant_name
                and beacon.pid == process.pid
            ):
                return beacon
        await asyncio.sleep(POLL_INTERVAL)

    observed = [(item.id, item.name, item.pid) for item in last_seen]
    raise TimeoutError(
        "native beacon did not register before the timeout; "
        f"expected name={implant_name!r} pid={process.pid}, observed={observed!r}"
    )


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def live_session(
    e2e_harness: SliverServerHarness,
    sliver_client: SliverClient,
    implant_config_factory: ImplantConfigFactory,
) -> AsyncIterator[LiveSession]:
    previous_ids = {session.id for session in await sliver_client.sessions()}
    generated: models.clientpb.Generate | None = None
    executable: Path | None = None
    process: ManagedProcess | None = None
    target: models.clientpb.Session | None = None
    try:
        generated = await sliver_client.generate_implant(
            implant_config_factory(is_beacon=False),
            timeout=GENERATE_TIMEOUT,
        )
        assert isinstance(generated, models.clientpb.Generate)
        executable = _save_generated_implant(
            e2e_harness,
            generated,
            kind="session",
        )
        process = e2e_harness.launch_implant(
            executable,
            name=f"session-{generated.implant_name}",
        )
        target = await _wait_for_session(
            sliver_client,
            process,
            previous_ids=previous_ids,
            implant_name=generated.implant_name,
        )
        interactive = await sliver_client.interact_session(
            target.id,
            timeout=COMMAND_TIMEOUT,
        )
        assert isinstance(interactive, InteractiveSession)
        yield LiveSession(
            generated=generated,
            executable=executable,
            process=process,
            target=target,
            interactive=interactive,
        )
    finally:
        cleanup_failures: list[tuple[str, Exception]] = []
        if target is not None:
            try:
                await asyncio.wait_for(
                    sliver_client.kill_session(
                        target.id,
                        force=True,
                        timeout=COMMAND_TIMEOUT,
                    ),
                    timeout=COMMAND_TIMEOUT,
                )
                assert (
                    await sliver_client.session_by_id(
                        target.id,
                        timeout=COMMAND_TIMEOUT,
                    )
                    is None
                )
            except Exception as error:
                cleanup_failures.append(("remove session", error))
        if process is not None:
            try:
                await process.astop()
            except Exception as error:
                cleanup_failures.append(("stop session process", error))
        if generated is not None and generated.implant_name:
            try:
                await sliver_client.delete_implant_build(
                    generated.implant_name,
                    timeout=COMMAND_TIMEOUT,
                )
                assert generated.implant_name not in await sliver_client.implant_builds(
                    timeout=COMMAND_TIMEOUT
                )
            except Exception as error:
                cleanup_failures.append(("delete session build", error))
        if executable is not None:
            with suppress(OSError):
                executable.unlink()
        _raise_cleanup_failures("native session", cleanup_failures)


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def live_beacon(
    e2e_harness: SliverServerHarness,
    sliver_client: SliverClient,
    implant_config_factory: ImplantConfigFactory,
) -> AsyncIterator[LiveBeacon]:
    previous_ids = {beacon.id for beacon in await sliver_client.beacons()}
    generated: models.clientpb.Generate | None = None
    executable: Path | None = None
    process: ManagedProcess | None = None
    target: models.clientpb.Beacon | None = None
    interactive: InteractiveBeacon | None = None
    try:
        generated = await sliver_client.generate_implant(
            implant_config_factory(is_beacon=True),
            timeout=GENERATE_TIMEOUT,
        )
        assert isinstance(generated, models.clientpb.Generate)
        executable = _save_generated_implant(
            e2e_harness,
            generated,
            kind="beacon",
        )
        process = e2e_harness.launch_implant(
            executable,
            name=f"beacon-{generated.implant_name}",
        )
        target = await _wait_for_beacon(
            sliver_client,
            process,
            previous_ids=previous_ids,
            implant_name=generated.implant_name,
        )
        interactive = await sliver_client.interact_beacon(
            target.id,
            timeout=COMMAND_TIMEOUT,
        )
        assert isinstance(interactive, InteractiveBeacon)
        yield LiveBeacon(
            generated=generated,
            executable=executable,
            process=process,
            target=target,
            interactive=interactive,
        )
    finally:
        cleanup_failures = []
        # RmBeacon removes a database record; it does not stop the implant.
        if process is not None:
            try:
                await process.astop()
            except Exception as error:
                cleanup_failures.append(("stop beacon process", error))
        if interactive is not None:
            try:
                await interactive.close()
            except Exception as error:
                cleanup_failures.append(("close beacon watcher", error))
        if target is not None:
            try:
                await asyncio.wait_for(
                    sliver_client.kill_beacon(
                        target.id,
                        timeout=COMMAND_TIMEOUT,
                    ),
                    timeout=COMMAND_TIMEOUT,
                )
                assert (
                    await sliver_client.beacon_by_id(
                        target.id,
                        timeout=COMMAND_TIMEOUT,
                    )
                    is None
                )
            except Exception as error:
                cleanup_failures.append(("remove beacon", error))
        if generated is not None and generated.implant_name:
            try:
                await sliver_client.delete_implant_build(
                    generated.implant_name,
                    timeout=COMMAND_TIMEOUT,
                )
                assert generated.implant_name not in await sliver_client.implant_builds(
                    timeout=COMMAND_TIMEOUT
                )
            except Exception as error:
                cleanup_failures.append(("delete beacon build", error))
        if executable is not None:
            with suppress(OSError):
                executable.unlink()
        _raise_cleanup_failures("native beacon", cleanup_failures)
