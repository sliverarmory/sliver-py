"""Run common commands through a session or beacon."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from sliver import (
    GOOS,
    Client,
    InteractiveBeacon,
    InteractiveSession,
    TargetKind,
)
from sliver.models.clientpb import Beacon, Session
from sliver.models.sliverpb import Execute, Ls, Ping, Pwd

TargetModel = Session | Beacon


@dataclass(frozen=True, slots=True)
class InteractionResult:
    """Results from the commands demonstrated by this example."""

    target: TargetModel
    ping: Ping
    pwd: Pwd
    listing: Ls
    executed: Execute


def _default_command(target_os: GOOS | str) -> tuple[str, list[str]]:
    if GOOS(target_os) is GOOS.WINDOWS:
        return "cmd.exe", ["/c", "whoami"]
    return "/usr/bin/id", []


async def _target_id(
    client: Client,
    kind: TargetKind,
    target_id: str | None,
    *,
    timeout: int,
) -> str:
    if target_id is not None:
        return target_id

    inventory = await client.inventory(timeout=timeout)
    targets = (
        inventory.sessions if kind is TargetKind.SESSION else inventory.beacons
    )
    if not targets:
        raise LookupError(f"no active {kind} found")
    return targets[0].id


async def run_interaction(
    client: Client,
    kind: TargetKind | str,
    target_id: str | None = None,
    *,
    remote_path: str = ".",
    executable: str | None = None,
    arguments: Sequence[str] = (),
    timeout: int = 360,
) -> InteractionResult:
    """Select an explicit target, or the first active target of ``kind``."""

    selected_kind = TargetKind(kind)
    selected_id = await _target_id(
        client,
        selected_kind,
        target_id,
        timeout=timeout,
    )

    beacon: InteractiveBeacon | None = None
    interaction: InteractiveSession | InteractiveBeacon
    if selected_kind is TargetKind.SESSION:
        interaction = await client.use_session(selected_id, timeout=timeout)
        target: TargetModel = interaction.session
    else:
        beacon = await client.use_beacon(selected_id, timeout=timeout)
        interaction = beacon
        target = beacon.beacon

    try:
        ping = await interaction.ping()
        pwd = await interaction.pwd()
        listing = await interaction.ls(remote_path)

        default_executable, default_arguments = _default_command(interaction.os)
        command = executable or default_executable
        command_arguments = list(arguments) if executable else default_arguments
        executed = await interaction.execute(command, command_arguments, output=True)
        return InteractionResult(target, ping, pwd, listing, executed)
    finally:
        if beacon is not None:
            await beacon.close()


def format_interaction(result: InteractionResult) -> str:
    """Render the public model fields returned by ``run_interaction``."""

    lines = [
        result.target.model_dump_json(indent=2, exclude_defaults=True),
        f"Working directory: {result.pwd.path}",
    ]
    lines.extend(
        f"{'dir' if item.is_dir else 'file':4} {item.size:10} {item.name}"
        for item in result.listing.files
    )
    stdout = result.executed.stdout.decode(errors="replace")
    stderr = result.executed.stderr.decode(errors="replace")
    if stdout:
        lines.append(stdout.rstrip("\n"))
    if stderr:
        lines.append(stderr.rstrip("\n"))
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> None:
    client = Client.from_config_file(args.config)
    async with client:
        result = await run_interaction(
            client,
            args.kind,
            args.target_id,
            remote_path=args.remote_path,
            executable=args.executable,
            arguments=args.argument,
            timeout=args.timeout,
        )
    print(format_interaction(result))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", type=TargetKind, choices=tuple(TargetKind))
    parser.add_argument("target_id", nargs="?")
    parser.add_argument("--config", help="operator config (or set SLIVER_CONFIG)")
    parser.add_argument("--remote-path", default=".")
    parser.add_argument("--executable", help="remote executable to run")
    parser.add_argument(
        "--argument",
        action="append",
        default=[],
        help="remote command argument; repeat as needed",
    )
    parser.add_argument("--timeout", type=int, default=360)
    args = parser.parse_args(argv)
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
