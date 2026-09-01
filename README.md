# imgconvert

`imgconvert` prepares edited photographs for publication on [Lukeseppe.com](https://www.lukeseppe.com/).

The old version of this repository was a long-running Bash/ImageMagick daemon in Docker. The current design is intentionally smaller: a local Python CLI processes one or more photographs, writes publication-ready WebP sources, and exits.

## What it does

For each input photograph, `imgconvert`:

- validates that the decoded image is a supported single-frame raster format
- rejects unexpectedly large inputs before they can consume unbounded resources
- applies EXIF orientation so the published pixels have normal orientation
- preserves a compatible ICC color profile
- removes inherited camera/editor EXIF and XMP metadata
- writes controlled creator and copyright metadata
- removes GPS/location metadata from the public result
- downsizes images wider than 3200 px by default without ever upscaling
- encodes a high-quality WebP source
- verifies the generated WebP before publication
- writes atomically and refuses to overwrite an existing output unless explicitly requested
- leaves the original photograph untouched

The default 3200 px source width gives the website room above its generated 1600 px responsive candidate without committing full camera-resolution files by default. Use `--no-resize` when the original dimensions are intentionally required.

## Why Python + Pillow

This tool is image-publishing glue, not an image-processing service. Python and Pillow provide the required WebP, EXIF, XMP, ICC, orientation, validation, and test support directly without a Docker daemon, filesystem watcher, ImageMagick subprocess, or custom concurrency layer.

Go or Rust would make sense if this became a distributed service or needed a single self-contained binary. That is not the current requirement.

## Supported inputs

The publication path accepts decoded JPEG, PNG, TIFF, and WebP files. CMYK and other unusual pixel modes are rejected instead of being silently color-converted with an incompatible profile; export those photographs as RGB from the editing application first.

RAW development is deliberately out of scope. Perform artistic edits and RAW processing in Lightroom, Darktable, Capture One, RawTherapee, or another photo editor before using `imgconvert`.

## Install

Python 3.13 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

The installed command is `imgconvert`.

## Usage

Convert one photograph:

```bash
imgconvert ~/Pictures/exports/city-at-night.jpg
```

Convert a batch:

```bash
imgconvert ~/Pictures/exports/*.jpg
```

By default outputs are written under `./publish/` using the input stem and a `.webp` extension.

Useful options:

```bash
imgconvert photo.jpg --output-dir ./ready
imgconvert photo.jpg --max-width 2400
imgconvert photo.jpg --no-resize
imgconvert photo.jpg --quality 92
imgconvert photo.jpg --overwrite
imgconvert photo.jpg --json
```

`--json` prints publication geometry and file-size information that is convenient when updating the website content model.

## Website handoff

`imgconvert` creates the canonical source WebP only. It does **not** create the website's responsive image set.

The intended workflow is:

1. finish artistic edits and export an RGB photograph
2. run `imgconvert`
3. visually inspect the generated WebP
4. copy it into the appropriate `ll_flask_app/www.lukeseppe.com/static/images/<category>/` directory
5. add/update the photograph and intrinsic dimensions in `site_content.py`
6. run the website's source validation/tests
7. let the website build generate its own responsive 480/800/1200/1600 derivatives

See [`docs/publishing-workflow.md`](docs/publishing-workflow.md) for the complete boundary between the two repositories.

## Security model

This is a local manual publishing tool, not an upload service and not a sandbox for hostile internet files. It still applies file-type, byte-size, pixel-count, metadata, and output-integrity controls because image decoders are native-code attack surfaces.

See [`docs/security.md`](docs/security.md).

## Development

```bash
python -m pip install -r requirements-dev.txt -e . --no-deps
pytest
ruff check src tests
bandit -q -r src
pip-audit -r requirements.txt
```

## License

MIT. See [LICENSE](LICENSE).
