#!/usr/bin/env python3
"""Exercise a packaged executable through the real JPEG-to-WebP publication path."""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 - this verifier intentionally executes the locally built artifact
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from imgconvert import __version__  # noqa: E402
from imgconvert.converter import (  # noqa: E402
    ARTIST_TAG,
    COPYRIGHT_TAG,
    DEFAULT_CREATOR,
    DEFAULT_RIGHTS,
    GPS_INFO_TAG,
    ORIENTATION_TAG,
)

PRIVATE_DESCRIPTION_TAG = 270


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve()

    if not executable.is_file():
        raise SystemExit(f"packaged executable does not exist: {executable}")

    # The executable is the CI-produced artifact under test; no shell is involved.
    version = subprocess.run(  # nosec B603
        [str(executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    expected_version = f"imgconvert {__version__}"
    if version != expected_version:
        raise SystemExit(f"version mismatch: expected {expected_version!r}, got {version!r}")

    with tempfile.TemporaryDirectory(prefix="imgconvert-package-test-") as temp_name:
        temp = Path(temp_name)
        source = temp / "source.jpg"
        output_dir = temp / "publish"

        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        exif = Image.Exif()
        exif[ORIENTATION_TAG] = 6
        exif[PRIVATE_DESCRIPTION_TAG] = "private editor metadata"

        image = Image.new("RGB", (640, 480), "navy")
        image.save(source, format="JPEG", quality=95, exif=exif, icc_profile=icc)
        image.close()

        # All argv values are locally constructed test paths/options; shell=False is the default.
        completed = subprocess.run(  # nosec B603
            [
                str(executable),
                str(source),
                "--output-dir",
                str(output_dir),
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        if len(payload) != 1 or (payload[0]["width"], payload[0]["height"]) != (480, 640):
            raise SystemExit(f"unexpected packaged conversion result: {payload!r}")

        published_path = output_dir / "source.webp"
        with Image.open(published_path) as published:
            published.load()
            if published.format != "WEBP" or published.size != (480, 640):
                raise SystemExit("packaged executable did not publish the expected WebP geometry")
            if getattr(published, "n_frames", 1) != 1:
                raise SystemExit("packaged executable unexpectedly published a multi-frame WebP")

            output_exif = published.getexif()
            if output_exif.get(ORIENTATION_TAG, 1) != 1:
                raise SystemExit("packaged executable did not normalize EXIF orientation")
            if output_exif.get(ARTIST_TAG) != DEFAULT_CREATOR:
                raise SystemExit("packaged executable is missing controlled Artist metadata")
            if output_exif.get(COPYRIGHT_TAG) != DEFAULT_RIGHTS:
                raise SystemExit("packaged executable is missing controlled Copyright metadata")
            if PRIVATE_DESCRIPTION_TAG in output_exif or GPS_INFO_TAG in output_exif:
                raise SystemExit("packaged executable retained private EXIF metadata")
            if published.info.get("icc_profile") != icc:
                raise SystemExit("packaged executable did not preserve the compatible ICC profile")

            xmp = published.info.get("xmp") or b""
            if DEFAULT_CREATOR.encode() not in xmp or DEFAULT_RIGHTS.encode() not in xmp:
                raise SystemExit("packaged executable is missing controlled XMP rights metadata")

    print(f"verified {executable.name}: {expected_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
