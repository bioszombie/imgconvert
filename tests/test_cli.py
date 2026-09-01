from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from imgconvert.cli import main


def test_json_output_reports_site_geometry(tmp_path: Path, capsys) -> None:
    source = tmp_path / "photo.jpg"
    output_dir = tmp_path / "publish"
    image = Image.new("RGB", (1200, 800), "navy")
    image.save(source, format="JPEG")
    image.close()

    exit_code = main([str(source), "--output-dir", str(output_dir), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == [
        {
            "source": str(source),
            "output": str(output_dir / "photo.webp"),
            "width": 1200,
            "height": 800,
            "source_bytes": source.stat().st_size,
            "output_bytes": (output_dir / "photo.webp").stat().st_size,
            "reduction_percent": payload[0]["reduction_percent"],
            "resized": False,
        }
    ]


def test_batch_collision_is_rejected_before_processing(tmp_path: Path) -> None:
    first = tmp_path / "a" / "same.jpg"
    second = tmp_path / "b" / "same.png"
    first.parent.mkdir()
    second.parent.mkdir()
    Image.new("RGB", (10, 10), "red").save(first)
    Image.new("RGB", (10, 10), "blue").save(second)

    try:
        main([str(first), str(second), "--output-dir", str(tmp_path / "publish")])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected argparse to reject colliding output names")

    assert not (tmp_path / "publish").exists()
