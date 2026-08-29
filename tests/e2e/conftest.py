from __future__ import annotations

import asyncio
import math
import os
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

import pytest
import pytest_asyncio

from sliver import (
    C2Protocol,
    Client,
    InteractiveBeacon,
    InteractiveSession,
    models,
)

from .harness import (
    E2ESettings,
    ManagedProcess,
    SliverServerHarness,
    retry_bind_conflicts,
)

GENERATE_TIMEOUT = 15 * 60
REGISTRATION_TIMEOUT = 3 * 60
COMMAND_TIMEOUT = 2 * 60
INTERACTION_SCENARIO_TIMEOUT = 5 * 60
POLL_INTERVAL = 0.25


@dataclass(frozen=True, slots=True)
class MTLSListener:
    """The one loopback-only C2 listener shared by the native implants."""

    port: int
    job_id: int

    @property
    def c2_url(self) -> str:
        return f"{C2Protocol.MTLS}://127.0.0.1:{self.port}"


@dataclass(frozen=True, slots=True)
class LiveSession:
    generated: models.clientpb.Generate
    executable: Path
    work_dir: Path
    process: ManagedProcess
    target: models.clientpb.Session
    interactive: InteractiveSession


@dataclass(frozen=True, slots=True)
class LiveBeacon:
    generated: models.clientpb.Generate
    executable: Path
    work_dir: Path
    process: ManagedProcess
    target: models.clientpb.Beacon
    interactive: InteractiveBeacon


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
    client: Client,
    job_id: int,
    timeout: float = 10.0,
) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        remaining = deadline - loop.time()
        rpc_timeout = max(1, min(COMMAND_TIMEOUT, math.ceil(remaining)))
        if await asyncio.wait_for(
            client.job_by_id(job_id, timeout=rpc_timeout),
            timeout=remaining,
        ) is None:
            return
        await asyncio.sleep(POLL_INTERVAL)
    raise TimeoutError(f"listener job {job_id} was not removed")


async def _stop_listener_job(client: Client, job_id: int) -> None:
    stopped = await asyncio.wait_for(
        client.kill_job(job_id, timeout=COMMAND_TIMEOUT),
        timeout=COMMAND_TIMEOUT,
    )
    if stopped.id != job_id or not stopped.success:
        raise RuntimeError(f"Sliver did not stop listener job {job_id}")
    await _wait_for_job_removal(client, job_id)


async def _start_loopback_listener_with_retry(
    client: Client,
    start: Callable[[int], Awaitable[models.clientpb.ListenerJob]],
) -> tuple[int, models.clientpb.ListenerJob]:
    """Start one ready listener, retrying only explicit port bind conflicts."""

    async def start_once(port: int) -> tuple[int, models.clientpb.ListenerJob]:
        listener: models.clientpb.ListenerJob | None = None
        try:
            listener = await start(port)
            if listener.job_id <= 0:
                raise RuntimeError("Sliver did not return a listener job ID")
            await _wait_for_loopback_listener(port)
            return port, listener
        except BaseException:
            if listener is not None and listener.job_id > 0:
                try:
                    await _stop_listener_job(client, listener.job_id)
                except Exception:
                    raise RuntimeError(
                        "failed to clean up a partial listener start"
                    ) from None
            raise

    return await retry_bind_conflicts(start_once)


def example_command(
    harness: SliverServerHarness,
    settings: E2ESettings,
    module: str,
    *arguments: str,
) -> tuple[str, ...]:
    """Build a host-native command for one repository example module."""

    return (
        sys.executable,
        "-m",
        module,
        "--config",
        str(harness.operator_config_path),
        *arguments,
    )


async def run_example_cli(
    harness: SliverServerHarness,
    settings: E2ESettings,
    module: str,
    *arguments: str,
    timeout: float = COMMAND_TIMEOUT,
) -> str:
    """Run an example module to completion and return its standard output."""

    command = example_command(harness, settings, module, *arguments)
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=settings.repo_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except BaseException as error:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
        try:
            _stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10,
            )
        except asyncio.TimeoutError:
            stderr = b"example process did not exit after forced termination"
        if not isinstance(error, asyncio.TimeoutError):
            raise
        diagnostic = stderr.decode(errors="replace")[-8192:]
        raise TimeoutError(
            f"example {module!r} did not exit within {timeout} seconds: {diagnostic}"
        ) from error

    stderr_text = stderr.decode(errors="replace")[-8192:]
    if process.returncode != 0:
        raise RuntimeError(
            f"example {module!r} exited with {process.returncode}: {stderr_text}"
        )
    return stdout.decode(errors="replace")


