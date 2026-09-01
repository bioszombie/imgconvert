"""Safe, single-shot conversion of edited photographs to publication WebP sources."""

from __future__ import annotations

import os
import tempfile
import warnings
from dataclasses import dataclass
from html import escape
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

DEFAULT_CREATOR = "Lucas Langosh"
DEFAULT_RIGHTS = "Copyright (c) Lucas Langosh. All rights reserved."
DEFAULT_MAX_WIDTH = 3200
DEFAULT_QUALITY = 90
MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_IMAGE_PIXELS = 100_000_000
SUPPORTED_FORMATS = frozenset({"JPEG", "PNG", "TIFF", "WEBP"})
SUPPORTED_MODES = frozenset({"RGB", "RGBA", "L", "LA", "P"})

ORIENTATION_TAG = 274
ARTIST_TAG = 315
COPYRIGHT_TAG = 33432
GPS_INFO_TAG = 34853

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class ConversionError(RuntimeError):
    """Raised when an input cannot safely satisfy the publication contract."""


@dataclass(frozen=True, slots=True)
class ConversionResult:
    source: Path
    output: Path
    width: int
    height: int
    source_bytes: int
    output_bytes: int
    resized: bool

    @property
    def reduction_percent(self) -> float:
        if self.source_bytes == 0:
            return 0.0
        return ((self.source_bytes - self.output_bytes) / self.source_bytes) * 100


def _rights_xmp(creator: str, rights: str) -> bytes:
    creator_xml = escape(creator, quote=True)
    rights_xml = escape(rights, quote=True)
    return (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">'
        f'<dc:creator><rdf:Seq><rdf:li>{creator_xml}</rdf:li></rdf:Seq></dc:creator>'
        '<dc:rights><rdf:Alt>'
        f'<rdf:li xml:lang="x-default">{rights_xml}</rdf:li>'
        '</rdf:Alt></dc:rights>'
        '<xmpRights:Marked>True</xmpRights:Marked>'
        '<xmpRights:UsageTerms><rdf:Alt>'
        '<rdf:li xml:lang="x-default">All rights reserved.</rdf:li>'
        '</rdf:Alt></xmpRights:UsageTerms>'
        '</rdf:Description></rdf:RDF></x:xmpmeta>'
    ).encode("utf-8")


def _controlled_exif(creator: str, rights: str) -> Image.Exif:
    exif = Image.Exif()
    exif[ARTIST_TAG] = creator
    exif[COPYRIGHT_TAG] = rights
    return exif


def _prepare_pixels(image: Image.Image, max_width: int | None) -> tuple[Image.Image, bool]:
    normalized = ImageOps.exif_transpose(image)
    try:
        if normalized.mode not in SUPPORTED_MODES:
            raise ConversionError(
                f"unsupported pixel mode {normalized.mode}; export the photograph as RGB first"
            )

        has_alpha = normalized.mode in {"RGBA", "LA"} or (
            normalized.mode == "P" and "transparency" in normalized.info
        )
        working = normalized.convert("RGBA" if has_alpha else "RGB")
    finally:
        normalized.close()

    resized = False
    if max_width is not None and working.width > max_width:
        new_height = round(working.height * max_width / working.width)
        scaled = working.resize((max_width, new_height), Image.Resampling.LANCZOS)
        working.close()
        working = scaled
        resized = True

    return working, resized


def _validate_published(
    path: Path,
    *,
    expected_size: tuple[int, int],
    creator: str,
    rights: str,
    expected_icc: bytes | None,
) -> None:
    with Image.open(path) as published:
        published.load()
        if published.format != "WEBP":
            raise ConversionError(f"generated file is not WebP: {path}")
        if getattr(published, "n_frames", 1) != 1:
            raise ConversionError(f"generated WebP unexpectedly contains multiple frames: {path}")
        if published.size != expected_size:
            raise ConversionError(
                f"generated dimensions drifted: expected {expected_size}, got {published.size}"
            )

        exif = published.getexif()
        if exif.get(ORIENTATION_TAG, 1) != 1:
            raise ConversionError(f"generated WebP has non-normal EXIF orientation: {path}")
        if exif.get(ARTIST_TAG) != creator:
            raise ConversionError(f"generated WebP is missing controlled Artist metadata: {path}")
        if exif.get(COPYRIGHT_TAG) != rights:
            raise ConversionError(f"generated WebP is missing controlled Copyright metadata: {path}")
        if GPS_INFO_TAG in exif:
            raise ConversionError(f"generated WebP contains GPS metadata: {path}")

        xmp = published.info.get("xmp")
        if not xmp:
            raise ConversionError(f"generated WebP is missing controlled XMP rights metadata: {path}")

        if expected_icc is not None and published.info.get("icc_profile") != expected_icc:
            raise ConversionError(f"generated WebP did not preserve the source ICC profile: {path}")


