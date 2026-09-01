# Development

## Source environment

Python 3.13+ is supported; CI tests 3.13 and 3.14.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python -m pip check
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
```

## Dependency files

The dependency boundaries are intentional:

- `requirements.txt` — runtime code required by the converter (`Pillow`)
- `requirements-build.txt` — runtime dependency plus the closed, pinned PyInstaller toolchain used to make standalone executables
- `requirements-dev.txt` — runtime dependency plus pinned test/security/lint tools
- `pyproject.toml` — project metadata and pinned source-build backend

Direct tool versions are exact so Dependabot PRs represent real toolchain changes instead of changes to a permissive lower bound that CI was already resolving past.

## Local checks

```bash
python -m pytest --cov=imgconvert --cov-report=term-missing --cov-fail-under=85
ruff check src tests scripts
bandit -q -r src scripts
pip-audit -r requirements.txt
pip-audit -r requirements-build.txt
python -m imgconvert --version
```

## Build a local standalone executable

Install the build toolchain in a clean environment:

```bash
python -m pip install --no-deps --only-binary=:all: -r requirements-build.txt
python -m pip check
```

Then build and verify a platform-local artifact directly from the checked-out source tree:

```bash
python scripts/build_executable.py --artifact-name imgconvert-local
python scripts/verify_executable.py release/imgconvert-local
```

On Windows use an artifact name ending in `.exe`.

A local build is useful for debugging but is not a substitute for the four-platform GitHub Actions **Standalone build** matrix used for releases.

## Versioning

`src/imgconvert/__init__.py` is the version source of truth. `pyproject.toml` reads it dynamically.

For a release-bearing change:

1. choose the next semantic version
2. update `__version__`
3. update documentation when behavior/distribution changes
4. open a PR
5. require source CI and all Standalone build checks to pass
6. merge to `master`
7. create the exactly matching `vMAJOR.MINOR.PATCH` tag
8. let the tag-triggered **Build & Release** workflow create the GitHub Release

The workflow rejects mismatched or non-stable version tags.

## Release scripts

Files under `scripts/` participate in CI linting, compilation, and Bandit SAST because they execute inside the trusted release pipeline. Treat changes to executable-build/checksum/tag-validation scripts as supply-chain changes, not convenience scripting.
