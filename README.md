# SliverPy

SliverPy is an async Python client library for [Sliver](https://github.com/BishopFox/sliver). It automates operator interactions over Sliver's mutually authenticated gRPC API and exposes descriptor-generated [Pydantic](https://docs.pydantic.dev/) models instead of generated protobuf messages at the public API. [See the project documentation for more details](https://sliverpy.readthedocs.io/).

The v0.1 API targets the current Sliver `master` protobuf definitions. Not every Sliver feature has a high-level convenience method yet; the Pydantic-aware RPC stub and raw generated gRPC stub are available for advanced use.

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

[Python's TLS implementation](https://docs.python.org/3/library/ssl.html) may exhibit platform specific behavoir, if you encounter OpenSSL connection errors you may need to re-install the gRPC Python library from source. This issue is known to affect recent versions of Kali Linux. To fix the issue use the following command to re-install gRPC from source, note depending on your distribution you may also need to install gcc (i.e. `build-essential`) and the development package for OpenSSL:

`GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=True pip install --use-pep517 --force-reinstall grpcio`

## Examples

For more examples and details please read the [project documentation](http://sliverpy.rtfd.io/).

#### Interact with Sessions

```python
#!/usr/bin/env python3

import os
import asyncio
from sliver import SliverClientConfig, SliverClient

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sliver-client", "configs")
DEFAULT_CONFIG = os.path.join(CONFIG_DIR, "default.cfg")

async def main():
    config = SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
    client = SliverClient(config)
    print('[*] Connected to server ...')
    await client.connect()
    sessions = await client.sessions()
    print('[*] Sessions: %r' % sessions)
    if len(sessions):
        print(f'[*] Interacting with session {sessions[0].name!r}')
        interact = await client.interact_session(sessions[0].id)
        ls = await interact.ls()
        print('[*] ls: %r' % ls)

if __name__ == '__main__':
    asyncio.run(main())
```

#### Interact with Beacons

```python
#!/usr/bin/env python3

import os
import asyncio
from sliver import SliverClientConfig, SliverClient

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".sliver-client", "configs")
DEFAULT_CONFIG = os.path.join(CONFIG_DIR, "default.cfg")

async def main():
    config = SliverClientConfig.parse_config_file(DEFAULT_CONFIG)
    client = SliverClient(config)
    print('[*] Connected to server ...')
    await client.connect()
    version = await client.version()
    print('[*] Server version: %s' % version)

    beacons = await client.beacons()
    print('[*] Beacons: %r' % beacons)
    if len(beacons):
        print(f'[*] Interacting with beacon: {beacons[0].name!r}')
        interact = await client.interact_beacon(beacons[0].id)
        ls = await interact.ls()
        print('[*] ls: %r' % ls)

if __name__ == '__main__':
    asyncio.run(main())
```

## Pydantic models

Every protobuf message has a Pydantic counterpart at `sliver.models.<package>.<Message>`. Model attributes and constructor arguments use Python `snake_case`; the original protobuf field names remain accepted as validation aliases for migration and wire-format interoperability.

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
```

After `SliverClient.connect()`, normal client and interactive calls convert model requests to protobuf and responses back to Pydantic automatically. Advanced callers can submit a model directly through the converted RPC stub:

```python
await client._stub.Rename(request)
```

If exact generated protobuf behavior is required, use the explicit raw escape hatch. Raw RPCs require raw protobuf requests and return raw protobuf responses:

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
