"""Start a loopback mTLS listener temporarily and always stop its job."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from sliver import SliverClient
from sliver.models.clientpb import KillJob, ListenerJob

from .common import connected_client


@dataclass(frozen=True, slots=True)
class TemporaryListenerResult:
    """The public models returned while starting and stopping the listener."""

    started: ListenerJob
    stopped: KillJob


async def run_temporary_listener(
    client: SliverClient,
    *,
    host: str = "127.0.0.1",
    port: int = 8888,
    duration: float = 60.0,
    timeout: int = 60,
) -> TemporaryListenerResult:
    """Run one mTLS listener for ``duration`` seconds, then stop it."""

    if duration < 0:
        raise ValueError("duration must not be negative")
    started = await client.start_mtls_listener(host=host, port=port, timeout=timeout)
    if started.job_id <= 0:
        raise RuntimeError("Sliver did not return a listener job ID")
    try:
        await asyncio.sleep(duration)
    finally:
        stopped = await client.kill_job(started.job_id, timeout=timeout)
        if stopped.id != started.job_id or not stopped.success:
            raise RuntimeError(f"Sliver did not stop listener job {started.job_id}")
    return TemporaryListenerResult(started, stopped)


async def _run(args: argparse.Namespace) -> None:
    async with connected_client(args.config) as client:
        result = await run_temporary_listener(
            client,
            host=args.host,
            port=args.port,
            duration=args.duration,
            timeout=args.timeout,
        )
    print(f"Started and stopped job {result.started.job_id}")
    print(f"Stop succeeded: {result.stopped.success}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="operator config (or set SLIVER_CONFIG)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args(argv)
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
