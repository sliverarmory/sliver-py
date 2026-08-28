from __future__ import annotations

from pathlib import Path

import pytest

from examples.generate_implant import (
    build_implant_config,
    host_target,
    save_generated_implant,
)
from examples.temporary_listener import run_temporary_listener
from examples.watch_events import collect_events
from sliver import models


def test_host_target_uses_sliver_platform_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("platform.machine", lambda: "arm64")

    assert host_target() == ("darwin", "arm64")


def test_implant_config_uses_public_pydantic_models() -> None:
    config = build_implant_config(
        "mtls://127.0.0.1:8888",
        goos="linux",
        goarch="amd64",
        is_beacon=True,
    )

    assert isinstance(config, models.clientpb.ImplantConfig)
    assert config.is_beacon
    assert config.format is models.clientpb.OutputFormat.EXECUTABLE
    assert config.c2 == [
        models.clientpb.ImplantC2(priority=0, url="mtls://127.0.0.1:8888")
    ]


def test_generated_implant_is_saved_exclusively(tmp_path: Path) -> None:
    generated = models.clientpb.Generate(
        implant_name="EXAMPLE",
        file=models.commonpb.File(name="example", data=b"implant"),
    )
    destination = tmp_path / "nested" / "example"

    assert save_generated_implant(generated, destination) == destination
    assert destination.read_bytes() == b"implant"
    with pytest.raises(FileExistsError):
        save_generated_implant(generated, destination)


class _EventClient:
    def __init__(self) -> None:
        self.selected: list[str] | None = None

    def on(self, event_types: list[str]):
        self.selected = event_types
        return self._events()

    async def _events(self):
        yield models.clientpb.Event(event_type="job-started")


async def test_event_example_accepts_one_event_type_as_a_string() -> None:
    client = _EventClient()

    events = await collect_events(
        client,  # type: ignore[arg-type]
        "job-started",
        count=1,
        timeout=1,
    )

    assert client.selected == ["job-started"]
    assert events == [models.clientpb.Event(event_type="job-started")]


class _ListenerClient:
    async def start_mtls_listener(self, **_kwargs):
        return models.clientpb.ListenerJob(job_id=7)

    async def kill_job(self, job_id: int, **_kwargs):
        return models.clientpb.KillJob(id=job_id, success=False)


async def test_temporary_listener_reports_cleanup_failure() -> None:
    with pytest.raises(RuntimeError, match="did not stop listener job 7"):
        await run_temporary_listener(  # type: ignore[arg-type]
            _ListenerClient(),
            duration=0,
        )
