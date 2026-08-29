"""Small compatibility helpers shared by third-party example imports."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sliver import Client


def new_client(config_path: str | Path | None = None) -> Client:
    """Construct a client from a Sliver operator configuration file."""

    return Client.from_config_file(config_path)


@asynccontextmanager
async def connected_client(
    config_path: str | Path | None = None,
) -> AsyncIterator[Client]:
    """Connect a new client and always close its gRPC channel."""

    client = Client.from_config_file(config_path)
    async with client:
        yield client
