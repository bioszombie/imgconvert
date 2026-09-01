# Security model

## Scope

`imgconvert` is a local, manually invoked publishing utility. It is not a web application, upload endpoint, network daemon, file-watching service, or multi-user system.

That distinction matters when applying OWASP guidance. Authentication, session, CSRF, browser-header, SSRF, and other web-application controls are not applicable. The relevant risks are unsafe parsing of complex image files, filesystem mistakes, resource exhaustion, metadata privacy, dependency compromise, and accidental publication of the wrong artifact.

## Trust boundary

The expected input is a photograph intentionally exported by the photographer from a trusted editing workflow. The tool is **not a security sandbox for arbitrary hostile internet files**.

Even trusted workflows can produce malformed files, and native image codecs periodically receive security fixes, so the converter still fails closed around its parsing boundary.

## File-processing controls

The converter:

- validates the decoded image format instead of trusting the filename extension
- accepts only JPEG, PNG, TIFF, and WebP publication inputs
- rejects animated/multi-frame input
- rejects symbolic-link input
- limits compressed input size to 256 MiB
- configures Pillow's decompression-bomb pixel limit at 100 megapixels
- treats decompression-bomb warnings as errors
- rejects unsupported color modes rather than silently applying a potentially incorrect profile conversion
- never executes content from the image
- never deletes or mutates the source file
- writes only WebP output
- refuses overwrite by default
- writes to a temporary file, verifies it, and atomically publishes it

These controls align with the file-validation, size-limit, safe-storage, and least-surprise principles normally applied to upload processing without pretending this CLI is an upload service.

## Metadata/privacy controls

Publication output must not accidentally disclose camera location or editing metadata.

The converter:

- applies EXIF orientation to the pixel data
- does not inherit input EXIF
- does not inherit input XMP
- preserves an ICC profile only when it remains compatible with the RGB/RGBA pixel representation
- writes controlled Artist/Copyright metadata
- writes controlled XMP creator/rights metadata
- verifies that GPS metadata is absent before the temporary output is atomically renamed into place

## Resource model

The CLI processes files sequentially. There is no worker pool, background queue, watcher, or daemon. Sequential execution is intentional for the manual publication workflow and places an obvious upper bound on simultaneous decoder/encoder work.

## Dependency model

Pillow is the only runtime dependency and is pinned in `requirements.txt`. Development/security tooling is separate in `requirements-dev.txt`. Dependabot watches both Python dependencies and GitHub Actions.

CI validates Python 3.13 and 3.14, tests converter behavior, runs Ruff and Bandit, scans tracked source for potential secrets, and audits the runtime dependency set.

## Containers

Docker is not part of the runtime design. Requiring a container solely to invoke a local image conversion library would add a base operating system, package manager, bind mounts, UID/GID behavior, image patching, and daemon dependency without improving the normal trusted-photo workflow.

If a future use case requires processing hostile files, design an explicit sandbox for that threat model rather than assuming this local CLI is one.
