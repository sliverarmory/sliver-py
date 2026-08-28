from __future__ import annotations

import os
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.interactive]

_LEGACY_CONFIG_PATH = Path("~/.sliver-client/configs/sliverpy.cfg").expanduser()
_config_override = os.environ.get("SLIVER_CONFIG")
SLIVER_CONFIG_PATH = (
    Path(_config_override).expanduser() if _config_override else _LEGACY_CONFIG_PATH
)

if not SLIVER_CONFIG_PATH.is_file():
    pytest.skip(
        "Sliver integration tests require an operator config; set SLIVER_CONFIG "
        f"or create {_LEGACY_CONFIG_PATH}",
        allow_module_level=True,
    )

import pytest_asyncio  # noqa: E402

from sliver import (  # noqa: E402
    InteractiveSession,
    SliverClient,
    SliverClientConfig,
    models,
)


@pytest_asyncio.fixture(scope="module")
async def sliver_client() -> AsyncIterator[SliverClient]:
    config = SliverClientConfig.parse_config_file(SLIVER_CONFIG_PATH)
    client = SliverClient(config)
    await client.connect()
    try:
        yield client
    finally:
        if client._channel is not None:
            await client._channel.close()


@pytest_asyncio.fixture(scope="module")
async def interactive_session(sliver_client: SliverClient) -> InteractiveSession:
    sessions = await sliver_client.sessions()
    if not sessions:
        pytest.skip("the Sliver server has no active sessions")

    session = await sliver_client.interact_session(sessions[0].id)
    assert session is not None
    return session


@pytest.fixture(scope="module")
def remote_test_directory() -> str:
    return f"sliver-pytest-{secrets.token_hex(8)}"


async def test_interactive_session_sends_a_ping(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.ping()

    assert isinstance(response, models.sliverpb.Ping)


async def test_interactive_session_lists_processes(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.ps()

    assert isinstance(response, models.sliverpb.Ps)
    assert all(
        isinstance(process, models.commonpb.Process) for process in response.processes
    )


async def test_interactive_session_lists_network_interfaces(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.ifconfig()

    assert isinstance(response, models.sliverpb.Ifconfig)
    assert all(
        isinstance(interface, models.sliverpb.NetInterface)
        for interface in response.net_interfaces
    )


async def test_interactive_session_lists_network_connections(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.netstat(
        tcp=True,
        udp=True,
        ipv4=True,
        ipv6=True,
        listening=True,
    )

    assert isinstance(response, models.sliverpb.Netstat)
    assert all(
        isinstance(entry, models.sliverpb.SockTabEntry) for entry in response.entries
    )


async def test_interactive_session_reports_its_working_directory(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.pwd()

    assert isinstance(response, models.sliverpb.Pwd)
    assert response.path


async def test_interactive_session_lists_its_working_directory(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.ls()

    assert isinstance(response, models.sliverpb.Ls)
    assert response.exists


async def test_interactive_session_changes_to_its_current_directory(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.cd(".")

    assert isinstance(response, models.sliverpb.Pwd)
    assert response.path


async def test_interactive_session_manages_a_remote_file_lifecycle(
    interactive_session: InteractiveSession,
    remote_test_directory: str,
) -> None:
    remote_file = f"{remote_test_directory}/sliverpy.txt"
    created = False

    try:
        directory = await interactive_session.mkdir(remote_test_directory)
        created = True
        assert isinstance(directory, models.sliverpb.Mkdir)

        upload = await interactive_session.upload(remote_file, b"sliverpy")
        assert isinstance(upload, models.sliverpb.Upload)

        download = await interactive_session.download(remote_file)
        assert isinstance(download, models.sliverpb.Download)
        assert download.exists
    finally:
        if created:
            removed = await interactive_session.rm(
                remote_test_directory,
                recursive=True,
                force=True,
            )

    assert isinstance(removed, models.sliverpb.Rm)


async def test_interactive_session_manages_an_environment_variable_lifecycle(
    interactive_session: InteractiveSession,
) -> None:
    key = "SLIVERPY_TEST"
    value = f"sliver-pytest-{secrets.token_hex(8)}"

    set_result = await interactive_session.set_env(key, value)
    assert isinstance(set_result, models.sliverpb.SetEnv)
    try:
        env_info = await interactive_session.get_env(key)
        assert isinstance(env_info, models.sliverpb.EnvInfo)
        assert any(
            variable.key == key and variable.value == value
            for variable in env_info.variables
        )
    finally:
        unset_result = await interactive_session.unset_env(key)

    assert isinstance(unset_result, models.sliverpb.UnsetEnv)


async def test_interactive_session_takes_a_screenshot(
    interactive_session: InteractiveSession,
) -> None:
    response = await interactive_session.screenshot()

    assert isinstance(response, models.sliverpb.Screenshot)


async def test_interactive_session_dumps_an_owned_process(
    interactive_session: InteractiveSession,
) -> None:
    process_list = await interactive_session.ps()
    owned_processes = [
        process
        for process in reversed(process_list.processes)
        if process.owner == interactive_session.username
    ]
    if not owned_processes:
        pytest.skip("the active session has no process owned by its current user")

    for process in owned_processes:
        dump = await interactive_session.process_dump(process.pid)
        if dump.data:
            assert isinstance(dump, models.sliverpb.ProcessDump)
            return

    pytest.fail("no owned process returned a non-empty memory dump")
