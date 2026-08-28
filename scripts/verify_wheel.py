#!/usr/bin/env python3
"""Verify that a built wheel contains the complete typed Pydantic API."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile

REQUIRED_FILES = {
    "sliver/py.typed",
    "sliver/_rpc_generated.py",
    "sliver/models/__init__.py",
    "sliver/models/clientpb.py",
    "sliver/models/clientpb.pyi",
    "sliver/models/commonpb.py",
    "sliver/models/commonpb.pyi",
    "sliver/models/sliverpb.py",
    "sliver/models/sliverpb.pyi",
}


def verify_wheel(wheel: Path) -> None:
    """Raise when ``wheel`` omits or obscures the concrete model package."""

    with ZipFile(wheel) as archive:
        names = set(archive.namelist())

    missing = sorted(REQUIRED_FILES - names)
    if missing:
        raise RuntimeError(
            f"{wheel.name} is missing typed public API files: {', '.join(missing)}"
        )
    if "sliver/models.py" in names:
        raise RuntimeError(
            f"{wheel.name} contains the removed dynamic sliver.models module"
        )
    print(f"Verified typed Pydantic API in {wheel}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    verify_wheel(args.wheel)


if __name__ == "__main__":
    main()
