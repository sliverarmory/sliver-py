import pytest
import pytest_asyncio

from sliver import SliverClient
from sliver.session import InteractiveSession

from .test_client import sliver_client, sliverpy_random_name


@pytest_asyncio.fixture(scope="function")
async def session_zero(sliver_client: SliverClient) -> InteractiveSession:
    sessions = await sliver_client.sessions()
    return await sliver_client.interact_session(sessions[0].ID)

@pytest.mark.asyncio
async def test_ping(session_zero: InteractiveSession):
    assert await session_zero.ping()


@pytest.mark.asyncio
async def test_ps(session_zero: InteractiveSession):
    assert await session_zero.ps()


@pytest.mark.asyncio
async def test_ifconfig(session_zero: InteractiveSession):
    assert await session_zero.ifconfig()


@pytest.mark.asyncio
async def test_netstat(session_zero: InteractiveSession):
    assert await session_zero.netstat(True, True, True, True, True)


@pytest.mark.asyncio
async def test_pwd(session_zero: InteractiveSession):
    assert await session_zero.pwd()


@pytest.mark.asyncio
async def test_ls(session_zero: InteractiveSession):
    assert await session_zero.ls()


@pytest.mark.asyncio
async def test_cd(session_zero: InteractiveSession):
    assert await session_zero.cd(".")


@pytest.mark.asyncio
async def test_mkdir(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.mkdir(sliverpy_random_name)


@pytest.mark.asyncio
async def test_upload(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.upload(sliverpy_random_name + "/sliverpy.txt", b"sliverpy")


@pytest.mark.asyncio
async def test_download(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.download(sliverpy_random_name, True)


@pytest.mark.asyncio
async def test_rm(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.rm(sliverpy_random_name, recursive=True, force=True)


@pytest.mark.asyncio
async def test_set_env(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.set_env("SLIVERPY_TEST", sliverpy_random_name)


@pytest.mark.asyncio
async def test_get_env(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.get_env(sliverpy_random_name)


@pytest.mark.asyncio
async def test_unset_env(session_zero: InteractiveSession, sliverpy_random_name: str):
    assert await session_zero.unset_env(sliverpy_random_name)


@pytest.mark.asyncio
async def test_screenshot(session_zero: InteractiveSession):
    assert await session_zero.screenshot()


@pytest.mark.asyncio
async def test_process_dump(session_zero: InteractiveSession):
    procs = await session_zero.ps()
    found_process = False
    for proc in reversed(procs):
        if proc.Owner == session_zero.username:
            dump = await session_zero.process_dump(proc.Pid)
            if len(dump.Data) > 0:
                found_process = True
                break
    assert found_process

