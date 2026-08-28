# Public API examples

These modules use only the public Pydantic API. Each async helper accepts an
already-connected `SliverClient`, so applications and tests can reuse their own
client lifecycle. Each command-line entry point loads an operator config,
connects, and closes its client automatically.

The GitHub Actions E2E matrix executes every command below against a freshly
compiled Sliver server on macOS/arm64, Linux/amd64, and Windows/amd64.

Set `SLIVER_CONFIG` or pass `--config`. The default is
`~/.sliver-client/configs/default.cfg`.

```console
uv run python -m examples.inventory
uv run python -m examples.interact session [SESSION_ID]
uv run python -m examples.interact beacon [BEACON_ID]
uv run python -m examples.watch_events job-started --count 1 --timeout 60
uv run python -m examples.generate_implant mtls://127.0.0.1:8888
uv run python -m examples.temporary_listener --port 8888 --duration 60
```

Implant generation defaults to the current host's Sliver target. Pass
`--goos` and `--goarch` to cross-compile for another supported target.

Generated implants are saved with exclusive file creation. Choose a new
`--output` path rather than overwriting an existing file. Beacon interactions
stop their task-result watcher before returning; session interactions do not own
a separate watcher.
