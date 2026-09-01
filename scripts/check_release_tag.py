#!/usr/bin/env python3
"""Fail a release when its Git tag does not exactly match the package version."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from imgconvert import __version__  # noqa: E402

TAG_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    args = parser.parse_args()

    if not TAG_PATTERN.fullmatch(args.tag):
        raise SystemExit(f"release tag must be stable SemVer vMAJOR.MINOR.PATCH, got {args.tag!r}")

    expected = f"v{__version__}"
    if args.tag != expected:
        raise SystemExit(f"release tag {args.tag!r} does not match package version {expected!r}")

    print(f"release tag {args.tag} matches imgconvert {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
