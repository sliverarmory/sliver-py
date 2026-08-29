"""List common server resources as public Pydantic models."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from sliver import Client, Inventory


async def collect_inventory(
    client: Client,
    *,
    timeout: int = 60,
) -> Inventory:
    """Collect common server resources from an already-connected client."""

    return await client.inventory(timeout=timeout)


def format_inventory(inventory: Inventory) -> str:
    """Render an inventory snapshot without exposing operator credentials."""

    version = inventory.version
    lines = [
        f"Sliver {version.major}.{version.minor}.{version.patch} "
        f"on {version.os}/{version.arch}",
        "",
        f"Sessions ({len(inventory.sessions)})",
    ]
    lines.extend(
        f"{item.id} {item.name} {item.username}@{item.hostname} "
        f"{item.os}/{item.arch} {item.remote_address}"
        for item in inventory.sessions
    )
    lines.extend(("", f"Beacons ({len(inventory.beacons)})"))
    lines.extend(
        f"{item.id} {item.name} {item.username}@{item.hostname} "
        f"{item.os}/{item.arch} {item.remote_address}"
        for item in inventory.beacons
    )
    lines.extend(("", f"Jobs ({len(inventory.jobs)})"))
    lines.extend(
        f"{item.id} {item.protocol} {item.name} port={item.port}"
        for item in inventory.jobs
    )
    lines.extend(("", f"Operators ({len(inventory.operators)})"))
    lines.extend(
        f"{item.name} {'online' if item.online else 'offline'}"
        for item in inventory.operators
    )
    return "\n".join(lines)


async def _run(config: str | None, timeout: int) -> None:
    client = Client.from_config_file(config)
    async with client:
        print(format_inventory(await collect_inventory(client, timeout=timeout)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="operator config (or set SLIVER_CONFIG)")
    parser.add_argument("--timeout", type=int, default=60, help="RPC timeout")
    args = parser.parse_args(argv)
    asyncio.run(_run(args.config, args.timeout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