def convert_image(
    source: Path,
    destination: Path,
    *,
    max_width: int | None = DEFAULT_MAX_WIDTH,
    quality: int = DEFAULT_QUALITY,
    creator: str = DEFAULT_CREATOR,
    rights: str = DEFAULT_RIGHTS,
    overwrite: bool = False,
) -> ConversionResult:
    """Convert one edited photograph to an atomic, verified WebP publication source."""

    source = Path(source)
    destination = Path(destination)

    if source.is_symlink():
        raise ConversionError(f"symbolic-link inputs are not accepted: {source}")
    if not source.is_file():
        raise ConversionError(f"input is not a regular file: {source}")
    if destination.suffix.lower() != ".webp":
        raise ConversionError(f"output must use a .webp extension: {destination}")
    if source.resolve() == destination.resolve(strict=False):
        raise ConversionError("source and destination must be different files")
    if destination.exists() and not overwrite:
        raise ConversionError(f"output already exists (use --overwrite to replace it): {destination}")
    if not 1 <= quality <= 100:
        raise ConversionError("quality must be between 1 and 100")
    if max_width is not None and max_width < 1:
        raise ConversionError("max_width must be positive when resizing is enabled")

    source_bytes = source.stat().st_size
    if source_bytes > MAX_INPUT_BYTES:
        raise ConversionError(
            f"input exceeds the {MAX_INPUT_BYTES // (1024 * 1024)} MiB publication limit: {source}"
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as image:
                image.load()
                if image.format not in SUPPORTED_FORMATS:
                    raise ConversionError(
                        f"unsupported decoded format {image.format or 'unknown'}; "
                        "expected JPEG, PNG, TIFF, or WebP"
                    )
                if getattr(image, "n_frames", 1) != 1:
                    raise ConversionError("animated or multi-frame images are not publishable sources")

                compatible_icc = (
                    image.info.get("icc_profile") if image.mode in {"RGB", "RGBA"} else None
                )
                prepared, resized = _prepare_pixels(image, max_width)
    except ConversionError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
    ) as exc:
        raise ConversionError(f"unable to decode image safely: {source}: {exc}") from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=".webp", dir=destination.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)

    try:
        save_options: dict[str, object] = {
            "format": "WEBP",
            "quality": quality,
            "method": 6,
            "exif": _controlled_exif(creator, rights),
            "xmp": _rights_xmp(creator, rights),
        }
        if compatible_icc is not None:
            save_options["icc_profile"] = compatible_icc

        prepared.save(temporary, **save_options)
        expected_size = prepared.size
        _validate_published(
            temporary,
            expected_size=expected_size,
            creator=creator,
            rights=rights,
            expected_icc=compatible_icc,
        )

        if overwrite:
            os.replace(temporary, destination)
        else:
            try:
                os.link(temporary, destination)
            except FileExistsError as exc:
                raise ConversionError(
                    f"output appeared during conversion and was not replaced: {destination}"
                ) from exc
            temporary.unlink()
    except ConversionError:
        raise
    except OSError as exc:
        raise ConversionError(f"unable to publish WebP atomically: {destination}: {exc}") from exc
    finally:
        prepared.close()
        temporary.unlink(missing_ok=True)

    return ConversionResult(
        source=source,
        output=destination,
        width=expected_size[0],
        height=expected_size[1],
        source_bytes=source_bytes,
        output_bytes=destination.stat().st_size,
        resized=resized,
    )
