from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import pytest

from sliver import models

from .conftest import COMMAND_TIMEOUT, LiveBeacon, MTLSListener
from .harness import E2ESettings

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_beacon,
    pytest.mark.asyncio(loop_scope="session"),
]


def _assert_implant_response_succeeded(result: object) -> None:
    response = getattr(result, "response", None)
    assert response is None or not response.err


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
    assert target.transport == "mtls"
    if target.active_c2:
        assert target.active_c2 == mtls_listener.c2_url
    assert not target.is_dead
    assert live_beacon.interactive.beacon_id == target.id


async def test_generated_beacon_supports_ping_and_pwd(
    live_beacon: LiveBeacon,
) -> None:
    ping = await asyncio.wait_for(
        live_beacon.interactive.ping(),
        timeout=COMMAND_TIMEOUT,
    )
    pwd = await asyncio.wait_for(
        live_beacon.interactive.pwd(),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(ping, models.sliverpb.Ping)
    _assert_implant_response_succeeded(ping)
    assert isinstance(pwd, models.sliverpb.Pwd)
    _assert_implant_response_succeeded(pwd)
    assert pwd.path
    assert Path(pwd.path).is_absolute()


async def test_generated_beacon_executes_the_runner_python(
    live_beacon: LiveBeacon,
) -> None:
    python = Path(sys.executable).resolve()
    marker = f"sliver-py-beacon-{uuid.uuid4().hex}"

    assert python.is_absolute()
    executed = await asyncio.wait_for(
        live_beacon.interactive.execute(
            str(python),
            ["-c", f"print({marker!r})"],
        ),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(executed, models.sliverpb.Execute)
    _assert_implant_response_succeeded(executed)
    assert executed.status == 0
    assert marker.encode() in executed.stdout
