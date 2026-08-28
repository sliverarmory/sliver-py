# SliverPy

SliverPy is an async Python client library for [Sliver](https://github.com/BishopFox/sliver). It automates operator interactions over Sliver's mutually authenticated gRPC API and exposes descriptor-generated [Pydantic](https://docs.pydantic.dev/) models instead of generated transport messages at the public API. [See the project documentation for more details](https://sliverpy.readthedocs.io/).

The v0.1 API is generated from the Sliver definitions at the exact submodule commit pinned by this repository. Not every Sliver RPC has a high-level convenience method yet; the Pydantic-only `pydantic_stub` remains available for advanced use.

[![SliverPy](https://github.com/moloch--/sliver-py/actions/workflows/autorelease.yml/badge.svg)](https://github.com/moloch--/sliver-py/actions/workflows/autorelease.yml)
[![Documentation Status](https://readthedocs.org/projects/sliverpy/badge/?version=latest)](https://sliverpy.readthedocs.io/en/latest/?badge=latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

### Install

Add the package to a uv-managed Python 3.10 or newer project:

```console
uv add sliver-py
```

Installation with pip remains supported:

```console
python -m pip install sliver-py
```

#### Kali Linux / Fix OpenSSL Errors

[Python's TLS implementation](https://docs.python.org/3/library/ssl.html) may exhibit platform-specific behavior. If a pip-based installation encounters OpenSSL connection errors, reinstall gRPC Python from source. Depending on the distribution, this may also require GCC (for example, `build-essential`) and the OpenSSL development package:

```console
GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=True python -m pip install --force-reinstall --no-binary grpcio grpcio
```

## Examples

For more examples and details, read the [project documentation](https://sliverpy.rtfd.io/).

#### Interact with Sessions

```python
#!/usr/bin/env python3

import asyncio
from pathlib import Path

from sliver import SliverClient, SliverClientConfig

DEFAULT_CONFIG = Path.home() / ".sliver-client" / "configs" / "default.cfg"


async def main() -> None:
    config = SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
    client = SliverClient(config)
    try:
        version = await client.connect()
        print(
            f"[*] Connected to Sliver "
            f"{version.major}.{version.minor}.{version.patch}"
        )

        sessions = await client.sessions()
        if not sessions:
            print("[*] No sessions")
            return

        print(f"[*] Interacting with session {sessions[0].name!r}")
        interaction = await client.interact_session(sessions[0].id)
        if interaction is None:
            print("[*] Session disconnected")
            return

        listing = await interaction.ls()
        print(f"[*] ls: {listing!r}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

`InteractiveSession.session` returns a defensive copy of the complete
`models.clientpb.Session` metadata model. Convenience properties such as
`session_id`, `name`, `hostname`, `os`, `arch`, and `pid` expose common fields.
The interaction shares the client's channel, so closing the client completes
its cleanup.

#### Interact with Beacons

```python
#!/usr/bin/env python3

import asyncio
from pathlib import Path

from sliver import SliverClient, SliverClientConfig

DEFAULT_CONFIG = Path.home() / ".sliver-client" / "configs" / "default.cfg"


async def main() -> None:
    config = SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
    client = SliverClient(config)
    interaction = None
    try:
        version = await client.connect()
        print(
            f"[*] Connected to Sliver "
            f"{version.major}.{version.minor}.{version.patch}"
        )

        beacons = await client.beacons()
        if not beacons:
            print("[*] No beacons")
            return

        print(f"[*] Interacting with beacon {beacons[0].name!r}")
        interaction = await client.interact_beacon(beacons[0].id)
        if interaction is None:
            print("[*] Beacon disappeared")
            return

        listing = await interaction.ls()
        print(f"[*] ls: {listing!r}")
    finally:
        if interaction is not None:
            await interaction.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Closing an `InteractiveBeacon` stops its local task-result watcher; it does not terminate or remove the remote beacon.
`InteractiveBeacon.beacon` returns a defensive copy of the complete
`models.clientpb.Beacon` metadata model, with matching scalar convenience
properties such as `beacon_id`, `name`, `hostname`, `os`, `arch`, and `pid`.

## Pydantic models

Every top-level Sliver API message and enum has a Pydantic counterpart at `sliver.models.<package>.<Type>`. Nested messages and enums remain attributes of their containing model, such as `models.sliverpb.SockTabEntry.SockAddr`, while map entries become normal dictionaries. Model attributes and constructor arguments use Python `snake_case`; original schema field names remain accepted as validation aliases.

```python
from sliver import models

# Preferred v0.1 spelling.
request = models.clientpb.RenameReq(
    session_id="session-id",
    name="web-server",
)

# Schema-shaped mappings are accepted at Pydantic validation boundaries.
same_request = models.clientpb.RenameReq.model_validate(
    {"SessionID": "session-id", "Name": "web-server"}
)
assert same_request.session_id == request.session_id

# Enum fields use generated IntEnum members, and nested messages use models.
implant_config = models.clientpb.ImplantConfig(
    goos="linux",
    goarch="amd64",
    format=models.clientpb.OutputFormat.EXECUTABLE,
    c2=[models.clientpb.ImplantC2(url="mtls://127.0.0.1:8888")],
    include_mtls=True,
)
```

Models support normal Pydantic validation and serialization methods, including `model_validate()`, `model_dump()`, `model_dump_json()`, and `model_json_schema()`. Repeated fields are lists, map fields are dictionaries, and enum fields use generated `IntEnum` members.

After `SliverClient.connect()`, every client, session, and beacon method accepts and returns only Pydantic models, standard Python containers, or primitive values. Advanced callers can invoke an RPC that lacks a high-level convenience method through the same Pydantic-only boundary:

```python
await client.pydantic_stub.Rename(request)
```

`pydantic_stub` is available only while the client is connected and validates each RPC's request model. The generated wire implementation is private: external callers neither pass nor receive generated transport messages.

See the [Pydantic model API](https://sliverpy.readthedocs.io/en/latest/models.html) for namespaces, serialization, aliases, nested types, field presence, and validation details.

## Development

SliverPy uses [uv](https://docs.astral.sh/uv/) for Python installation, dependency locking, virtual environments, and package builds. Clone the Sliver submodule and sync the locked development environment:

```console
git clone --recurse-submodules https://github.com/moloch--/sliver-py.git
cd sliver-py
uv sync --frozen
```

uv creates the project environment at `.venv`; editors such as VS Code can use `.venv/bin/python` as the interpreter. Run project tools through uv so manual activation is unnecessary:

```console
uv run ruff format .
uv run ruff check .
uv run pytest
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
uv build
```

When dependencies change, update `pyproject.toml` with `uv add` or `uv remove`, then commit the regenerated `uv.lock`. CI and release builds use `--frozen` or `--locked` to reject stale lockfiles.

### Docker/WSL2

A Dockerfile is included if you wish to develop inside a container. This may be preferable for development on any operating system to keep the dev environment isolated. Windows developers may choose to develop inside WSL2.

In either case, `scripts/sliver_install.sh` contains a modified version of the official Sliver installation script that does not create a `systemd` based service. After running this script, you may start a local Sliver server in your container or WSL2 instance by running:

`sudo /root/sliver-server daemon &`

Alternatively, you can still choose to set up an external Sliver instance to connect to via Sliver's [multi-player mode](https://github.com/BishopFox/sliver/wiki/Multiplayer-Mode). The `sliver_install` script is purely for local development convenience.

### Updating generated models

The repository records an exact Sliver submodule commit so local generation and CI use the same API definitions. When intentionally updating for a release, advance the submodule on its configured branch, review and stage the resulting gitlink, then regenerate the private transport modules and Pydantic model inputs:

```console
git submodule update --init --remote sliver
uv sync --frozen --group protobuf
uv run python scripts/protobufgen.py
```

### Running tests

The optional integration tests require a running Sliver server, an operator configuration selected with `SLIVER_CONFIG` (or `~/.sliver-client/configs/sliverpy.cfg`), and at least one connected beacon and session implant. Run the full pytest suite or select a marker:

- `uv run pytest`: all tests
- `uv run pytest -m client`: top-level client API tests
- `uv run pytest -m interactive`: interactive session tests

The managed end-to-end suite runs in GitHub Actions on native macOS/arm64,
Linux/amd64, and Windows/amd64 runners. Each job compiles the pinned Sliver
server, creates an isolated localhost operator, and executes generated session
and beacon implants before testing their APIs. These tests are skipped locally
unless explicitly enabled; see [`tests/e2e/README.md`](tests/e2e/README.md) for
the lifecycle, safety boundaries, and marker groups.
