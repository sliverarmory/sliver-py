"""Watch a bounded number of server events."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from sliver import SliverClient, models

from .common import connected_client


async def collect_events(
    client: SliverClient,
    event_types: str | Sequence[str] = (),
    *,
    count: int = 1,
    timeout: float = 60.0,
) -> list[models.clientpb.Event]:
    """Collect at most ``count`` matching events within an overall timeout."""

    if count < 1:
        raise ValueError("count must be at least 1")
    if timeout <= 0:
        raise ValueError("timeout must be greater than 0")

    selected = [event_types] if isinstance(event_types, str) else list(event_types)
    stream = client.on(selected) if selected else client.events()

    async def receive() -> list[models.clientpb.Event]:
        events: list[models.clientpb.Event] = []
        iterator = stream.__aiter__()
        events.append(await anext(iterator))
        if len(events) == count:
            return events
        async for event in iterator:
            events.append(event)
            if len(events) == count:
                break
        return events

    try:
        return await asyncio.wait_for(receive(), timeout=timeout)
    finally:
        await stream.aclose()


async def _run(args: argparse.Namespace) -> None:
    async with connected_client(args.config) as client:
        events = await collect_events(
            client,
            args.event_types,
            count=args.count,
            timeout=args.timeout,
        )
        for event in events:
            print(
                event.model_dump_json(
                    indent=2,
                    exclude_none=True,
                    exclude_defaults=True,
                ),
                flush=True,
            )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "event_types",
        nargs="*",
        help="event types such as session-connected or job-started",
    )
    parser.add_argument("--config", help="operator config (or set SLIVER_CONFIG)")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args(argv)
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