async def _generate_implant_with_example(
    harness: SliverServerHarness,
    settings: E2ESettings,
    listener: MTLSListener,
    *,
    kind: str,
    is_beacon: bool,
) -> tuple[models.clientpb.Generate, Path]:
    """Run the generation CLI and reconstruct its public result model."""

    suffix = ".exe" if settings.target_os == "windows" else ""
    output = harness.implant_root / kind / f"example-{kind}{suffix}"
    arguments = [
        listener.c2_url,
        "--output",
        str(output),
        "--timeout",
        str(GENERATE_TIMEOUT),
    ]
    if is_beacon:
        arguments.append("--beacon")
    stdout = await run_example_cli(
        harness,
        settings,
        "examples.generate_implant",
        *arguments,
        timeout=GENERATE_TIMEOUT + COMMAND_TIMEOUT,
    )
    prefix = "Implant name: "
    implant_name = next(
        (
            line.removeprefix(prefix).strip()
            for line in stdout.splitlines()
            if line.startswith(prefix)
        ),
        "",
    )
    if not implant_name:
        raise RuntimeError(f"generation example omitted the implant name: {stdout!r}")
    data = output.read_bytes()
    if not data:
        raise RuntimeError("generation example wrote an empty implant")
    generated = models.clientpb.Generate(
        implant_name=implant_name,
        file=models.commonpb.File(name=output.name, data=data),
    )
    return generated, output


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


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def e2e_harness(
    e2e_settings: E2ESettings,
    request: pytest.FixtureRequest,
) -> AsyncIterator[SliverServerHarness]:
    scenario = Path(str(request.node.path)).stem.removeprefix("test_")
    harness = SliverServerHarness(e2e_settings, scenario=scenario)
    await harness.start()
    try:
        yield harness
    finally:
        await harness.aclose()


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def sliver_client(e2e_harness: SliverServerHarness) -> Client:
    client = e2e_harness.client
    if client is None:
        raise RuntimeError("the E2E harness did not create a Sliver client")
    return client


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def mtls_listener(
    sliver_client: Client,
) -> AsyncIterator[MTLSListener]:
    # The listener request and readiness probe both use the IPv4 loopback
    # interface; the listener RPC itself is the authoritative bind.
    async def start(port: int) -> models.clientpb.ListenerJob:
        return await sliver_client.start_mtls_listener(
            host="127.0.0.1",
            port=port,
            timeout=COMMAND_TIMEOUT,
        )

    port, listener = await _start_loopback_listener_with_retry(
        sliver_client,
        start,
    )
    assert isinstance(listener, models.clientpb.ListenerJob)
    value = MTLSListener(port=port, job_id=listener.job_id)
    try:
        yield value
    finally:
        try:
            await _stop_listener_job(sliver_client, value.job_id)
        except Exception as error:
            raise RuntimeError("failed to stop the shared mTLS listener") from error


