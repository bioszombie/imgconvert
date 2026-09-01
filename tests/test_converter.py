from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from imgconvert.converter import (
    ARTIST_TAG,
    COPYRIGHT_TAG,
    DEFAULT_CREATOR,
    DEFAULT_RIGHTS,
    GPS_INFO_TAG,
    ConversionError,
    convert_image,
)


def _save_rgb(path: Path, size: tuple[int, int] = (800, 600), *, exif=None) -> None:
    image = Image.new("RGB", size, (25, 50, 75))
    image.save(path, format="JPEG", quality=95, exif=exif)
    image.close()


def test_conversion_preserves_source_and_does_not_upscale(tmp_path: Path) -> None:
    source = tmp_path / "photo.jpg"
    output = tmp_path / "publish" / "photo.webp"
    _save_rgb(source)
    before = source.read_bytes()

    result = convert_image(source, output)

    assert source.read_bytes() == before
    assert result.width == 800
    assert result.height == 600
    assert result.resized is False
    assert output.is_file()


def test_conversion_resizes_wide_image(tmp_path: Path) -> None:
    source = tmp_path / "wide.jpg"
    output = tmp_path / "wide.webp"
    _save_rgb(source, (4000, 2000))

    result = convert_image(source, output, max_width=3200)

    assert (result.width, result.height) == (3200, 1600)
    assert result.resized is True


def test_exif_orientation_is_applied_to_pixels(tmp_path: Path) -> None:
    source = tmp_path / "portrait.jpg"
    output = tmp_path / "portrait.webp"
    exif = Image.Exif()
    exif[274] = 6
    _save_rgb(source, (40, 20), exif=exif)

    result = convert_image(source, output)

    assert (result.width, result.height) == (20, 40)
    with Image.open(output) as published:
        assert published.getexif().get(274, 1) == 1


def test_inherited_metadata_is_replaced_with_controlled_rights(tmp_path: Path) -> None:
    source = tmp_path / "metadata.jpg"
    output = tmp_path / "metadata.webp"
    exif = Image.Exif()
    exif[ARTIST_TAG] = "Camera Owner"
    exif[COPYRIGHT_TAG] = "Old rights"
    _save_rgb(source, exif=exif)

    convert_image(source, output)

    with Image.open(output) as published:
        published_exif = published.getexif()
        assert published_exif.get(ARTIST_TAG) == DEFAULT_CREATOR
        assert published_exif.get(COPYRIGHT_TAG) == DEFAULT_RIGHTS
        assert GPS_INFO_TAG not in published_exif
        xmp = published.info.get("xmp", b"")
        assert DEFAULT_CREATOR.encode() in xmp
        assert DEFAULT_RIGHTS.encode() in xmp


def test_existing_destination_is_not_overwritten_by_default(tmp_path: Path) -> None:
    source = tmp_path / "photo.jpg"
    output = tmp_path / "photo.webp"
    _save_rgb(source)
    output.write_bytes(b"existing")

    with pytest.raises(ConversionError, match="already exists"):
        convert_image(source, output)

    assert output.read_bytes() == b"existing"


def test_animated_webp_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "animated.webp"
    output = tmp_path / "output.webp"
    first = Image.new("RGB", (20, 20), "black")
    second = Image.new("RGB", (20, 20), "white")
    first.save(source, save_all=True, append_images=[second], format="WEBP", duration=100, loop=0)
    first.close()
    second.close()

    with pytest.raises(ConversionError, match="multi-frame"):
        convert_image(source, output)


def test_cmyk_input_is_rejected_instead_of_silently_reprofiling(tmp_path: Path) -> None:
    source = tmp_path / "cmyk.jpg"
    output = tmp_path / "cmyk.webp"
    image = Image.new("CMYK", (20, 20), (0, 10, 20, 0))
    image.save(source, format="JPEG")
    image.close()

    with pytest.raises(ConversionError, match="export the photograph as RGB"):
        convert_image(source, output)


def test_non_image_input_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "not-an-image.jpg"
    output = tmp_path / "not-an-image.webp"
    source.write_text("not actually an image")

    with pytest.raises(ConversionError, match="unable to decode image safely"):
        convert_image(source, output)
