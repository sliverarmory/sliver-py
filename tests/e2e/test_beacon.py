from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import pytest

from sliver import BeaconTaskState, C2Protocol, Client, InteractiveBeacon, models

from .conftest import (
    COMMAND_TIMEOUT,
    INTERACTION_SCENARIO_TIMEOUT,
    LiveBeacon,
    MTLSListener,
    run_example_cli,
)
from .harness import E2ESettings, SliverServerHarness
from .interactions import (
    assert_implant_response_succeeded,
    exercise_captured_execute,
    exercise_environment_lifecycle,
    exercise_filesystem_lifecycle,
    exercise_read_only_inventory,
    exercise_tracked_child_lifecycle,
)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_beacon,
    pytest.mark.asyncio(loop_scope="session"),
]


async def test_generated_beacon_registers_as_the_owned_native_process(
    live_beacon: LiveBeacon,
    e2e_settings: E2ESettings,
    mtls_listener: MTLSListener,
) -> None:
    assert isinstance(live_beacon.generated, models.clientpb.Generate)
    assert live_beacon.generated.file is not None
    assert live_beacon.generated.file.data
    assert live_beacon.executable.is_file()
    assert live_beacon.process.running

    target = live_beacon.target
    assert isinstance(target, models.clientpb.Beacon)
    assert target.id
    assert target.name == live_beacon.generated.implant_name
    assert target.pid == live_beacon.process.pid
    assert target.os == e2e_settings.target_os
    assert target.arch == e2e_settings.target_arch
    assert target.transport == str(C2Protocol.MTLS)
    if target.active_c2:
        assert target.active_c2 == mtls_listener.c2_url
    assert not target.is_dead
    assert live_beacon.interactive.beacon_id == target.id


async def test_client_resolves_renames_and_uses_the_live_beacon(
    live_beacon: LiveBeacon,
    sliver_client: Client,
) -> None:
    target = live_beacon.target
    assert await sliver_client.find_beacon(target.id) == target
    assert await sliver_client.get_beacon(target.id) == target
    interaction = await sliver_client.use(target)
    assert isinstance(interaction, InteractiveBeacon)
    assert interaction.beacon_id == target.id

    updated_name = f"beacon-e2e-{uuid.uuid4().hex}"
    await sliver_client.rename_beacon(target.id, updated_name)
    try:
        renamed = await sliver_client.get_beacon(target.id)
        assert renamed.name == updated_name
    finally:
        await sliver_client.rename_beacon(target.id, target.name)
    assert (await sliver_client.get_beacon(target.id)).name == target.name


async def test_generated_beacon_supports_portable_read_only_commands(
    live_beacon: LiveBeacon,
) -> None:
    await asyncio.wait_for(
        exercise_read_only_inventory(
            live_beacon.interactive,
            implant_pid=live_beacon.process.pid,
            work_dir=live_beacon.work_dir,
        ),
        timeout=INTERACTION_SCENARIO_TIMEOUT,
    )


async def test_generated_beacon_manages_files_and_environment(
    live_beacon: LiveBeacon,
) -> None:
    await asyncio.wait_for(
        exercise_filesystem_lifecycle(
            live_beacon.interactive,
            work_dir=live_beacon.work_dir,
            label="beacon",
        ),
        timeout=INTERACTION_SCENARIO_TIMEOUT,
    )
    await asyncio.wait_for(
        exercise_environment_lifecycle(
            live_beacon.interactive,
            label="beacon",
        ),
        timeout=INTERACTION_SCENARIO_TIMEOUT,
    )


async def test_generated_beacon_executes_with_output_and_environment(
    live_beacon: LiveBeacon,
) -> None:
    await asyncio.wait_for(
        exercise_captured_execute(live_beacon.interactive, label="beacon"),
        timeout=COMMAND_TIMEOUT,
    )
    await asyncio.wait_for(
        exercise_tracked_child_lifecycle(live_beacon.interactive),
        timeout=COMMAND_TIMEOUT,
    )


async def test_beacon_command_is_correlated_with_completed_task_content(
    live_beacon: LiveBeacon,
    sliver_client: Client,
) -> None:
    before = {
        task.id
        for task in await sliver_client.tasks(live_beacon.target.id)
    }
    nonce = 0x51A7E2E

    ping = await live_beacon.interactive.ping(nonce)
    assert_implant_response_succeeded(ping)
    assert ping.nonce == nonce

    delta = [
        task
        for task in await sliver_client.tasks(live_beacon.target.id)
        if task.id not in before
    ]
    assert len(delta) == 1
    task = delta[0]
    assert task.beacon_id == live_beacon.target.id
    assert task.state == str(BeaconTaskState.COMPLETED)
    assert task.completed_at > 0

    fetched = await sliver_client.tasks_fetch(task.id)
    assert fetched.id == task.id
    assert fetched.beacon_id == live_beacon.target.id
    assert fetched.state == str(BeaconTaskState.COMPLETED)
    assert fetched.completed_at == task.completed_at
    assert fetched.request
    assert fetched.response


async def test_interaction_example_runs_against_the_live_beacon(
    live_beacon: LiveBeacon,
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
) -> None:
    python = Path(sys.executable).resolve()
    marker = f"sliver-py-beacon-example-{uuid.uuid4().hex}"

    output = await run_example_cli(
        e2e_harness,
        e2e_settings,
        "examples.interact",
        "beacon",
        live_beacon.target.id,
        "--executable",
        str(python),
        "--argument=-c",
        f"--argument=print({marker!r})",
        "--timeout",
        str(COMMAND_TIMEOUT),
        timeout=COMMAND_TIMEOUT,
    )

    assert live_beacon.target.id in output
    assert "Working directory:" in output
    assert marker in output
