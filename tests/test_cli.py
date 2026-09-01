from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from imgconvert.cli import main


def _save(path: Path, size: tuple[int, int] = (1200, 800)) -> None:
    image = Image.new("RGB", size, "navy")
    image.save(path, format="JPEG")
    image.close()


def test_json_output_reports_site_geometry(tmp_path: Path, capsys) -> None:
    source = tmp_path / "photo.jpg"
    output_dir = tmp_path / "publish"
    _save(source)

    exit_code = main([str(source), "--output-dir", str(output_dir), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["source"] == str(source)
    assert payload[0]["output"] == str(output_dir / "photo.webp")
    assert payload[0]["width"] == 1200
    assert payload[0]["height"] == 800
    assert payload[0]["source_bytes"] == source.stat().st_size
    assert payload[0]["output_bytes"] == (output_dir / "photo.webp").stat().st_size
    assert isinstance(payload[0]["reduction_percent"], float)
    assert payload[0]["resized"] is False


def test_human_output_reports_conversion(tmp_path: Path, capsys) -> None:
    source = tmp_path / "photo.jpg"
    _save(source)

    exit_code = main([str(source), "--output-dir", str(tmp_path / "publish")])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "1200x800" in output
    assert "original dimensions" in output
    assert "reduction" in output


def test_no_resize_cli_keeps_wide_source(tmp_path: Path, capsys) -> None:
    source = tmp_path / "wide.jpg"
    _save(source, (4000, 2000))

    exit_code = main(
        [str(source), "--output-dir", str(tmp_path / "publish"), "--no-resize", "--json"]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert (payload[0]["width"], payload[0]["height"]) == (4000, 2000)
    assert payload[0]["resized"] is False


def test_conversion_failure_sets_nonzero_exit_code(tmp_path: Path, capsys) -> None:
    source = tmp_path / "broken.jpg"
    source.write_text("not an image")

    exit_code = main([str(source), "--output-dir", str(tmp_path / "publish")])

    assert exit_code == 1
    assert "ERROR:" in capsys.readouterr().err


def test_batch_collision_is_rejected_before_processing(tmp_path: Path) -> None:
    first = tmp_path / "a" / "same.jpg"
    second = tmp_path / "b" / "same.png"
    first.parent.mkdir()
    second.parent.mkdir()
    Image.new("RGB", (10, 10), "red").save(first)
    Image.new("RGB", (10, 10), "blue").save(second)

    with pytest.raises(SystemExit) as error:
        main([str(first), str(second), "--output-dir", str(tmp_path / "publish")])

    assert error.value.code == 2
    assert not (tmp_path / "publish").exists()


@pytest.mark.parametrize(
    "args",
    [
        ["photo.jpg", "--quality", "0"],
        ["photo.jpg", "--max-width", "0"],
    ],
)
def test_invalid_cli_numeric_options_are_rejected(args: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(args)

    assert error.value.code == 2
