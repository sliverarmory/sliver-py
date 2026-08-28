from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import pytest

from sliver import models

from .conftest import COMMAND_TIMEOUT, LiveSession, MTLSListener
from .harness import E2ESettings

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_session,
    pytest.mark.asyncio(loop_scope="session"),
]


def _assert_implant_response_succeeded(result: object) -> None:
    response = getattr(result, "response", None)
    assert response is None or not response.err


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
    assert target.transport == "mtls"
    if target.active_c2:
        assert target.active_c2 == mtls_listener.c2_url
    assert not target.is_dead
    assert live_session.interactive.session_id == target.id


async def test_generated_session_supports_ping_and_pwd(
    live_session: LiveSession,
) -> None:
    ping = await asyncio.wait_for(
        live_session.interactive.ping(),
        timeout=COMMAND_TIMEOUT,
    )
    pwd = await asyncio.wait_for(
        live_session.interactive.pwd(),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(ping, models.sliverpb.Ping)
    _assert_implant_response_succeeded(ping)
    assert isinstance(pwd, models.sliverpb.Pwd)
    _assert_implant_response_succeeded(pwd)
    assert pwd.path
    assert Path(pwd.path).is_absolute()


async def test_generated_session_executes_the_runner_python(
    live_session: LiveSession,
) -> None:
    python = Path(sys.executable).resolve()
    marker = f"sliver-py-session-{uuid.uuid4().hex}"

    assert python.is_absolute()
    executed = await asyncio.wait_for(
        live_session.interactive.execute(
            str(python),
            ["-c", f"print({marker!r})"],
        ),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(executed, models.sliverpb.Execute)
    _assert_implant_response_succeeded(executed)
    assert executed.status == 0
    assert marker.encode() in executed.stdout
