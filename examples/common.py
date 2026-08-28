"""Shared connection helpers for the runnable examples."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sliver import SliverClient, SliverClientConfig

DEFAULT_CONFIG_PATH = Path("~/.sliver-client/configs/default.cfg").expanduser()


def resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Resolve an explicit config, ``SLIVER_CONFIG``, or the default path."""

    if config_path is not None:
        return Path(config_path).expanduser()
    configured = os.environ.get("SLIVER_CONFIG")
    return Path(configured).expanduser() if configured else DEFAULT_CONFIG_PATH


def new_client(config_path: str | Path | None = None) -> SliverClient:
    """Construct a client from a Sliver operator configuration file."""

    config = SliverClientConfig.parse_config_file(resolve_config_path(config_path))
    return SliverClient(config)


@asynccontextmanager
async def connected_client(
    config_path: str | Path | None = None,
) -> AsyncIterator[SliverClient]:
    """Connect a new client and always close its gRPC channel."""

    client = new_client(config_path)
    try:
        await client.connect()
        yield client
    finally:
        await client.close()


def require_success(result: object) -> None:
    """Raise when an interactive command reports a Sliver-side error."""

    response = getattr(result, "response", None)
    error = getattr(response, "err", "")
    if error:
        raise RuntimeError(error)
