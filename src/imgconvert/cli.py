"""Command-line interface for publication image preparation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from imgconvert.converter import (
    DEFAULT_CREATOR,
    DEFAULT_MAX_WIDTH,
    DEFAULT_QUALITY,
    DEFAULT_RIGHTS,
    ConversionError,
    ConversionResult,
    convert_image,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imgconvert",
        description="Prepare edited photographs as publication-ready WebP sources.",
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Edited photograph(s) to convert.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("publish"),
        help="Output directory (default: ./publish).",
    )
    resize = parser.add_mutually_exclusive_group()
    resize.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        help=f"Downsize images wider than this value (default: {DEFAULT_MAX_WIDTH}).",
    )
    resize.add_argument(
        "--no-resize",
        action="store_true",
        help="Keep the oriented source dimensions.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help=f"WebP quality from 1-100 (default: {DEFAULT_QUALITY}).",
    )
    parser.add_argument(
        "--creator",
        default=DEFAULT_CREATOR,
        help=f"Controlled Artist/XMP creator value (default: {DEFAULT_CREATOR!r}).",
    )
    parser.add_argument(
        "--rights",
        default=DEFAULT_RIGHTS,
        help="Controlled Copyright/XMP rights value.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Explicitly allow replacement of an existing destination WebP.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable publication results.",
    )
    return parser


def _human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    raise AssertionError("unreachable")


def _result_json(result: ConversionResult) -> dict[str, object]:
    return {
        "source": str(result.source),
        "output": str(result.output),
        "width": result.width,
        "height": result.height,
        "source_bytes": result.source_bytes,
        "output_bytes": result.output_bytes,
        "reduction_percent": round(result.reduction_percent, 2),
        "resized": result.resized,
    }


def _validate_batch(parser: argparse.ArgumentParser, inputs: list[Path], output_dir: Path) -> None:
    destinations: dict[str, Path] = {}
    for source in inputs:
        destination = output_dir / f"{source.stem}.webp"
        key = str(destination.resolve(strict=False)).casefold()
        previous = destinations.get(key)
        if previous is not None:
            parser.error(
                f"multiple inputs map to the same output {destination}: {previous} and {source}"
            )
        destinations[key] = source


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")
    if not args.no_resize and args.max_width < 1:
        parser.error("--max-width must be positive")

    _validate_batch(parser, args.inputs, args.output_dir)
    max_width = None if args.no_resize else args.max_width

    results: list[ConversionResult] = []
    failed = False

    for source in args.inputs:
        destination = args.output_dir / f"{source.stem}.webp"
        try:
            result = convert_image(
                source,
                destination,
                max_width=max_width,
                quality=args.quality,
                creator=args.creator,
                rights=args.rights,
                overwrite=args.overwrite,
            )
        except ConversionError as exc:
            failed = True
            print(f"ERROR: {exc}", file=sys.stderr)
            continue
        results.append(result)

        if not args.json_output:
            resize_note = "resized" if result.resized else "original dimensions"
            print(
                f"{result.source} -> {result.output} "
                f"({result.width}x{result.height}, {resize_note}, "
                f"{_human_bytes(result.source_bytes)} -> {_human_bytes(result.output_bytes)}, "
                f"{result.reduction_percent:.1f}% reduction)"
            )

    if args.json_output:
        print(json.dumps([_result_json(result) for result in results], indent=2))

    return 1 if failed else 0
