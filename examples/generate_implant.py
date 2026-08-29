"""Generate an executable implant and save it without overwriting files."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

from sliver import (
    GOARCH,
    GOOS,
    BeaconOptions,
    C2Endpoint,
    Client,
    GeneratedImplant,
    ImplantSpec,
    Target,
)
from sliver.models.clientpb import Generate, ImplantConfig


def host_target() -> tuple[str, str]:
    """Return the current host's typed Sliver target as wire-format values."""

    target = Target.current()
    return target.os.value, target.arch.value


def build_implant_spec(
    c2_url: str,
    *,
    target: Target | None = None,
    is_beacon: bool = False,
) -> ImplantSpec:
    """Build the concise domain model accepted by :meth:`Client.generate`."""

    beacon = (
        BeaconOptions(interval=timedelta(seconds=5), jitter=timedelta())
        if is_beacon
        else None
    )
    return ImplantSpec(
        target=target or Target.current(),
        c2=[C2Endpoint.from_url(c2_url)],
        beacon=beacon,
    )


def build_implant_config(
    c2_url: str,
    *,
    goos: GOOS | str,
    goarch: GOARCH | str,
    is_beacon: bool = False,
) -> ImplantConfig:
    """Compatibility helper returning the generated Pydantic config model."""

    return build_implant_spec(
        c2_url,
        target=Target(os=GOOS(goos), arch=GOARCH(goarch)),
        is_beacon=is_beacon,
    ).to_implant_config()


def save_generated_implant(
    generated: Generate | GeneratedImplant,
    output: Path | None = None,
) -> Path:
    """Compatibility helper for safely persisting either generation result."""

    implant = (
        generated
        if isinstance(generated, GeneratedImplant)
        else GeneratedImplant.from_generate(generated)
    )
    return implant.save(output)


def _target(goos: GOOS | None, goarch: GOARCH | None) -> Target:
    if goos is not None and goarch is not None:
        return Target(os=goos, arch=goarch)
    current = Target.current()
    return Target(os=goos or current.os, arch=goarch or current.arch)


async def _run(args: argparse.Namespace) -> None:
    spec = build_implant_spec(
        args.c2,
        target=_target(args.goos, args.goarch),
        is_beacon=args.beacon,
    )

    client = Client.from_config_file(args.config)
    async with client:
        generated = await client.generate(spec, timeout=args.timeout)
    path = generated.save(args.output)

    print(f"Implant name: {generated.implant_name}")
    print(f"Saved: {path}")
    print(f"Size: {path.stat().st_size} bytes")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("c2", help="C2 URL, e.g. mtls://127.0.0.1:8888")
    parser.add_argument("--config", help="operator config (or set SLIVER_CONFIG)")
    parser.add_argument(
        "--goos",
        type=GOOS,
        choices=tuple(GOOS),
        help="target GOOS (defaults to the current host)",
    )
    parser.add_argument(
        "--goarch",
        type=GOARCH,
        choices=tuple(GOARCH),
        help="target GOARCH (defaults to the current host)",
    )
    parser.add_argument("--beacon", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=360)
    args = parser.parse_args(argv)
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
