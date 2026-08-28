from __future__ import annotations

import asyncio
from contextlib import suppress

import pytest

from sliver import SliverClient, models

from .conftest import (
    COMMAND_TIMEOUT,
    MTLSListener,
    _wait_for_job_removal,
    example_command,
    run_example_cli,
)
from .harness import E2ESettings, SliverServerHarness, free_loopback_port

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_basic,
    pytest.mark.asyncio(loop_scope="session"),
]


async def test_server_version_matches_the_native_runner(
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
    sliver_client: SliverClient,
) -> None:
    version = await asyncio.wait_for(
        sliver_client.version(timeout=COMMAND_TIMEOUT),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(version, models.clientpb.Version)
    assert version == e2e_harness.version
    assert version.os == e2e_settings.target_os
    assert version.arch == e2e_settings.target_arch


async def test_server_lists_the_generated_operator_as_a_pydantic_model(
    e2e_harness: SliverServerHarness,
    sliver_client: SliverClient,
) -> None:
    operators = await sliver_client.operators(timeout=COMMAND_TIMEOUT)

    assert operators
    assert all(isinstance(item, models.clientpb.Operator) for item in operators)
    assert e2e_harness.operator_config is not None
    assert e2e_harness.operator_config.operator in {item.name for item in operators}


async def test_server_lists_implants_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    sessions, beacons, builds = await asyncio.gather(
        sliver_client.sessions(timeout=COMMAND_TIMEOUT),
        sliver_client.beacons(timeout=COMMAND_TIMEOUT),
        sliver_client.implant_builds(timeout=COMMAND_TIMEOUT),
    )

    assert all(isinstance(item, models.clientpb.Session) for item in sessions)
    assert all(isinstance(item, models.clientpb.Beacon) for item in beacons)
    assert all(
        isinstance(item, models.clientpb.ImplantConfig) for item in builds.values()
    )


async def test_inventory_example_cli_connects_and_exits_cleanly(
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
) -> None:
    output = await run_example_cli(
        e2e_harness,
        e2e_settings,
        "examples.inventory",
        "--timeout",
        str(COMMAND_TIMEOUT),
        timeout=COMMAND_TIMEOUT,
    )
    assert e2e_harness.version is not None
    assert (
        f"Sliver {e2e_harness.version.major}.{e2e_harness.version.minor}."
        f"{e2e_harness.version.patch}" in output
    )
    assert e2e_harness.operator_name in output


async def test_shared_mtls_listener_is_loopback_only_and_queryable(
    sliver_client: SliverClient,
    mtls_listener: MTLSListener,
) -> None:
    jobs = await sliver_client.jobs(timeout=COMMAND_TIMEOUT)

    assert all(isinstance(item, models.clientpb.Job) for item in jobs)
    job = await sliver_client.job_by_id(
        mtls_listener.job_id,
        timeout=COMMAND_TIMEOUT,
    )
    assert isinstance(job, models.clientpb.Job)
    assert job.id == mtls_listener.job_id
    assert job.port == mtls_listener.port
    assert job.protocol.lower() == "tcp"
    assert (
        await sliver_client.job_by_port(
            mtls_listener.port,
            timeout=COMMAND_TIMEOUT,
        )
        == job
    )


async def test_event_and_temporary_listener_examples_work_together(
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
    sliver_client: SliverClient,
) -> None:
    event_command = example_command(
        e2e_harness,
        e2e_settings,
        "examples.watch_events",
        "job-started",
        "--count",
        "1",
        "--timeout",
        str(COMMAND_TIMEOUT),
    )
    event_process = await asyncio.create_subprocess_exec(
        *event_command,
        cwd=e2e_settings.repo_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    listener_job_ids: list[int] = []
    listener_ports: list[int] = []
    try:
        deadline = asyncio.get_running_loop().time() + 10
        while asyncio.get_running_loop().time() < deadline:
            if event_process.returncode is not None:
                raise RuntimeError("event example exited before subscribing")
            operators = await sliver_client.operators(timeout=COMMAND_TIMEOUT)
            if any(
                item.name == e2e_harness.operator_name and item.online
                for item in operators
            ):
                break
            await asyncio.sleep(0.05)
        else:
            raise TimeoutError("event example did not subscribe within 10 seconds")

        # The first start is also a broker synchronization event: Sliver does
        # not acknowledge EventBroker.Subscribe on its streaming RPC. A second
        # start makes the assertion deterministic if the first publication and
        # subscription crossed in the broker's select loop.
        for _attempt in range(2):
            port = free_loopback_port()
            listener_ports.append(port)
            output = await run_example_cli(
                e2e_harness,
                e2e_settings,
                "examples.temporary_listener",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--duration",
                "0.01",
                "--timeout",
                str(COMMAND_TIMEOUT),
                timeout=COMMAND_TIMEOUT,
            )
            prefix = "Started and stopped job "
            job_id = next(
                (
                    int(line.removeprefix(prefix))
                    for line in output.splitlines()
                    if line.startswith(prefix)
                ),
                0,
            )
            assert job_id > 0
            assert "Stop succeeded: True" in output
            listener_job_ids.append(job_id)
            await _wait_for_job_removal(sliver_client, job_id)

        stdout, stderr = await asyncio.wait_for(
            event_process.communicate(),
            timeout=COMMAND_TIMEOUT,
        )
    finally:
        if event_process.returncode is None:
            with suppress(ProcessLookupError):
                event_process.kill()
            await event_process.communicate()

    error = stderr.decode(errors="replace")[-8192:]
    assert event_process.returncode == 0, error
    event = models.clientpb.Event.model_validate_json(stdout)
    assert event.event_type == "job-started"
    assert event.job is not None
    assert event.job.id in listener_job_ids
    assert event.job.port in listener_ports
    for job_id in listener_job_ids:
        assert await sliver_client.job_by_id(job_id) is None
