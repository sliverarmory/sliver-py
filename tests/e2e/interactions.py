"""Reusable assertions for the portable native interaction contract."""

from __future__ import annotations

import asyncio
import gzip
import ipaddress
import os
import socket
import sys
import uuid
from pathlib import Path

from sliver import InteractiveBeacon, InteractiveSession, models

from .conftest import COMMAND_TIMEOUT, POLL_INTERVAL

Interactive = InteractiveSession | InteractiveBeacon


def assert_implant_response_succeeded(result: object) -> None:
    response = getattr(result, "response", None)
    assert response is None or not response.err


def assert_same_native_path(actual: str, expected: Path) -> None:
    assert os.path.normcase(str(Path(actual).resolve())) == os.path.normcase(
        str(expected.resolve())
    )


def decoded_download_data(download: models.sliverpb.Download) -> bytes:
    if not download.encoder:
        return download.data
    if download.encoder == "gzip":
        return gzip.decompress(download.data)
    raise AssertionError(f"unexpected download encoder {download.encoder!r}")


async def exercise_read_only_inventory(
    interactive: Interactive,
    *,
    implant_pid: int,
    work_dir: Path,
) -> None:
    """Exercise deterministic process, network, filesystem, and Wasm inventory."""

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    known_port = int(listener.getsockname()[1])
    try:
        ping, processes, working_directory = await asyncio.gather(
            interactive.ping(0x5A17C0DE),
            interactive.ps(full_info=True),
            interactive.pwd(),
        )
        interfaces, connections, mounts = await asyncio.gather(
            interactive.ifconfig(),
            interactive.netstat(
                tcp=True,
                udp=False,
                ipv4=True,
                ipv6=False,
                listening=True,
            ),
            interactive.mount(),
        )
        wasm_extensions = await interactive.wasm_ls()
    finally:
        listener.close()

    for result in (
        ping,
        processes,
        working_directory,
        interfaces,
        connections,
        mounts,
        wasm_extensions,
    ):
        assert_implant_response_succeeded(result)

    assert ping.nonce == 0x5A17C0DE
    assert any(process.pid == implant_pid for process in processes.processes)
    assert_same_native_path(working_directory.path, work_dir)
    assert any(
        ipaddress.ip_interface(address).ip.is_loopback
        for interface in interfaces.net_interfaces
        for address in interface.ip_addresses
    )
    assert any(
        entry.protocol.lower() == "tcp"
        and entry.sk_state.upper() == "LISTEN"
        and entry.local_addr is not None
        and entry.local_addr.port == known_port
        for entry in connections.entries
    )
    assert mounts.info
    assert wasm_extensions.names == []


async def exercise_filesystem_lifecycle(
    interactive: Interactive,
    *,
    work_dir: Path,
    label: str,
) -> None:
    """Round-trip known bytes through Sliver's portable filesystem commands."""

    unique = uuid.uuid4().hex
    fixture = work_dir / f"fixture-{label}-{unique}"
    original = fixture / "original.txt"
    copied = fixture / "copied.txt"
    moved = fixture / "moved.txt"
    sentinel = work_dir / f"sentinel-{label}-{unique}.txt"
    marker = f"sliver-py-{label}-{unique}"
    contents = f"before\n{marker}\nafter\n".encode()
    sentinel_contents = b"outside-fixture"
    sentinel.write_bytes(sentinel_contents)
    created = False

    try:
        made = await interactive.mkdir(str(fixture))
        created = True
        assert_implant_response_succeeded(made)

        uploaded = await interactive.upload(str(original), contents)
        assert_implant_response_succeeded(uploaded)
        assert uploaded.written_files == 1

        copy = await interactive.cp(str(original), str(copied))
        assert_implant_response_succeeded(copy)
        assert copy.bytes_written == len(contents)

        move = await interactive.mv(str(copied), str(moved))
        assert_implant_response_succeeded(move)

        matches = await interactive.grep(marker, str(original))
        assert_implant_response_succeeded(matches)
        assert any(
            marker in match.line
            for file_result in matches.results.values()
            for match in file_result.file_results
        )

        changed = await interactive.chtimes(
            str(original),
            1_700_000_000,
            1_700_000_001,
        )
        assert_implant_response_succeeded(changed)
        assert_same_native_path(changed.path, original)
        assert int(original.stat().st_mtime) == 1_700_000_001

        listing = await interactive.ls(str(fixture))
        assert_implant_response_succeeded(listing)
        assert listing.exists
        names = {Path(item.name).name: item for item in listing.files}
        assert names[original.name].size == len(contents)
        assert names[moved.name].size == len(contents)

        downloaded = await interactive.download(str(original))
        assert_implant_response_succeeded(downloaded)
        assert downloaded.exists
        assert decoded_download_data(downloaded) == contents

        changed_directory = await interactive.cd(str(fixture))
        assert_implant_response_succeeded(changed_directory)
        assert_same_native_path(changed_directory.path, fixture)
        assert_same_native_path((await interactive.pwd()).path, fixture)
        restored = await interactive.cd(str(work_dir))
        assert_implant_response_succeeded(restored)
        assert_same_native_path(restored.path, work_dir)
    finally:
        try:
            await interactive.cd(str(work_dir))
        finally:
            if created:
                await interactive.rm(str(fixture), recursive=True, force=True)

    assert not fixture.exists()
    assert sentinel.read_bytes() == sentinel_contents
    sentinel.unlink()


