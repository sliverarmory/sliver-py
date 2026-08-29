from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import pytest

from sliver import C2Protocol, Client, InteractiveSession, models

from .conftest import (
    COMMAND_TIMEOUT,
    INTERACTION_SCENARIO_TIMEOUT,
    LiveSession,
    MTLSListener,
    run_example_cli,
    unique_sliver_name,
)
from .harness import E2ESettings, SliverServerHarness
from .interactions import (
    exercise_captured_execute,
    exercise_environment_lifecycle,
    exercise_filesystem_lifecycle,
    exercise_read_only_inventory,
    exercise_tracked_child_lifecycle,
)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_session,
    pytest.mark.asyncio(loop_scope="session"),
]


async def test_generated_session_registers_as_the_owned_native_process(
    live_session: LiveSession,
    e2e_settings: E2ESettings,
    mtls_listener: MTLSListener,
) -> None:
    assert isinstance(live_session.generated, models.clientpb.Generate)
    assert live_session.generated.file is not None
    assert live_session.generated.file.data
    assert live_session.executable.is_file()
    assert live_session.process.running

    target = live_session.target
    assert isinstance(target, models.clientpb.Session)
    assert target.id
    assert target.name == live_session.generated.implant_name
    assert target.pid == live_session.process.pid
    assert target.os == e2e_settings.target_os
    assert target.arch == e2e_settings.target_arch
    assert target.transport == str(C2Protocol.MTLS)
    if target.active_c2:
        assert target.active_c2 == mtls_listener.c2_url
    assert not target.is_dead
    assert live_session.interactive.session_id == target.id


async def test_client_resolves_renames_and_uses_the_live_session(
    live_session: LiveSession,
    sliver_client: Client,
) -> None:
    target = live_session.target
    assert await sliver_client.find_session(target.id) == target
    assert await sliver_client.get_session(target.id) == target
    interaction = await sliver_client.use(target)
    assert isinstance(interaction, InteractiveSession)
    assert interaction.session_id == target.id

    updated_name = unique_sliver_name("session-e2e-")
    await sliver_client.rename_session(target.id, updated_name)
    try:
        renamed = await sliver_client.get_session(target.id)
        assert renamed.name == updated_name
    finally:
        await sliver_client.rename_session(target.id, target.name)
    assert (await sliver_client.get_session(target.id)).name == target.name


async def test_generated_session_supports_portable_read_only_commands(
    live_session: LiveSession,
) -> None:
    await asyncio.wait_for(
        exercise_read_only_inventory(
            live_session.interactive,
            implant_pid=live_session.process.pid,
            work_dir=live_session.work_dir,
        ),
        timeout=INTERACTION_SCENARIO_TIMEOUT,
    )


async def test_generated_session_manages_files_and_environment(
    live_session: LiveSession,
) -> None:
    await asyncio.wait_for(
        exercise_filesystem_lifecycle(
            live_session.interactive,
            work_dir=live_session.work_dir,
            label="session",
        ),
        timeout=INTERACTION_SCENARIO_TIMEOUT,
    )
    await asyncio.wait_for(
        exercise_environment_lifecycle(
            live_session.interactive,
            label="session",
        ),
        timeout=INTERACTION_SCENARIO_TIMEOUT,
    )


async def test_generated_session_executes_and_tracks_owned_processes(
    live_session: LiveSession,
) -> None:
    await asyncio.wait_for(
        exercise_captured_execute(live_session.interactive, label="session"),
        timeout=COMMAND_TIMEOUT,
    )
    await asyncio.wait_for(
        exercise_tracked_child_lifecycle(live_session.interactive),
        timeout=COMMAND_TIMEOUT,
    )


async def test_generated_session_lists_extensions_and_pivots(
    live_session: LiveSession,
) -> None:
    extensions, pivots = await asyncio.wait_for(
        asyncio.gather(
            live_session.interactive.extensions_list(),
            live_session.interactive.pivots(),
        ),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(extensions, models.sliverpb.ListExtensions)
    assert extensions.names == []
    assert pivots == []


async def test_interaction_example_runs_against_the_live_session(
    live_session: LiveSession,
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
) -> None:
    python = Path(sys.executable).resolve()
    marker = f"sliver-py-session-example-{uuid.uuid4().hex}"

    output = await run_example_cli(
        e2e_harness,
        e2e_settings,
        "examples.interact",
        "session",
        live_session.target.id,
        "--executable",
        str(python),
        "--argument=-c",
        f"--argument=print({marker!r})",
        "--timeout",
        str(COMMAND_TIMEOUT),
        timeout=COMMAND_TIMEOUT,
    )

    assert live_session.target.id in output
    assert "Working directory:" in output
    assert marker in output
