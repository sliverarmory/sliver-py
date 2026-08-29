from __future__ import annotations

import asyncio
import uuid
from contextlib import suppress

import pytest

from sliver import (
    GOARCH,
    GOOS,
    C2Endpoint,
    Client,
    EventType,
    ImplantSpec,
    JobProtocol,
    ResourceNotFoundError,
    Target,
    models,
)

from .conftest import (
    COMMAND_TIMEOUT,
    MTLSListener,
    _start_loopback_listener_with_retry,
    _stop_listener_job,
    _wait_for_job_removal,
    example_command,
    run_example_cli,
)
from .harness import E2ESettings, SliverServerHarness, retry_bind_conflicts

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.e2e_basic,
    pytest.mark.asyncio(loop_scope="session"),
]


async def test_server_version_matches_the_native_runner(
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
    sliver_client: Client,
) -> None:
    version = await asyncio.wait_for(
        sliver_client.version(timeout=COMMAND_TIMEOUT),
        timeout=COMMAND_TIMEOUT,
    )

    assert isinstance(version, models.clientpb.Version)
    assert version == e2e_harness.version
    assert version.os == e2e_settings.target_os
    assert version.arch == e2e_settings.target_arch


async def test_preferred_client_facade_owns_and_reconnects_its_channel(
    e2e_harness: SliverServerHarness,
) -> None:
    client = Client.from_config_file(e2e_harness.operator_config_path)
    assert not client.is_connected()

    async with client as connected:
        assert connected is client
        assert client.is_connected()
        assert await client.version(timeout=COMMAND_TIMEOUT) == e2e_harness.version

    assert not client.is_connected()
    await client.connect(timeout=COMMAND_TIMEOUT)
    assert client.is_connected()
    await client.aclose()
    assert not client.is_connected()


async def test_server_lists_the_generated_operator_as_a_pydantic_model(
    e2e_harness: SliverServerHarness,
    sliver_client: Client,
) -> None:
    operators = await sliver_client.operators(timeout=COMMAND_TIMEOUT)

    assert operators
    assert all(isinstance(item, models.clientpb.Operator) for item in operators)
    assert e2e_harness.operator_config is not None
    assert e2e_harness.operator_config.operator in {item.name for item in operators}


