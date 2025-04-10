import os
from pathlib import Path

import pytest
import pytest_asyncio
import pdb

from sliver import SliverClient, SliverClientConfig
from sliver.pb.clientpb.client_pb2 import (
    ImplantC2,
    ImplantConfig,
    ImplantProfile,
    OutputFormat,
    StageProtocol,
)

@pytest_asyncio.fixture(scope="function")
async def sliver_client() -> SliverClient:
    CONFIG_PATH = Path("~/.sliver-client/configs/sliverpy.cfg").expanduser()
    config = SliverClientConfig.parse_config_file(CONFIG_PATH)
    client = SliverClient(config)
    await client.connect()
    return client


@pytest_asyncio.fixture(scope="function")
async def implant_config() -> ImplantConfig:
    return ImplantConfig(
        IsBeacon=False,
        GOARCH="amd64",
        GOOS="linux",
        Format=OutputFormat.EXECUTABLE,
        ObfuscateSymbols=False,
        C2=[ImplantC2(Priority=0, URL="http://localhost:80")],
        HTTPC2ConfigName="default"
    )


@pytest_asyncio.fixture(scope="module")
def sliverpy_random_name() -> str:
    return "sliver-pytest-" + os.urandom(8).hex()


@pytest_asyncio.fixture(scope="function")
def data_dir() -> Path:
    return Path(__file__).parent / "data"

@pytest.mark.asyncio
async def test_client_can_get_version(sliver_client):
    assert await sliver_client.version()


@pytest.mark.asyncio
async def test_client_can_list_operators(sliver_client):
    assert await sliver_client.operators()


@pytest.mark.asyncio
async def test_client_can_list_beacons(sliver_client):
    assert await sliver_client.beacons()

@pytest.mark.asyncio
async def test_client_can_list_beacons_by_id(sliver_client):
    beacons = await sliver_client.beacons()
    assert await sliver_client.beacon_by_id(beacons[0].ID)


@pytest.mark.asyncio
async def test_client_can_rename_beacon(sliver_client):
    beacons = await sliver_client.beacons()
    beacon_name = beacons[0].Name
    beacon_id = beacons[0].ID
    await sliver_client.rename_beacon(beacon_id, "sliver-pytest")

    beacon = await sliver_client.beacon_by_id(beacon_id)
    assert beacon.Name == "sliver-pytest"

    await sliver_client.rename_beacon(beacon.ID, beacon_name)


@pytest.mark.asyncio
async def test_client_can_list_sessions(sliver_client):
    assert await sliver_client.sessions()


@pytest.mark.asyncio
async def test_client_can_list_sessions_by_id(sliver_client):
    sessions = await sliver_client.sessions()
    assert await sliver_client.session_by_id(sessions[0].ID)


@pytest.mark.asyncio
async def test_client_can_rename_session(sliver_client):
    sessions = await sliver_client.sessions()
    session_name = sessions[0].Name
    session_id = sessions[0].ID
    await sliver_client.rename_session(session_id, "sliver-pytest2")

    session = await sliver_client.session_by_id(session_id)
    assert session.Name == "sliver-pytest2"

    await sliver_client.rename_session(session.ID, session_name)


@pytest.mark.asyncio
async def test_client_can_list_implant_builds(sliver_client):
    assert await sliver_client.implant_builds()

@pytest.mark.asyncio
async def test_client_can_generate_implant(sliver_client, implant_config):
    assert await sliver_client.generate_implant("sliverpy-session", implant_config)

@pytest.mark.asyncio
async def test_client_can_regenerate_implant(sliver_client, implant_config):
    assert await sliver_client.regenerate_implant("sliverpy-session")


@pytest.mark.asyncio
async def test_client_can_save_implant_profiles(sliver_client, implant_config, sliverpy_random_name):
    implant_profile = ImplantProfile(Name=sliverpy_random_name, Config=implant_config)
    assert await sliver_client.save_implant_profile(implant_profile)


@pytest.mark.asyncio
async def test_client_can_list_implant_profiles(sliver_client, sliverpy_random_name):
    assert sliverpy_random_name in [profile.Name for profile in await sliver_client.implant_profiles()]


@pytest.mark.asyncio
async def test_client_can_delete_implant_profiles(sliver_client, sliverpy_random_name):
    await sliver_client.delete_implant_profile(sliverpy_random_name)
    assert sliverpy_random_name not in [profile.Name for profile in await sliver_client.implant_profiles()]


