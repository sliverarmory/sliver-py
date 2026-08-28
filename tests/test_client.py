from __future__ import annotations

import os
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.client]

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
    InteractiveBeacon,
    InteractiveSession,
    SliverClient,
    SliverClientConfig,
    models,
)


def _random_name() -> str:
    return f"sliver-pytest-{secrets.token_hex(8)}"


def _random_port() -> int:
    return 20_000 + secrets.randbelow(20_000)


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


@pytest.fixture(scope="module")
def implant_config() -> models.clientpb.ImplantConfig:
    return models.clientpb.ImplantConfig(
        is_beacon=False,
        goarch="amd64",
        goos="linux",
        format=models.clientpb.OutputFormat.EXECUTABLE,
        obfuscate_symbols=False,
        c2=[
            models.clientpb.ImplantC2(
                priority=0,
                url="http://localhost:80",
            )
        ],
    )


@pytest.fixture(scope="module")
def data_dir() -> Path:
    return Path(__file__).parent / "data"


async def test_client_version_returns_a_pydantic_model(
    sliver_client: SliverClient,
) -> None:
    version = await sliver_client.version()

    assert isinstance(version, models.clientpb.Version)


async def test_client_lists_operators_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    operators = await sliver_client.operators()

    assert isinstance(operators, list)
    assert all(isinstance(operator, models.clientpb.Operator) for operator in operators)


async def test_client_lists_beacons_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    beacons = await sliver_client.beacons()

    assert isinstance(beacons, list)
    assert all(isinstance(beacon, models.clientpb.Beacon) for beacon in beacons)


async def test_client_resolves_and_renames_a_beacon(
    sliver_client: SliverClient,
) -> None:
    beacons = await sliver_client.beacons()
    if not beacons:
        pytest.skip("the Sliver server has no active beacons")

    beacon = beacons[0]
    original_name = beacon.name
    updated_name = _random_name()
    await sliver_client.rename_beacon(beacon.id, updated_name)
    try:
        updated = await sliver_client.beacon_by_id(beacon.id)
        assert isinstance(updated, models.clientpb.Beacon)
        assert updated.name == updated_name
    finally:
        await sliver_client.rename_beacon(beacon.id, original_name)


async def test_client_lists_sessions_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    sessions = await sliver_client.sessions()

    assert isinstance(sessions, list)
    assert all(isinstance(session, models.clientpb.Session) for session in sessions)


async def test_client_resolves_and_renames_a_session(
    sliver_client: SliverClient,
) -> None:
    sessions = await sliver_client.sessions()
    if not sessions:
        pytest.skip("the Sliver server has no active sessions")

    session = sessions[0]
    original_name = session.name
    updated_name = _random_name()
    await sliver_client.rename_session(session.id, updated_name)
    try:
        updated = await sliver_client.session_by_id(session.id)
        assert isinstance(updated, models.clientpb.Session)
        assert updated.name == updated_name
    finally:
        await sliver_client.rename_session(session.id, original_name)


async def test_client_lists_implant_builds_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    builds = await sliver_client.implant_builds()

    assert isinstance(builds, dict)
    assert all(
        isinstance(config, models.clientpb.ImplantConfig) for config in builds.values()
    )


async def test_client_generates_regenerates_and_deletes_an_implant_build(
    sliver_client: SliverClient,
    implant_config: models.clientpb.ImplantConfig,
) -> None:
    generated = await sliver_client.generate_implant(implant_config)
    assert isinstance(generated, models.clientpb.Generate)
    assert generated.implant_name

    try:
        regenerated = await sliver_client.regenerate_implant(
            generated.implant_name,
            timeout=360,
        )
        assert isinstance(regenerated, models.clientpb.Generate)
        assert generated.implant_name in await sliver_client.implant_builds()
    finally:
        await sliver_client.delete_implant_build(generated.implant_name)

    assert generated.implant_name not in await sliver_client.implant_builds()


async def test_client_saves_lists_and_deletes_a_pydantic_implant_profile(
    sliver_client: SliverClient,
    implant_config: models.clientpb.ImplantConfig,
) -> None:
    profile_name = _random_name()
    profile = models.clientpb.ImplantProfile(
        name=profile_name,
        config=implant_config,
    )

    saved = await sliver_client.save_implant_profile(profile)
    assert isinstance(saved, models.clientpb.ImplantProfile)
    assert saved.name == profile_name
    try:
        profiles = await sliver_client.implant_profiles()
        assert all(
            isinstance(item, models.clientpb.ImplantProfile) for item in profiles
        )
        assert profile_name in {item.name for item in profiles}
    finally:
        await sliver_client.delete_implant_profile(profile_name)

    assert profile_name not in {
        item.name for item in await sliver_client.implant_profiles()
    }


async def test_client_lists_jobs_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    jobs = await sliver_client.jobs()

    assert isinstance(jobs, list)
    assert all(isinstance(job, models.clientpb.Job) for job in jobs)


async def test_client_resolves_jobs_by_id_and_port(
    sliver_client: SliverClient,
) -> None:
    jobs = await sliver_client.jobs()
    if not jobs:
        pytest.skip("the Sliver server has no active jobs")

    job = jobs[0]
    assert await sliver_client.job_by_id(job.id) == job
    assert await sliver_client.job_by_port(job.port) == job


