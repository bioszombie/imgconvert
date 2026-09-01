# Security model

## Scope

`imgconvert` is a local, manually invoked publishing utility. It is not a web application, upload endpoint, network daemon, file-watching service, or multi-user system.

That distinction matters when applying OWASP guidance. Authentication, session, CSRF, browser-header, SSRF, and other web-application controls are not applicable. Relevant risks are unsafe parsing of complex image files, filesystem mistakes, resource exhaustion, metadata privacy, dependency/build compromise, and accidental publication of the wrong artifact.

## Trust boundary

Expected input is a photograph intentionally exported by the photographer from a trusted editing workflow. The tool is **not a security sandbox for arbitrary hostile internet files**.

Even trusted workflows can produce malformed files, and native image codecs periodically receive security fixes, so the converter still fails closed around its parsing boundary.

## File-processing controls

The converter:

- validates the decoded format instead of trusting the filename extension
- accepts only JPEG, PNG, TIFF, and WebP publication inputs
- rejects animated/multi-frame input
- rejects symbolic-link input
- limits compressed input size to 256 MiB
- configures Pillow's decompression-bomb pixel limit at 100 megapixels
- treats decompression-bomb warnings as errors
- rejects unsupported color modes instead of silently applying an uncertain conversion
- never executes content from the image
- never deletes or mutates the source file
- writes only WebP output
- refuses overwrite by default, including an atomic create-if-absent publication path
- encodes to a temporary file and verifies it before publication

These controls align with file-validation, size-limit, safe-storage, and least-surprise principles normally applied to upload processing without pretending this CLI is an upload service.

## Metadata/privacy controls

The publication output is public content. The converter therefore:

- applies EXIF orientation to pixel data
- does not inherit input EXIF
- does not inherit input XMP
- preserves an ICC profile only when compatible with the resulting RGB/RGBA representation
- writes controlled Artist/Copyright metadata
- writes controlled XMP creator/rights metadata
- verifies GPS metadata is absent before final publication

## Resource model

The CLI processes files sequentially. There is no worker pool, background queue, watcher, or daemon. Sequential execution is intentional for the manual workflow and places an obvious upper bound on simultaneous decoder/encoder work.

## Dependency and build model

Pillow is the only runtime dependency and is exactly pinned in `requirements.txt`. PyInstaller is isolated in `requirements-build.txt`. Development/security tooling is isolated in `requirements-dev.txt`. The setuptools build backend is also version controlled.

Dependabot watches Python dependencies and GitHub Actions. Source CI audits both runtime and standalone-build requirements. Release scripts are compiled, linted, and included in Bandit SAST because they are part of the trusted build path.

## Standalone executable boundary

Release executables are built independently on Linux, Windows, macOS Intel, and macOS Apple Silicon. Each packaged executable is executed in CI against a real JPEG-to-WebP fixture and its output contract is revalidated.

PyInstaller bundles a Python runtime and dependencies. This removes target-machine Python drift; it does not transform Python into memory-safe native application code or eliminate vulnerabilities in Pillow/native codecs.

PyInstaller one-file executables extract their runtime into a temporary directory at startup. The program still runs with the invoking user's privileges and should not be run elevated merely to convert a photograph.

## Release supply chain

Stable release tags must exactly match the internal semantic version and point to a commit reachable from `master`. All platform builds must succeed before release publication.

Tagged releases include SHA-256 checksums and GitHub/Sigstore build-provenance attestations. Attestations bind artifact hashes to the repository/workflow that produced them; they are evidence of provenance, **not a claim that the binary is vulnerability-free**.

Release workflow write permissions are limited to the release job. Ordinary source/package build jobs remain read-only.

## OS signing

Current Windows releases are not Authenticode-signed. Current macOS releases are not Apple Developer ID signed/notarized. Operating-system reputation/Gatekeeper warnings are therefore possible.

GitHub provenance must not be described as equivalent to Microsoft or Apple code signing. If distribution expands beyond the owner's machines, add protected platform signing credentials as a separate control.

## Network and update behavior

The converter has no application network functionality, telemetry, update check, or self-updater. Updating is an explicit operator action through GitHub Releases.

## Containers

Docker is not part of the runtime design. Requiring a container solely to invoke a local image conversion library would add a base OS, package manager, bind mounts, UID/GID behavior, image patching, and daemon dependency without improving the normal trusted-photo workflow.

If a future use case requires processing hostile files, design an explicit sandbox for that threat model rather than assuming this local CLI is one.