@pytest.mark.asyncio
async def test_client_can_delete_implant_builds(sliver_client, implant_config):
    await sliver_client.delete_implant_build("sliverpy-session")
    assert "sliverpy-session" not in [build for build in await sliver_client.implant_builds()]

@pytest.mark.asyncio
async def test_client_can_list_jobs(sliver_client):
    assert await sliver_client.jobs()


@pytest.mark.asyncio
async def test_client_can_get_job_by_id(sliver_client):
    jobs = await sliver_client.jobs()
    assert await sliver_client.job_by_id(jobs[0].ID)


@pytest.mark.asyncio
async def test_client_can_get_job_by_port(sliver_client):
    assert await sliver_client.job_by_port(80)

@pytest.mark.asyncio
async def test_client_can_start_http_listener(sliver_client):
    assert await sliver_client.start_http_listener(port=8123)


@pytest.mark.asyncio
async def test_client_can_start_https_listener(sliver_client):
    assert await sliver_client.start_https_listener(port=8124)


@pytest.mark.asyncio
async def test_client_can_start_dns_listener(sliver_client):
    assert await sliver_client.start_dns_listener(port=8125, domains=["sliverpy.local"])


@pytest.mark.asyncio
async def test_client_can_start_mtls_listener(sliver_client):
    assert await sliver_client.start_mtls_listener(port=8126)

@pytest.mark.asyncio
async def test_client_can_start_tcp_stager_listener(sliver_client):
    assert await sliver_client.start_tcp_stager_listener("0.0.0.0", 9000, b"sliver-pytest")


@pytest.mark.asyncio
async def test_client_can_kill_jobs(sliver_client):
    jobs = await sliver_client.jobs()
    for job in jobs:
        if job.Port != 80 and job.Port != 31337:
            await sliver_client.kill_job(job.ID)
    assert len(await sliver_client.jobs()) == 2


@pytest.mark.asyncio
async def test_client_can_generate_wireguard_ip(sliver_client):
    assert await sliver_client.generate_wg_ip()

''' Wireguard is broken server side, removing for now
# @pytest.mark.skip(reason="Something is wrong with killing WG listeners on the server")
@pytest.mark.asyncio
async def test_client_can_start_wg_listener(sliver_client):
    ip = await sliver_client.generate_wg_ip()
    assert await sliver_client.start_wg_listener(ip.IP, "1.2.3.4", 5353, 8889, 1338)
'''

@pytest.mark.asyncio
async def test_client_can_generate_wg_client_config(sliver_client):
    assert await sliver_client.generate_wg_client_config()


@pytest.mark.asyncio
async def test_client_can_generate_donut_shellcode(sliver_client, data_dir):
    dll_data = Path(data_dir / "test_write.exe").read_bytes()
    assert await sliver_client.shellcode(dll_data, "Main")


@pytest.mark.asyncio
async def test_client_can_interact_with_session(sliver_client):
    sessions = await sliver_client.sessions()
    session = sessions[0]
    assert await sliver_client.interact_session(session.ID)


@pytest.mark.asyncio
async def test_client_can_interact_with_beacon(sliver_client):
    beacons = await sliver_client.beacons()
    beacon = beacons[0]
    assert await sliver_client.interact_beacon(beacon.ID)


@pytest.mark.asyncio
async def test_client_can_add_website_content(sliver_client, data_dir):
    html_content = Path(data_dir / "website.html").read_bytes()
    assert await sliver_client.add_website_content(
        "sliverpy-test", "sliverpy", "test/html", html_content
    )


@pytest.mark.asyncio
async def test_client_can_update_website_content(sliver_client, data_dir):
    html_content = Path(data_dir / "website_update.html").read_bytes()
    assert await sliver_client.add_website_content(
        "sliverpy-test", "sliverpy", "test/html", html_content
    )

@pytest.mark.asyncio
async def test_client_can_list_websites(sliver_client):
    assert "sliverpy-test" in [website.Name for website in await sliver_client.websites()]


@pytest.mark.asyncio
async def test_client_can_remove_website_content(sliver_client):
    assert await sliver_client.remove_website_content("sliverpy-test", ["sliverpy"])

@pytest.mark.asyncio
async def test_client_can_remove_website(sliver_client):
    await sliver_client.remove_website("sliverpy-test")
    assert "sliverpy-test" not in [website.Name for website in await sliver_client.websites()]
