from __future__ import annotations

import asyncio

import pytest

from sliver import SliverClient, models

from .conftest import COMMAND_TIMEOUT, MTLSListener
from .harness import E2ESettings, SliverServerHarness

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
    assert version.major >= 1


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
