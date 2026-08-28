# Managed Sliver end-to-end tests

These tests own the complete Sliver lifecycle. They start an isolated server,
generate an operator configuration, connect with `sliver-py`, bind a single
loopback-only mTLS listener, and generate and execute one native session and one
native beacon. The tests run in one pytest process so the server, client, and
listener are reused across all three test groups.

The suite is disabled during normal collection. Set `SLIVER_E2E=1` only on an
isolated test runner where executing freshly generated Sliver implants is
expected.

## GitHub Actions

`.github/workflows/e2e.yml` is the supported execution path. Pull requests and
pushes to `master` run all three native matrix targets; `workflow_dispatch`
also permits a manual run for a branch:

```console
gh workflow run e2e.yml --ref <branch>
```

Each matrix job builds the server once and invokes all three test modules in a
single pytest process so the isolated daemon and listener are reused.

## Test groups

- `e2e_basic`: server version, operator, inventory, event, build, and listener
  APIs. The inventory, event-watcher, and temporary-listener examples run as
  separate command-line processes against the isolated server.
- `e2e_session`: native executable generation, registration, ping, working
  directory, and subprocess execution through a session. The generation and
  interaction examples run as command-line processes and produce the fixture.
- `e2e_beacon`: the same native lifecycle and interactions through beacon tasks.
  The beacon-generation and interaction examples run as command-line processes.

Session and beacon generation explicitly use Sliver's `EXECUTABLE` output
format. A session or beacon is accepted only when its ID was not present before
launch and its generated name and PID match the process owned by the harness.

## Required environment

The GitHub Actions workflow supplies these canonical variables:

- `SLIVER_E2E=1`
- `SLIVER_E2E_REPO_ROOT`: this repository checkout
- `SLIVER_E2E_SLIVER_ROOT`: the checked-out pinned `sliver` submodule
- `SLIVER_E2E_SERVER`: absolute path to the native `sliver-server` executable
- `SLIVER_E2E_RESULTS_ROOT`: safe destination for JUnit and diagnostic logs
- `SLIVER_E2E_WORK_ROOT`: private disposable work directory
- `SLIVER_E2E_TARGET_OS`: `darwin`, `linux`, or `windows`
- `SLIVER_E2E_TARGET_ARCH`: `arm64` or `amd64`

For local diagnosis, build the pinned server submodule first and set the same
variables before running:

```console
uv run --frozen --only-group test pytest tests/e2e -m e2e
```

Use `-m e2e_basic`, `-m e2e_session`, or `-m e2e_beacon` to select one group.

## Safety and artifacts

Both the daemon gRPC endpoint and implant C2 listener bind explicitly to
`127.0.0.1`. Server state, operator credentials, and generated executables stay
under `SLIVER_E2E_WORK_ROOT` and are removed during teardown. They must never be
uploaded as workflow artifacts. Only JUnit output and sanitized, bounded
diagnostic logs under `SLIVER_E2E_RESULTS_ROOT` are artifact-safe.

Teardown stops the exact process trees launched by the harness. Session cleanup
also requests an implant exit; beacon cleanup stops the owned process before
removing its server database record because Sliver's `RmBeacon` RPC does not
terminate a running beacon.
