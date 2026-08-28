"""Run common commands through a session or beacon."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from sliver import SliverClient, models

from .common import connected_client, require_success

TargetKind = Literal["session", "beacon"]
Target = models.clientpb.Session | models.clientpb.Beacon


@dataclass(frozen=True, slots=True)
class InteractionResult:
    """Results from the commands demonstrated by this example."""

    target: Target
    ping: models.sliverpb.Ping
    pwd: models.sliverpb.Pwd
    listing: models.sliverpb.Ls
    executed: models.sliverpb.Execute


def _default_command(target_os: str) -> tuple[str, list[str]]:
    if target_os.lower() == "windows":
        return "cmd.exe", ["/c", "whoami"]
    return "/usr/bin/id", []


async def run_interaction(
    client: SliverClient,
    kind: TargetKind,
    target_id: str | None = None,
    *,
    remote_path: str = ".",
    executable: str | None = None,
    arguments: Sequence[str] = (),
    timeout: int = 360,
) -> InteractionResult:
    """Interact with an explicit target, or the first target of ``kind``."""

    if kind == "session":
        targets = await client.sessions(timeout=timeout)
    elif kind == "beacon":
        targets = await client.beacons(timeout=timeout)
    else:
        raise ValueError(f"unsupported target kind: {kind}")

    target = next(
        (item for item in targets if target_id is None or item.id == target_id),
        None,
    )
    if target is None:
        detail = f" {target_id!r}" if target_id is not None else ""
        raise LookupError(f"no active {kind}{detail} found")

    if kind == "session":
        interaction = await client.interact_session(target.id, timeout=timeout)
    else:
        interaction = await client.interact_beacon(target.id, timeout=timeout)
    if interaction is None:
        raise LookupError(f"{kind} {target.id!r} disappeared before interaction")

    try:
        ping = await asyncio.wait_for(interaction.ping(), timeout=timeout)
        require_success(ping)
        pwd = await asyncio.wait_for(interaction.pwd(), timeout=timeout)
        require_success(pwd)
        listing = await asyncio.wait_for(interaction.ls(remote_path), timeout=timeout)
        require_success(listing)

        command, default_arguments = _default_command(interaction.os)
        if executable is None:
            executable = command
            command_arguments = default_arguments
        else:
            command_arguments = list(arguments)
        executed = await asyncio.wait_for(
            interaction.execute(executable, command_arguments, output=True),
            timeout=timeout,
        )
        require_success(executed)
        return InteractionResult(target, ping, pwd, listing, executed)
    finally:
        if kind == "beacon":
            await interaction.close()


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
    async with connected_client(args.config) as client:
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
    parser.add_argument("kind", choices=("session", "beacon"))
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
