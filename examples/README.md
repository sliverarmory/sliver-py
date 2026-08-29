# Idiomatic public API examples

These runnable modules use the small, typed API exported directly from
`sliver`. They demonstrate the patterns an application normally needs:

- `Client.from_config_file()` resolves an explicit path,
  `SLIVER_CONFIG`, or Sliver's default operator config.
- `async with client` owns the connection and closes it on every exit path.
- `GOOS`, `GOARCH`, `TargetKind`, and `EventType` replace string constants.
- `Target`, `C2Endpoint`, `BeaconOptions`, and `ImplantSpec` validate generation
  inputs before an RPC is sent.
- `inventory()`, `collect_events()`, `use_session()`, `use_beacon()`, and
  `temporary_mtls()` handle common multi-call workflows.
- Interactive commands use Sliver client names and raise `CommandError` when
  the implant reports an error.

For example, a complete inventory request is just:

```python
from sliver import Client

client = Client.from_config_file()
async with client:
    inventory = await client.inventory()
```

Implant generation uses typed values rather than a large generated config:

```python
from sliver import C2Endpoint, GOARCH, GOOS, ImplantSpec, Target

spec = ImplantSpec(
    target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
    c2=[C2Endpoint.mtls("c2.example.org")],
)

async with client:
    implant = await client.generate(spec)
implant.save("./implant")
```

The event helper bounds both the result count and the wait:

```python
from sliver import EventType

async with client:
    events = await client.collect_events(
        EventType.JOB_STARTED,
        limit=1,
        timeout=60,
    )
```

Owned listeners are always stopped, including when the body raises:

```python
import asyncio

async with client:
    async with client.temporary_mtls(host="127.0.0.1") as listener:
        await asyncio.sleep(60)
```

Run the examples with `uv`:

```console
uv run python -m examples.inventory
uv run python -m examples.interact session [SESSION_ID]
uv run python -m examples.interact beacon [BEACON_ID]
uv run python -m examples.watch_events job-started --count 1 --timeout 60
uv run python -m examples.generate_implant mtls://127.0.0.1:8888
uv run python -m examples.temporary_listener --port 8888 --duration 60
```

Generation defaults to the current host's supported target. Use `--goos` and
`--goarch` to cross-compile. Generated files use exclusive creation by default,
so choose a new `--output` path instead of overwriting an existing file.

The high-level methods intentionally cover common command workflows. For an
unwrapped server operation, `client.rpc.<snake_case>()` is the typed Pydantic
escape hatch; raw protobuf messages are not part of the public API.
