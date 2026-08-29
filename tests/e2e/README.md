# Managed Sliver end-to-end tests

These tests own the complete Sliver lifecycle. They start an isolated server,
generate an operator configuration, connect with `sliver-py`, bind a single
loopback-only mTLS listener, and generate and execute one native session and one
native beacon. The tests run in one pytest process, but each scenario module
gets a fresh server, client, listener, private state root, and diagnostic-log
namespace. A failed event broker or daemon therefore cannot contaminate the
next scenario group.

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

Each matrix job builds the server once and runs the complete `tests/e2e`
directory. Directory discovery is deliberate: adding a new managed E2E module
cannot silently omit it from CI.

## Test groups

- `e2e_basic`: preferred `Client` lifecycle and reconnect behavior; strict
  find/get semantics; server, operator, inventory, build, profile, website,
  canary, job, HTTP, mTLS, and event APIs. The inventory, event-watcher,
  generation, and temporary-listener examples also run as separate processes.
- `e2e_session`: native generation and registration; lookup/use/rename/restore;
  correlated ping; full process, interface, socket, mount, extension, pivot,
  and Wasm inventory; filesystem and environment lifecycles; captured execution;
  and a verified tracked-child termination lifecycle.
- `e2e_beacon`: the same portable inventory, filesystem, environment, and
  captured and tracked-child execution commands through asynchronous beacon
  tasks. It also asserts the exact new task ID, beacon ID, completed state,
  timestamps, and stored request and response content for a representative
  command.

Session and beacon generation explicitly use Sliver's `EXECUTABLE` output
format. A session or beacon is accepted only when its ID was not present before
launch and its generated name and PID match the process owned by the harness.

Portable filesystem mutation stays beneath the exact implant work directory.
Tests compare known bytes after download (including gzip decoding), restore the
working directory before cleanup, and verify a sentinel outside the owned
subtree survives. Process termination is limited to a child created with
`background=True`, returned by `execute_children()`, and re-identified by PID,
path, and marker immediately before termination.

## Coverage contract

`coverage.py` is the manually audited, checked-in denominator for all 159
exported high-level methods. `tests/test_e2e_coverage.py` fails if a method is
added, removed, assigned to more than one disposition, absent from the managed
scenario call sites, or if the exact native target and reachable-RPC identities
drift. The native jobs remain the authoritative proof that those calls execute
successfully; the static ledger does not manufacture runtime coverage.

The current accounting is:

- 71 exact public names invoked by native E2E on all three targets;
- 5 additional names executed by managed example subprocesses;
- 3 implementations reached transitively through another public method;
- 41 compatibility aliases covered by exact request/delegation unit tests;
- 5 safe methods explicitly queued for a future managed scenario; and
- 34 platform-, artifact-, privilege-, or higher-risk methods reserved for a
  specialized lane.

That makes 79 of 159 exported names behavior-covered by managed E2E (49.7%),
up from the original 33 of 151 (21.9%). Alias coverage is reported separately
so calling one spelling cannot inflate exact-name E2E coverage.

Exported-method coverage is not the same as Sliver feature completeness. The
pinned server exposes 193 RPCs; 86 are currently reachable through a handwritten
high-level client or interaction method (44.6%), leaving 107 raw-RPC-only. The
coverage contract also snapshots those counts so adding or removing pinned RPCs
cannot silently change the denominator. The largest high-level gaps are loot,
credentials, hosts/IOCs, HTTP C2 profiles, monitoring configuration,
certificate/compiler/encoder inventory, builders, tunnels, SOCKS/port-forward,
and several registry/service/pivot operations. These require API design and
managed scenarios before this client can honestly be called feature-complete.

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
uv run --frozen --group test pytest tests/e2e -m e2e
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

The default portable lane deliberately excludes DNS (the server ignores its
host argument), WireGuard (its outer UDP socket binds wildcard), HTTPS without
an owned certificate, arbitrary stage data, screenshots, process dumps,
credential/token operations, service or registry mutation, injection and
in-memory execution, tunnels, and external services. Those need dedicated
fixtures and capability markers rather than opportunistic skips.