async def exercise_environment_lifecycle(
    interactive: Interactive,
    *,
    label: str,
) -> None:
    key = f"SLIVER_PY_E2E_{label.upper()}_{uuid.uuid4().hex.upper()}"
    value = f"value-{uuid.uuid4().hex}"

    initial = await interactive.env()
    assert_implant_response_succeeded(initial)
    assert key not in {variable.key for variable in initial.variables}

    set_result = await interactive.env_set(key, value)
    assert_implant_response_succeeded(set_result)
    try:
        selected = await interactive.env(key)
        assert_implant_response_succeeded(selected)
        assert [(variable.key, variable.value) for variable in selected.variables] == [
            (key, value)
        ]
    finally:
        unset_result = await interactive.env_unset(key)
        assert_implant_response_succeeded(unset_result)

    final = await interactive.env()
    assert_implant_response_succeeded(final)
    assert key not in {variable.key for variable in final.variables}


async def exercise_captured_execute(
    interactive: Interactive,
    *,
    label: str,
) -> None:
    marker = f"sliver-py-{label}-{uuid.uuid4().hex}"
    error_marker = f"{marker}-stderr"
    env_key = "SLIVER_PY_EXEC_MARKER"
    script = (
        "import os,sys;"
        f"print(os.environ[{env_key!r}]);"
        f"print({error_marker!r}, file=sys.stderr);"
        "raise SystemExit(7)"
    )

    executed = await interactive.execute(
        str(Path(sys.executable).resolve()),
        ["-c", script],
        output=True,
        env={env_key: marker},
        env_inheritance=True,
    )

    assert_implant_response_succeeded(executed)
    assert executed.status == 7
    assert executed.stdout.strip() == marker.encode()
    assert executed.stderr.strip() == error_marker.encode()
    assert executed.pid > 0


async def exercise_tracked_child_lifecycle(
    interactive: Interactive,
) -> None:
    """Create, identify, terminate, and observe one owned background child."""

    python = Path(sys.executable).resolve()
    marker = f"sliver-py-child-{uuid.uuid4().hex}"
    started = await interactive.execute(
        str(python),
        ["-c", "import time; time.sleep(120)", marker],
        output=False,
        background=True,
        env_inheritance=True,
    )
    assert_implant_response_succeeded(started)
    assert started.pid > 0

    try:
        children = await interactive.execute_children()
        assert_implant_response_succeeded(children)
        child = next(item for item in children.children if item.pid == started.pid)
        assert not child.exited
        assert_same_native_path(child.path, python)
        assert marker in child.args

        processes = await interactive.ps(full_info=True)
        assert any(process.pid == started.pid for process in processes.processes)

        terminated = await interactive.terminate(started.pid, force=True)
        assert_implant_response_succeeded(terminated)
        assert terminated.pid == started.pid

        deadline = asyncio.get_running_loop().time() + min(COMMAND_TIMEOUT, 30)
        while True:
            tracked = await interactive.execute_children()
            matching = [item for item in tracked.children if item.pid == started.pid]
            if matching and matching[0].exited:
                assert matching[0].exit_time > 0
                return
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError(f"tracked execute child {started.pid} did not exit")
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        children = await interactive.execute_children()
        matching = [item for item in children.children if item.pid == started.pid]
        if matching and not matching[0].exited:
            assert_same_native_path(matching[0].path, python)
            assert marker in matching[0].args
            await interactive.terminate(started.pid, force=True)


__all__ = [
    "assert_implant_response_succeeded",
    "assert_same_native_path",
    "decoded_download_data",
    "exercise_captured_execute",
    "exercise_environment_lifecycle",
    "exercise_filesystem_lifecycle",
    "exercise_read_only_inventory",
    "exercise_tracked_child_lifecycle",
]