async def test_client_starts_and_stops_an_http_listener(
    sliver_client: SliverClient,
) -> None:
    listener = await sliver_client.start_http_listener(port=_random_port())
    try:
        assert isinstance(listener, models.clientpb.ListenerJob)
        assert listener.job_id > 0
    finally:
        stopped = await sliver_client.kill_job(listener.job_id)

    assert isinstance(stopped, models.clientpb.KillJob)
    assert stopped.success


async def test_client_starts_and_stops_an_https_listener(
    sliver_client: SliverClient,
) -> None:
    listener = await sliver_client.start_https_listener(port=_random_port())
    try:
        assert isinstance(listener, models.clientpb.ListenerJob)
        assert listener.job_id > 0
    finally:
        stopped = await sliver_client.kill_job(listener.job_id)

    assert isinstance(stopped, models.clientpb.KillJob)
    assert stopped.success


async def test_client_starts_and_stops_an_mtls_listener(
    sliver_client: SliverClient,
) -> None:
    listener = await sliver_client.start_mtls_listener(port=_random_port())
    try:
        assert isinstance(listener, models.clientpb.ListenerJob)
        assert listener.job_id > 0
    finally:
        stopped = await sliver_client.kill_job(listener.job_id)

    assert isinstance(stopped, models.clientpb.KillJob)
    assert stopped.success


async def test_client_starts_and_stops_a_dns_listener(
    sliver_client: SliverClient,
) -> None:
    listener = await sliver_client.start_dns_listener(
        domains=["sliverpy.local"],
        port=_random_port(),
    )
    try:
        assert isinstance(listener, models.clientpb.ListenerJob)
        assert listener.job_id > 0
    finally:
        stopped = await sliver_client.kill_job(listener.job_id)

    assert isinstance(stopped, models.clientpb.KillJob)
    assert stopped.success


async def test_client_starts_and_stops_a_tcp_stager_listener(
    sliver_client: SliverClient,
) -> None:
    listener = await sliver_client.start_tcp_stager_listener(
        "0.0.0.0",
        _random_port(),
        b"sliver-pytest",
    )
    try:
        assert isinstance(listener, models.clientpb.StagerListener)
        assert listener.job_id > 0
    finally:
        stopped = await sliver_client.kill_job(listener.job_id)

    assert isinstance(stopped, models.clientpb.KillJob)
    assert stopped.success


async def test_client_generates_a_wireguard_ip(
    sliver_client: SliverClient,
) -> None:
    address = await sliver_client.generate_wg_ip()

    assert isinstance(address, models.clientpb.UniqueWGIP)
    assert address.ip


async def test_client_generates_a_wireguard_client_config(
    sliver_client: SliverClient,
) -> None:
    config = await sliver_client.generate_wg_client_config()

    assert isinstance(config, models.clientpb.WGClientConfig)
    assert config.client_ip


async def test_client_lists_dns_canaries_as_pydantic_models(
    sliver_client: SliverClient,
) -> None:
    canaries = await sliver_client.canaries()

    assert isinstance(canaries, list)
    assert all(isinstance(canary, models.clientpb.DNSCanary) for canary in canaries)


async def test_client_generates_shellcode_from_a_pe_file(
    sliver_client: SliverClient,
    data_dir: Path,
) -> None:
    executable = (data_dir / "test_write.exe").read_bytes()
    shellcode = await sliver_client.shellcode(executable, "Main")

    assert isinstance(shellcode, models.clientpb.ShellcodeRDI)
    assert shellcode.data


async def test_client_creates_an_interactive_session_wrapper(
    sliver_client: SliverClient,
) -> None:
    sessions = await sliver_client.sessions()
    if not sessions:
        pytest.skip("the Sliver server has no active sessions")

    session = await sliver_client.interact_session(sessions[0].id)
    assert isinstance(session, InteractiveSession)


async def test_client_creates_an_interactive_beacon_wrapper(
    sliver_client: SliverClient,
) -> None:
    beacons = await sliver_client.beacons()
    if not beacons:
        pytest.skip("the Sliver server has no active beacons")

    beacon = await sliver_client.interact_beacon(beacons[0].id)
    assert isinstance(beacon, InteractiveBeacon)


async def test_client_manages_a_website_content_lifecycle(
    sliver_client: SliverClient,
    data_dir: Path,
) -> None:
    website_name = _random_name()
    web_path = "index.html"
    original_content = (data_dir / "website.html").read_bytes()
    updated_content = (data_dir / "website_update.html").read_bytes()
    created = False

    try:
        website = await sliver_client.add_website_content(
            website_name,
            web_path,
            "text/html",
            original_content,
        )
        created = True
        assert isinstance(website, models.clientpb.Website)

        updated = await sliver_client.update_website_content(
            website_name,
            web_path,
            "text/html",
            updated_content,
        )
        assert isinstance(updated, models.clientpb.Website)
        fetched = await sliver_client.website(website_name)
        assert isinstance(fetched, models.clientpb.Website)
        assert web_path in fetched.contents
        assert website_name in {item.name for item in await sliver_client.websites()}

        without_content = await sliver_client.remove_website_content(
            website_name,
            [web_path],
        )
        assert isinstance(without_content, models.clientpb.Website)
    finally:
        if created:
            await sliver_client.remove_website(website_name)

    assert website_name not in {item.name for item in await sliver_client.websites()}
