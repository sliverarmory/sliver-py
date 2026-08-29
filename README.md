# SliverPy

SliverPy is an async Python client library for [Sliver](https://github.com/BishopFox/sliver). It automates operator interactions over Sliver's mutually authenticated gRPC API and keeps generated transport messages behind a public boundary made of [Pydantic](https://docs.pydantic.dev/) models, Python primitives, and normal containers. [See the project documentation for more details](https://sliverpy.readthedocs.io/).

The v0.1 API is generated from the Sliver definitions at the exact submodule commit pinned by this repository. The concise `Client` API follows Sliver's command names, while `client.rpc` provides typed Pydantic access to every RPC when a high-level method is not available.

Single-token commands retain their Sliver spelling (`runas`, `spawndll`,
`rev2self`); nested command paths are flattened in order (`profiles generate`
becomes `profiles_generate`).

[![SliverPy](https://github.com/moloch--/sliver-py/actions/workflows/autorelease.yml/badge.svg)](https://github.com/moloch--/sliver-py/actions/workflows/autorelease.yml)
[![Documentation Status](https://readthedocs.org/projects/sliverpy/badge/?version=latest)](https://sliverpy.readthedocs.io/en/latest/?badge=latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Install

Add the package to a uv-managed Python 3.10 or newer project:

```console
uv add sliver-py
```

Installation with pip remains supported:

```console
python -m pip install sliver-py
```

### Kali Linux / Fix OpenSSL Errors

[Python's TLS implementation](https://docs.python.org/3/library/ssl.html) may exhibit platform-specific behavior. If a pip-based installation encounters OpenSSL connection errors, reinstall gRPC Python from source. Depending on the distribution, this may also require GCC (for example, `build-essential`) and the OpenSSL development package:

```console
GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=True python -m pip install --force-reinstall --no-binary grpcio grpcio
```

## Quick start

`Client.from_config_file()` resolves an explicit path, then `SLIVER_CONFIG`,
then Sliver's default `~/.sliver-client/configs/default.cfg`. The client is an
async context manager, so connection and cleanup have one owner:

```python
import asyncio

from sliver import Client


async def main() -> None:
    async with Client.from_config_file() as client:
        inventory = await client.inventory()
        print(inventory.version)
        for session in inventory.sessions:
            print(session.id, session.name, session.remote_address)


asyncio.run(main())
```

The longer `SliverClient` and `SliverClientConfig` names remain available for
existing programs. New code should prefer `Client`, `OperatorConfig`, the async
context manager, command-aligned method names, and the typed enums and domain
models exported from `sliver`.

## Idiomatic generation

Human-facing models validate common workflows without exposing schema-shaped
configuration fields or magic strings:

```python
import asyncio
from pathlib import Path

from sliver import (
    C2Endpoint,
    Client,
    GOARCH,
    GOOS,
    ImplantSpec,
    OutputFormat,
    Target,
)


async def main() -> None:
    async with Client.from_config_file() as client:
        implant = await client.generate(
            ImplantSpec(
                target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
                c2=[C2Endpoint.mtls("c2.example.test")],
                output_format=OutputFormat.EXECUTABLE,
            ),
            name="web-server",
        )
        saved = implant.save(Path("artifacts") / implant.filename)
        print(saved)


asyncio.run(main())
```

`ImplantSpec`, `Target`, `C2Endpoint`, `BeaconOptions`, and `ShellcodeOptions`
convert to the generated Pydantic request models. `GeneratedImplant.save()`
uses exclusive creation by default so an existing artifact is not overwritten
silently.

Saved profiles use Sliver's command vocabulary as well:
`profiles_generate(profile_name)` and `profiles_stage(request)` return the same
rich `GeneratedImplant` result shape.

## Sessions, beacons, and events

Use `find_*()` when absence is expected, `get_*()` when it is an error, and
`use_*()` (or `use(model)`) to obtain an interactive wrapper:

```python
import asyncio

from sliver import Client, EventType


async def main() -> None:
    async with Client.from_config_file() as client:
        sessions = await client.sessions()
        if sessions:
            session = await client.use(sessions[0])
            listing = await session.ls()
            print(listing.path)

        connected = await client.collect_events(
            EventType.SESSION_CONNECTED,
            limit=1,
            timeout=30,
        )
        print(connected)


asyncio.run(main())
```

`client.events()` is the streaming form and accepts an `EventType`, a string,
or a collection of either. All subscriptions and interactive beacon commands
share one lazy event stream owned by the client. Subscriber buffers are
bounded; slow consumers should process or hand off events promptly. The broker
reconnects after an unexpected stream interruption, while each beacon command's
deadline remains authoritative. Closing the client stops subscriptions,
cancels pending task waits, and closes the channel in that order.

An `InteractiveBeacon` command queues a remote task and awaits its typed result.
On timeout or local cancellation, SliverPy cleans up the local waiter and asks
the server to cancel the task when supported. `InteractiveBeacon.close()` is
retained for compatibility, but a wrapper obtained from `Client` does not own
the shared dispatcher. It never terminates or removes the remote beacon.

The command-aligned lifecycle methods deliberately distinguish two operations:

- `await client.kill_beacon(beacon_id)` queues a command to terminate the
  beacon implant process.
- `await client.beacons_rm(beacon_id)` removes the server's beacon record without
  terminating a running implant.

Runnable, cross-platform E2E-tested programs for inventory, listeners, events,
implant generation, sessions, and beacons live in [`examples/`](examples/).

## Pydantic RPC escape hatch

Every public structured request and response is a concrete Pydantic class under
`sliver.models`. Model attributes use Python `snake_case`; original schema field
names remain accepted as validation aliases. When no high-level method exists,
use the connected client's `rpc` property:

```python
from sliver.models.clientpb import RenameReq

request = RenameReq(session_id="session-id", name="web-server")
await client.rpc.rename(request)
```

The RPC adapter validates the request model and returns the declared Pydantic
response model. Generated transport messages remain private. `rpc` is available
only while connected and raises `NotConnectedError` otherwise. The historical
`pydantic_stub` property and PascalCase RPC spellings are compatibility aliases.

## Errors

High-level failures use exceptions exported from `sliver`:

- `RPCError` normalizes gRPC transport failures and records the RPC operation,
  status, and details.
- `ResourceNotFoundError` distinguishes required `get_*()`/`use_*()` lookups
  from optional `find_*()` results.
- `CommandError` reports a command result whose Sliver response contains an
  error.
- `SliverTimeoutError` reports library-owned deadlines and is also a built-in
  `TimeoutError`.
- `CleanupError` collects failures while releasing an owned resource.
- `UnsupportedTargetError` reports a host that cannot be mapped to a supported
  `GOOS`/`GOARCH` pair.

See the [project documentation](https://sliverpy.rtfd.io/) for configuration,
domain models, enums, event/task semantics, the complete API, and the
compatibility policy.

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
uv run mypy --no-incremental typecheck tests/typecheck
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

The repository records an exact Sliver submodule commit so local generation and CI use the same API definitions. When intentionally updating for a release, advance the submodule on its configured branch, review and stage the resulting gitlink, then regenerate the private transport modules and concrete Pydantic modules:

```console
git submodule update --init --remote sliver
uv sync --frozen --group protobuf
uv run python scripts/protobufgen.py
```

When changing the handwritten client, session, beacon, configuration, or
interactive APIs, regenerate their source-derived type stubs as well:

```console
uv run python scripts/highlevelstubgen.py
```

CI checks all generated sources and stubs for freshness, then type-checks the
installed public surface with `Any` disallowed.

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
