"""Run a loopback mTLS listener with managed cleanup."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from sliver import Client
from sliver.models.clientpb import ListenerJob


async def run_temporary_listener(
    client: Client,
    *,
    host: str = "127.0.0.1",
    port: int = 8888,
    duration: float = 60.0,
    timeout: int = 60,
) -> ListenerJob:
    """Run one mTLS listener for ``duration`` seconds, then stop it."""

    if duration < 0:
        raise ValueError("duration must not be negative")

    if hasattr(client, "temporary_mtls"):
        async with client.temporary_mtls(
            host=host,
            port=port,
            timeout=timeout,
        ) as listener:
            if listener.job_id <= 0:
                raise RuntimeError("Sliver did not return a listener job ID")
            await asyncio.sleep(duration)
        return listener

    # Compatibility for callers that copied the pre-facade example test double.
    listener = await client.start_mtls_listener(
        host=host,
        port=port,
        timeout=timeout,
    )
    try:
        await asyncio.sleep(duration)
    finally:
        stopped = await client.kill_job(listener.job_id, timeout=timeout)
        if stopped.id != listener.job_id or not stopped.success:
            raise RuntimeError(f"Sliver did not stop listener job {listener.job_id}")
    return listener


async def _run(args: argparse.Namespace) -> None:
    client = Client.from_config_file(args.config)
    async with client:
        listener = await run_temporary_listener(
            client,
            host=args.host,
            port=args.port,
            duration=args.duration,
            timeout=args.timeout,
        )

    print(f"Started and stopped job {listener.job_id}")
    print("Stop succeeded: True")


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
