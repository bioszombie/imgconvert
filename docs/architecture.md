# Architecture

## Purpose

`imgconvert` is a photographer-facing publication-preparation utility. Its job ends when it has produced one canonical WebP source suitable for review and check-in to `ll_flask_app`.

It is deliberately **not** a service, daemon, upload endpoint, image library, asset database, or deployment component.

## System boundary

```text
photo editor / RAW developer
          |
          | edited RGB JPEG/PNG/TIFF/WebP
          v
      imgconvert
          |
          | canonical publication WebP
          v
     human review
          |
          v
     ll_flask_app
          |
          +--> site_content.py owns editorial metadata and geometry
          +--> build creates responsive derivatives
          +--> NGINX serves static photography
          v
        browser
```

The boundary prevents duplicated responsibilities. `imgconvert` does not know Flask routes or responsive layouts. The website does not know how a camera RAW file was edited or how the canonical source was normalized.

## Runtime architecture

The converter is a single-shot CLI:

1. parse explicit input paths and options
2. decode and validate one photograph
3. normalize orientation and public metadata
4. optionally resize without upscaling
5. encode a temporary WebP
6. reopen and verify the encoded artifact
7. atomically publish the final path
8. continue to the next requested photograph, then exit

There is no watcher, background queue, network listener, worker pool, persistent process, or source-deletion lifecycle.

## Technology choices

### Python + Pillow

Image decoding/encoding and metadata handling dominate this tool's problem space. Pillow directly provides WebP, EXIF, XMP, ICC, orientation, resizing, and decoder safety controls while keeping orchestration small and testable.

Go or Rust would reduce dependence on a Python runtime only if the program were distributed from source. The release model instead bundles the tested Python runtime and Pillow with PyInstaller, so release users do not manage Python environments.

### PyInstaller for distribution

PyInstaller is a **distribution boundary**, not the application architecture. Source remains normal Python. CI builds a native launcher plus bundled interpreter/application dependencies separately on each target operating system.

The executable is not equivalent to a Go/Rust fully native compilation, but operationally it gives the desired property: a release user invokes one file and does not install Python or Pillow.

### No Docker

Docker solved the wrong problem for this manual workflow. It added a base OS, package manager, daemon, bind mounts, UID/GID behavior, container patching, and lifecycle complexity solely to execute a local conversion command.

If the threat model later changes to hostile internet-supplied files, design an explicit sandbox then rather than reintroducing containers by default.

## Source of truth

`src/imgconvert/__init__.py` owns the application version. Python package metadata reads that value dynamically. Release tags must match it exactly.

`requirements.txt` owns the runtime dependency set. `requirements-build.txt` owns the standalone-build toolchain. `requirements-dev.txt` owns test/security tooling.

## Quality boundaries

Source CI validates Python 3.13 and 3.14, unit/integration behavior, coverage, Ruff, Bandit, secret detection, and dependency audits.

Package CI independently builds and executes the actual one-file artifact on Linux x86-64, Windows x86-64, macOS Intel, and macOS Apple Silicon. A release therefore depends on the packaged behavior, not on the assumption that source tests imply packaging correctness.