async def test_server_lists_implants_as_pydantic_models(
    sliver_client: Client,
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

    inventory = await sliver_client.inventory(timeout=COMMAND_TIMEOUT)
    assert inventory.version is not None
    assert inventory.sessions == sessions
    assert inventory.beacons == beacons
    assert all(isinstance(item, models.clientpb.Job) for item in inventory.jobs)
    assert all(
        isinstance(item, models.clientpb.Operator) for item in inventory.operators
    )


async def test_strict_client_lookup_distinguishes_missing_resources(
    sliver_client: Client,
) -> None:
    missing_session = str(uuid.uuid4())
    missing_beacon = str(uuid.uuid4())
    missing_job = 2_147_483_647

    assert await sliver_client.find_session(missing_session) is None
    assert await sliver_client.find_beacon(missing_beacon) is None
    assert await sliver_client.find_job(missing_job) is None
    with pytest.raises(ResourceNotFoundError):
        await sliver_client.get_session(missing_session)
    with pytest.raises(ResourceNotFoundError):
        await sliver_client.get_beacon(missing_beacon)
    with pytest.raises(ResourceNotFoundError):
        await sliver_client.get_job(missing_job)


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
    sliver_client: Client,
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
    assert JobProtocol(job.protocol.lower()) is JobProtocol.TCP
    assert (
        await sliver_client.job_by_port(
            mtls_listener.port,
            timeout=COMMAND_TIMEOUT,
        )
        == job
    )


async def test_http_listener_lifecycle_uses_the_command_aligned_api(
    sliver_client: Client,
) -> None:
    async def start(port: int) -> models.clientpb.ListenerJob:
        return await sliver_client.http(
            host="127.0.0.1",
            port=port,
            domain="localhost",
            enforce_otp=False,
            long_poll_timeout=1,
            long_poll_jitter=0,
            timeout=COMMAND_TIMEOUT,
        )

    port, listener = await _start_loopback_listener_with_retry(
        sliver_client,
        start,
    )
    assert isinstance(listener, models.clientpb.ListenerJob)
    try:
        job = await sliver_client.get_job(listener.job_id)
        assert job.port == port
        assert job.protocol == str(JobProtocol.TCP)
        assert await sliver_client.job_by_port(port) == job
    finally:
        await _stop_listener_job(sliver_client, listener.job_id)


async def test_profile_lifecycle_uses_typed_native_target_constants(
    sliver_client: Client,
    e2e_settings: E2ESettings,
    mtls_listener: MTLSListener,
) -> None:
    profile_name = f"e2e-profile-{uuid.uuid4().hex}"
    spec = ImplantSpec(
        target=Target(
            os=GOOS(e2e_settings.target_os),
            arch=GOARCH(e2e_settings.target_arch),
        ),
        c2=[C2Endpoint.from_url(mtls_listener.c2_url)],
    )
    profile = models.clientpb.ImplantProfile(
        name=profile_name,
        config=spec.to_implant_config(),
    )

    saved = await sliver_client.profiles_new(profile)
    assert saved.name == profile_name
    assert saved.config is not None
    try:
        profiles = await sliver_client.profiles()
        stored = next(item for item in profiles if item.name == profile_name)
        assert stored.config is not None
        assert stored.config.goos == e2e_settings.target_os
        assert stored.config.goarch == e2e_settings.target_arch
    finally:
        await sliver_client.profiles_rm(profile_name)

    assert profile_name not in {item.name for item in await sliver_client.profiles()}


async def test_website_content_lifecycle_uses_command_aligned_methods(
    sliver_client: Client,
) -> None:
    website_name = f"e2e-website-{uuid.uuid4().hex}"
    web_path = "/index.html"
    original = b"<h1>sliver-py original</h1>"
    updated = b"<h1>sliver-py updated</h1>"
    synchronized = b"<h1>sliver-py synchronized</h1>"
    created = False

    try:
        website = await sliver_client.add_website_content(
            website_name,
            web_path,
            "text/html",
            original,
        )
        created = True
        assert website.name == website_name
        assert website.contents[web_path].content == original

        website = await sliver_client.update_website_content(
            website_name,
            web_path,
            "text/html",
            updated,
        )
        assert website.contents[web_path].size == len(updated)
        assert website.contents[web_path].content_type == "text/html"
        assert website.contents[web_path].content == updated
        shown = await sliver_client.websites_show(website_name)
        assert shown.contents[web_path].size == len(updated)
        assert shown.contents[web_path].content_type == "text/html"
        assert shown.contents[web_path].content == updated

        desired = shown.model_copy(
            update={
                "contents": {
                    web_path: models.clientpb.WebContent(
                        path=web_path,
                        content_type="text/html",
                        content=synchronized,
                        size=len(synchronized),
                    )
                }
            }
        )
        website = await sliver_client.update_website(desired)
        assert website.contents[web_path].content == synchronized
        assert website.contents[web_path].size == len(synchronized)
        assert website_name in {item.name for item in await sliver_client.websites()}

        without_content = await sliver_client.websites_rm_content(
            website_name,
            [web_path],
        )
        assert web_path not in without_content.contents
    finally:
        if created:
            await sliver_client.websites_rm(website_name)

    assert website_name not in {item.name for item in await sliver_client.websites()}


async def test_canary_inventory_is_pydantic_only(sliver_client: Client) -> None:
    canaries = await sliver_client.canaries(timeout=COMMAND_TIMEOUT)
    assert all(isinstance(item, models.clientpb.DNSCanary) for item in canaries)


async def test_event_and_temporary_listener_examples_work_together(
    e2e_harness: SliverServerHarness,
    e2e_settings: E2ESettings,
    sliver_client: Client,
) -> None:
    event_command = example_command(
        e2e_harness,
        e2e_settings,
        "examples.watch_events",
        str(EventType.JOB_STARTED),
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
    direct_events = sliver_client.on(EventType.JOB_STARTED)
    direct_event_task = asyncio.create_task(anext(direct_events))
    listener_job_ids: list[int] = []
    listener_ports: list[int] = []
    try:
        # Sliver's event stream has no subscription acknowledgement. Publish
        # bounded, uniquely identifiable stimuli until the watcher observes
        # one rather than treating an unrelated operator connection as proof
        # that the stream is ready.
        for _attempt in range(5):
            if event_process.returncode is not None and direct_event_task.done():
                break

            async def run_listener(port: int) -> tuple[int, int]:
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
                if job_id <= 0 or "Stop succeeded: True" not in output:
                    raise RuntimeError(
                        "temporary listener example omitted its cleanup result"
                    )
                return port, job_id

            port, job_id = await retry_bind_conflicts(run_listener)
            listener_ports.append(port)
            listener_job_ids.append(job_id)
            await _wait_for_job_removal(sliver_client, job_id)
            await asyncio.sleep(0.25)

        if event_process.returncode is None or not direct_event_task.done():
            raise TimeoutError(
                "event consumers did not both observe a listener event"
            )

        stdout, stderr = await asyncio.wait_for(
            event_process.communicate(),
            timeout=COMMAND_TIMEOUT,
        )
        direct_event = await direct_event_task
    finally:
        if not direct_event_task.done():
            direct_event_task.cancel()
            with suppress(asyncio.CancelledError):
                await direct_event_task
        await direct_events.aclose()
        if event_process.returncode is None:
            with suppress(ProcessLookupError):
                event_process.kill()
            await asyncio.wait_for(event_process.communicate(), timeout=10)

    error = stderr.decode(errors="replace")[-8192:]
    assert event_process.returncode == 0, error
    event = models.clientpb.Event.model_validate_json(stdout)
    assert event.event_type == str(EventType.JOB_STARTED)
    assert event.job is not None
    assert event.job.id in listener_job_ids
    assert event.job.port in listener_ports
    assert direct_event.event_type == str(EventType.JOB_STARTED)
    assert direct_event.job is not None
    assert direct_event.job.id in listener_job_ids
    assert direct_event.job.port in listener_ports
    for job_id in listener_job_ids:
        assert await sliver_client.job_by_id(job_id) is None
