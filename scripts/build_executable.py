#!/usr/bin/env python3
"""Build one self-contained imgconvert executable with the pinned PyInstaller toolchain."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from PyInstaller.__main__ import run as pyinstaller_run

ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = ROOT / "build" / "pyinstaller"
RELEASE_ROOT = ROOT / "release"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-name", required=True)
    args = parser.parse_args()

    shutil.rmtree(BUILD_ROOT, ignore_errors=True)
    RELEASE_ROOT.mkdir(parents=True, exist_ok=True)

    dist_dir = BUILD_ROOT / "dist"
    work_dir = BUILD_ROOT / "work"
    spec_dir = BUILD_ROOT / "spec"

    pyinstaller_run(
        [
            "--clean",
            "--noconfirm",
            "--onefile",
            "--console",
            "--noupx",
            "--name=imgconvert",
            f"--paths={ROOT / 'src'}",
            f"--distpath={dist_dir}",
            f"--workpath={work_dir}",
            f"--specpath={spec_dir}",
            str(ROOT / "src" / "imgconvert" / "__main__.py"),
        ]
    )

    built_name = "imgconvert.exe" if os.name == "nt" else "imgconvert"
    built = dist_dir / built_name
    if not built.is_file():
        raise SystemExit(f"PyInstaller did not produce the expected executable: {built}")

    target = RELEASE_ROOT / args.artifact_name
    shutil.copy2(built, target)
    if os.name != "nt":
        target.chmod(target.stat().st_mode | 0o111)

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
