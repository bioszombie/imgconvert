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

Pillow is the only runtime dependency and is exactly pinned in `requirements.txt`. Development/security tooling is isolated and exactly pinned in `requirements-dev.txt`.

The standalone release path has a separate closed dependency set in `requirements-build.txt`. It includes exact versions for pip, PyInstaller, PyInstaller's common transitive dependencies, and the macOS/Windows-specific transitive dependencies used by the native Standalone build jobs. The Build & Release workflow installs that set with `--no-deps` and `--only-binary=:all:` so an undeclared dependency or missing wheel fails closed instead of being resolved or built implicitly.

Standalone builds use exact CPython 3.14.7. They build directly from the checked-out `src/` tree, so the release path does not create an isolated project-build environment or an intermediate application wheel. `pip check` verifies the installed locked set before PyInstaller runs.

Dependabot watches Python dependencies and GitHub Actions. Source CI audits runtime and standalone-build requirements. Release scripts are compiled, linted, and included in Bandit SAST because they are part of the trusted build path.

## Standalone executable boundary

Release executables are built independently on Linux, Windows, macOS Intel, and macOS Apple Silicon. Each standalone executable is executed in CI against a real JPEG-to-WebP fixture and its output contract is revalidated.

PyInstaller bundles a Python runtime and dependencies. This removes target-machine Python drift; it does not transform Python into memory-safe native application code or eliminate vulnerabilities in Pillow/native codecs.

PyInstaller one-file executables extract their runtime into a temporary directory at startup. The program still runs with the invoking user's privileges and should not be run elevated merely to convert a photograph.

## Release supply chain

Stable release tags must exactly match the internal semantic version and point to a commit reachable from `master`. All platform Standalone build jobs must succeed before release publication.

Browser/manual releases are dispatched from `master` with a requested semantic version. The workflow validates the requested version against `imgconvert.__version__`, runs all four standalone builds, and only then creates the matching version tag on the exact workflow commit. This ordering prevents a failed build from leaving behind a release tag without validated release artifacts.

Local version-tag pushes remain supported. Both release paths converge on the same checksum, attestation, and GitHub Release publication steps.

The Python portion of the standalone build is version-locked, but the project does not claim byte-for-byte reproducibility. GitHub-hosted runner images and their operating-system toolchains remain provider-managed inputs. Published checksums identify the exact release artifacts, while GitHub/Sigstore attestations bind those artifact hashes to the repository and workflow that produced them.

Release workflow write permissions are limited to the release job. Ordinary source/standalone-build jobs remain read-only. The manual release path uses the repository `GITHUB_TOKEN`; no long-lived personal access token or release secret is required.

Repository branch protection is an external governance control, not something a workflow can safely emulate. `master` should require pull requests plus the source and Standalone build checks before merge and should reject force-push/deletion bypasses. The release workflow's `master` ancestry check is defense in depth and must not be interpreted as proof that a commit passed review.

Published version tags are immutable by policy: an existing tag is never moved or reused. A correction receives a new semantic version.

GitHub Releases are the durable distribution channel. Actions artifacts are temporary CI evidence/handoff objects. GitHub Packages is intentionally not part of the release design because this project does not need a registry-native package format.

## OS signing

Current Windows releases are not Authenticode-signed. Current macOS releases are not Apple Developer ID signed/notarized. Operating-system reputation/Gatekeeper warnings are therefore possible.

GitHub provenance must not be described as equivalent to Microsoft or Apple code signing. If distribution expands beyond the owner's machines, add protected platform signing credentials as a separate control.

## Network and update behavior

The converter has no application network functionality, telemetry, update check, or self-updater. Updating is an explicit operator action through GitHub Releases.

## Containers

Docker is not part of the runtime design. Requiring a container solely to invoke a local image conversion library would add a base OS, package manager, bind mounts, UID/GID behavior, image patching, and daemon dependency without improving the normal trusted-photo workflow.

If a future use case requires processing hostile files, design an explicit sandbox for that threat model rather than assuming this local CLI is one.
