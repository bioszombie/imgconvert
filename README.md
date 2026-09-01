# imgconvert

`imgconvert` prepares edited photographs as publication-ready WebP source files for [Lukeseppe.com](https://www.lukeseppe.com/).

The normal user experience is a **standalone executable**. Python and Pillow are implementation details used to develop and build the tool; a release user does not need to install Python, manage a virtual environment, run Docker, or install ImageMagick.

## What it does

For each photograph, `imgconvert`:

- verifies the decoded image is a supported single-frame raster format
- limits compressed bytes and decoded pixel count
- applies EXIF orientation to the pixels
- preserves a compatible ICC color profile
- removes inherited EXIF/XMP and GPS/location metadata
- writes controlled creator/copyright metadata
- downsizes images wider than 3200 px by default and never upscales
- encodes WebP at quality 90 by default
- reopens and verifies the generated WebP
- publishes output atomically and refuses overwrite unless `--overwrite` is explicit
- never deletes or mutates the original photograph

The result is the **canonical source WebP** checked into the photography website. `ll_flask_app` remains responsible for its own responsive 480/800/1200/1600 derivatives.

## Install a release

Download the asset for your platform from the repository's **Releases** page:

| Platform | Release asset |
| --- | --- |
| Linux x86-64 | `imgconvert-linux-x86_64` |
| Windows x86-64 | `imgconvert-windows-x86_64.exe` |
| macOS Intel | `imgconvert-macos-x86_64` |
| macOS Apple Silicon | `imgconvert-macos-arm64` |

Linux and macOS downloads need executable permission after download:

```bash
chmod +x imgconvert-linux-x86_64
./imgconvert-linux-x86_64 --version
```

Optionally rename/install it on your `PATH` as `imgconvert`.

On Windows, run the downloaded `.exe` directly or place it in a directory on `PATH`:

```powershell
.\imgconvert-windows-x86_64.exe --version
```

Released executables bundle the Python runtime, Pillow, and the application. No system Python environment is required.

> Windows binaries are not Authenticode-signed and macOS binaries are not Apple-notarized. GitHub provenance and checksums establish where the release artifact came from; they are not substitutes for Microsoft/Apple code signing. See [`docs/distribution.md`](docs/distribution.md).

## Verify a release

Every release includes `SHA256SUMS`, and the release binaries/checksum manifest receive GitHub artifact provenance attestations.

With GitHub CLI installed, verify provenance with:

```bash
gh attestation verify ./imgconvert-linux-x86_64 -R bioszombie/imgconvert
```

You can also compare the file's SHA-256 digest with `SHA256SUMS` before running it.

## Usage

Convert one photograph:

```bash
imgconvert photo.jpg
```

Convert several photographs:

```bash
imgconvert photo-1.jpg photo-2.jpg photo-3.tif
```

By default output is written to `./publish/` using each input stem and a `.webp` extension.

Useful options:

```bash
imgconvert photo.jpg --output-dir ./ready
imgconvert photo.jpg --max-width 2400
imgconvert photo.jpg --no-resize
imgconvert photo.jpg --quality 92
imgconvert photo.jpg --overwrite
imgconvert photo.jpg --json
imgconvert --version
```

`--json` reports exact publication geometry and byte counts, which is useful when updating the website content model.

## Supported inputs

The publication path accepts decoded JPEG, PNG, TIFF, and WebP files. Animated/multi-frame files, symbolic-link inputs, CMYK, and unsupported pixel modes are rejected rather than silently transformed.

RAW development is intentionally out of scope. Finish artistic edits and RAW processing in Lightroom, Darktable, Capture One, RawTherapee, or another editor, then export an RGB publication candidate for `imgconvert`.

## Website handoff

The intended boundary is:

```text
edited RGB photograph
        |
        v
    imgconvert
        |
        v
canonical source WebP
        |
        v
   ll_flask_app
        |
        +--> content model / intrinsic geometry
        +--> responsive derivatives
        +--> web publication
```

See [`docs/publishing-workflow.md`](docs/publishing-workflow.md) for the complete manual sequence.

## Development from source

Developers need Python 3.13 or newer. Release users do not.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
pytest
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

See [`docs/development.md`](docs/development.md) for local builds, tests, dependency files, and versioning.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system boundaries and architectural rationale
- [`docs/publishing-workflow.md`](docs/publishing-workflow.md) — handoff to the photography website
- [`docs/distribution.md`](docs/distribution.md) — standalone builds, releases, checksums, provenance, and platform signing status
- [`docs/security.md`](docs/security.md) — threat model and security controls
- [`docs/development.md`](docs/development.md) — source development and release preparation

## License

MIT. See [LICENSE](LICENSE).
