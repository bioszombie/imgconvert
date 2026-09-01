#!/usr/bin/env python3
"""Write deterministic SHA-256 checksums for release files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    files = sorted(
        path
        for path in args.directory.iterdir()
        if path.is_file() and path.resolve() != args.output.resolve()
    )
    if not files:
        raise SystemExit(f"no release files found in {args.directory}")

    lines = [f"{digest(path)} *{path.name}" for path in files]
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
