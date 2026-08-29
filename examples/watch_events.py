"""Watch a bounded number of typed server events."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncGenerator, Sequence

from sliver import Client, EventType
from sliver.models.clientpb import Event


async def _collect_legacy_stream(
    stream: AsyncGenerator[Event, None],
    *,
    count: int,
    timeout: float,
) -> list[Event]:
    """Keep the original helper usable with older client-shaped test doubles."""

    async def receive() -> list[Event]:
        events: list[Event] = []
        async for event in stream:
            events.append(event)
            if len(events) == count:
                break
        return events

    try:
        return await asyncio.wait_for(receive(), timeout=timeout)
    finally:
        await stream.aclose()


async def collect_events(
    client: Client,
    event_types: EventType | str | Sequence[EventType | str] = (),
    *,
    count: int = 1,
    timeout: float = 60.0,
) -> list[Event]:
    """Collect a bounded set with the client's managed event subscription."""

    if count < 1:
        raise ValueError("count must be at least 1")
    if timeout <= 0:
        raise ValueError("timeout must be greater than 0")

    values = [event_types] if isinstance(event_types, str) else event_types
    selected = tuple(EventType(value) for value in values)
    if hasattr(client, "collect_events"):
        return await client.collect_events(
            *selected,
            limit=count,
            timeout=timeout,
        )

    # Compatibility for callers that copied the pre-facade example test double.
    stream = (
        client.on([str(event_type) for event_type in selected])
        if selected
        else client.events()
    )
    return await _collect_legacy_stream(
        stream,
        count=count,
        timeout=timeout,
    )


async def _run(args: argparse.Namespace) -> None:
    client = Client.from_config_file(args.config)
    async with client:
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
        type=EventType,
        choices=tuple(EventType),
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
