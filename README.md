# SliverPy

SliverPy is an async Python client library for [Sliver](https://github.com/BishopFox/sliver). It automates operator interactions over Sliver's mutually authenticated gRPC API and exposes descriptor-generated [Pydantic](https://docs.pydantic.dev/) models instead of generated protobuf messages at the public API. [See the project documentation for more details](https://sliverpy.readthedocs.io/).

The v0.1 API is generated from the Sliver protobuf definitions at the submodule commit pinned by this release. Not every Sliver feature has a high-level convenience method yet; public Pydantic-aware and raw generated gRPC stubs are available for advanced use.

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

## Pydantic models

Every top-level protobuf message and enum has a Pydantic counterpart at `sliver.models.<package>.<Type>`. Nested messages and enums remain attributes of their containing model, such as `models.sliverpb.SockTabEntry.SockAddr`. Model attributes and constructor arguments use Python `snake_case`; original protobuf field and JSON names remain accepted as validation aliases for migration.

```python
from sliver import models

# Preferred v0.1 spelling.
request = models.clientpb.RenameReq(
    session_id="session-id",
    name="web-server",
)

# Existing protobuf-shaped data is accepted at validation boundaries.
same_request = models.clientpb.RenameReq.model_validate(
    {"SessionID": "session-id", "Name": "web-server"}
)
assert same_request.session_id == request.session_id

# Explicit conversion is available when integrating with protobuf-only code.
protobuf_request = request.to_protobuf()
request_again = models.clientpb.RenameReq.from_protobuf(protobuf_request)

# Enum fields use generated IntEnum members, and nested messages use models.
implant_config = models.clientpb.ImplantConfig(
    goos="linux",
    goarch="amd64",
    format=models.clientpb.OutputFormat.EXECUTABLE,
    c2=[models.clientpb.ImplantC2(url="mtls://127.0.0.1:8888")],
    include_mtls=True,
)
```

After `SliverClient.connect()`, normal client and interactive calls convert model requests to protobuf and responses back to Pydantic automatically. Advanced callers can submit a model directly through the public converted RPC stub:

```python
await client.pydantic_stub.Rename(request)
```

If exact generated protobuf behavior is required, use the explicit raw escape hatch. Raw RPCs require raw protobuf requests and return raw protobuf responses. Both stubs are available only while the client is connected:

```python
from sliver.pb.clientpb import client_pb2

raw_request = client_pb2.RenameReq(
    SessionID="session-id",
    Name="web-server",
)
await client.raw_stub.Rename(raw_request)
```

See [Pydantic models and protobuf interoperability](https://sliverpy.readthedocs.io/en/latest/models.html) for namespaces, serialization, aliases, and conversion details.

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

### Updating protobufs

This should only be necessary when changes are made to Sliver's protobuf definitions. Update the submodule, sync the generator dependencies, then regenerate both the Python modules and `.pyi` type hints:

```console
git submodule update --init --remote sliver
uv sync --frozen --group protobuf
uv run python scripts/protobufgen.py
```

### Running tests

The integration tests require a running Sliver server, an operator configuration at `~/.sliver-client/configs/sliverpy.cfg`, and at least one connected beacon and session implant. Run the full pytest suite or select a marker:

- `uv run pytest`: all tests
- `uv run pytest -m client`: top-level client API tests
- `uv run pytest -m interactive`: interactive session tests

The managed end-to-end suite runs in GitHub Actions on native macOS/arm64,
Linux/amd64, and Windows/amd64 runners. Each job compiles the pinned Sliver
server, creates an isolated localhost operator, and executes generated session
and beacon implants before testing their APIs. These tests are skipped locally
unless explicitly enabled; see [`tests/e2e/README.md`](tests/e2e/README.md) for
the lifecycle, safety boundaries, and marker groups.