async def _wait_for_session(
    client: Client,
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
        remaining = deadline - asyncio.get_running_loop().time()
        rpc_timeout = max(1, min(COMMAND_TIMEOUT, math.ceil(remaining)))
        last_seen = await asyncio.wait_for(
            client.sessions(timeout=rpc_timeout),
            timeout=remaining,
        )
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
    client: Client,
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
        remaining = deadline - asyncio.get_running_loop().time()
        rpc_timeout = max(1, min(COMMAND_TIMEOUT, math.ceil(remaining)))
        last_seen = await asyncio.wait_for(
            client.beacons(timeout=rpc_timeout),
            timeout=remaining,
        )
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


async def _wait_for_session_removal(
    client: Client,
    session_id: str,
    timeout: float = 30.0,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"session {session_id} was not removed")
        rpc_timeout = max(1, min(COMMAND_TIMEOUT, math.ceil(remaining)))
        if await asyncio.wait_for(
            client.session_by_id(session_id, timeout=rpc_timeout),
            timeout=remaining,
        ) is None:
            return
        await asyncio.sleep(min(POLL_INTERVAL, remaining))


async def _wait_for_beacon_removal(
    client: Client,
    beacon_id: str,
    timeout: float = 30.0,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"beacon {beacon_id} was not removed")
        rpc_timeout = max(1, min(COMMAND_TIMEOUT, math.ceil(remaining)))
        if await asyncio.wait_for(
            client.beacon_by_id(beacon_id, timeout=rpc_timeout),
            timeout=remaining,
        ) is None:
            return
        await asyncio.sleep(min(POLL_INTERVAL, remaining))


async def _wait_for_build_removal(
    client: Client,
    implant_name: str,
    timeout: float = 30.0,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"implant build {implant_name!r} was not removed")
        rpc_timeout = max(1, min(COMMAND_TIMEOUT, math.ceil(remaining)))
        builds = await asyncio.wait_for(
            client.implant_builds(timeout=rpc_timeout),
            timeout=remaining,
        )
        if implant_name not in builds:
            return
        await asyncio.sleep(min(POLL_INTERVAL, remaining))


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def live_session(
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
    sliver_client: Client,
    mtls_listener: MTLSListener,
) -> AsyncIterator[LiveSession]:
    previous_ids = {session.id for session in await sliver_client.sessions()}
    generated: models.clientpb.Generate | None = None
    executable: Path | None = None
    process: ManagedProcess | None = None
    work_dir: Path | None = None
    target: models.clientpb.Session | None = None
    try:
        generated, executable = await _generate_implant_with_example(
            e2e_harness,
            e2e_settings,
            mtls_listener,
            kind="session",
            is_beacon=False,
        )
        assert isinstance(generated, models.clientpb.Generate)
        process_name = f"session-{generated.implant_name}"
        work_dir = e2e_harness.implant_root / process_name
        process = e2e_harness.launch_implant(
            executable,
            name=process_name,
            work_dir=work_dir,
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
            work_dir=work_dir,
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
                await _wait_for_session_removal(sliver_client, target.id)
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
                await _wait_for_build_removal(
                    sliver_client,
                    generated.implant_name,
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
    e2e_settings: E2ESettings,
    sliver_client: Client,
    mtls_listener: MTLSListener,
) -> AsyncIterator[LiveBeacon]:
    previous_ids = {beacon.id for beacon in await sliver_client.beacons()}
    generated: models.clientpb.Generate | None = None
    executable: Path | None = None
    process: ManagedProcess | None = None
    work_dir: Path | None = None
    target: models.clientpb.Beacon | None = None
    interactive: InteractiveBeacon | None = None
    try:
        generated, executable = await _generate_implant_with_example(
            e2e_harness,
            e2e_settings,
            mtls_listener,
            kind="beacon",
            is_beacon=True,
        )
        assert isinstance(generated, models.clientpb.Generate)
        process_name = f"beacon-{generated.implant_name}"
        work_dir = e2e_harness.implant_root / process_name
        process = e2e_harness.launch_implant(
            executable,
            name=process_name,
            work_dir=work_dir,
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
            work_dir=work_dir,
            process=process,
            target=target,
            interactive=interactive,
        )
    finally:
        cleanup_failures = []
        # Stop the owned process first, then remove its database record.
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
                    sliver_client.rm_beacon(
                        target.id,
                        timeout=COMMAND_TIMEOUT,
                    ),
                    timeout=COMMAND_TIMEOUT,
                )
                await _wait_for_beacon_removal(sliver_client, target.id)
            except Exception as error:
                cleanup_failures.append(("remove beacon", error))
        if generated is not None and generated.implant_name:
            try:
                await sliver_client.delete_implant_build(
                    generated.implant_name,
                    timeout=COMMAND_TIMEOUT,
                )
                await _wait_for_build_removal(
                    sliver_client,
                    generated.implant_name,
                )
            except Exception as error:
                cleanup_failures.append(("delete beacon build", error))
        if executable is not None:
            with suppress(OSError):
                executable.unlink()
        _raise_cleanup_failures("native beacon", cleanup_failures)
