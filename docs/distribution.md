# Distribution and releases

## Goal

Release users should not need to synchronize Python versions, virtual environments, Pillow wheels, or build tools. GitHub Releases are therefore the primary distribution channel.

Python packaging remains useful for development, but it is not the normal installation contract.

## Distribution channels

`imgconvert` uses three different GitHub concepts for different purposes:

- **GitHub Actions artifacts** are temporary CI outputs used to move and inspect tested executables during a workflow run.
- **GitHub Releases** are the durable, versioned distribution channel for end users.
- **GitHub Packages** is intentionally unused. The project does not publish a container, npm package, NuGet package, or other registry-native artifact merely to populate the Packages section.

A successful pull request or `master` build therefore does not create a public downloadable release. Durable publication happens only from a valid version tag after all release gates pass.

## Supported release assets

Each release builds these artifacts on the matching GitHub-hosted architecture:

| Artifact | Build runner | Architecture |
| --- | --- | --- |
| `imgconvert-linux-x86_64` | Ubuntu 22.04 | x86-64 |
| `imgconvert-windows-x86_64.exe` | Windows Server 2022 | x86-64 |
| `imgconvert-macos-x86_64` | macOS 15 Intel | x86-64 |
| `imgconvert-macos-arm64` | macOS 15 | Apple Silicon arm64 |

PyInstaller is not a cross-compiler. Each executable is produced on its own operating system/architecture rather than relabeling one build for several platforms.

Linux intentionally builds on Ubuntu 22.04 instead of `ubuntu-latest` to avoid unnecessarily raising the glibc baseline as GitHub updates its newest runner image.

## Locked release-build inputs

Standalone executables are built with CPython **3.14.7** on every platform. The Python package closure used by PyInstaller is declared in `requirements-build.txt`:

- the runtime Pillow pin is included from `requirements.txt`
- pip and PyInstaller are exact-version pins
- PyInstaller's common transitive dependencies are exact-version pins
- macOS-only and Windows-only dependencies use explicit environment markers
- the Build & Release workflow installs the file with `--no-deps`, so pip cannot silently resolve an undeclared transitive package
- the Build & Release workflow requires binary distributions with `--only-binary=:all:`, so a missing supported wheel fails instead of executing an unexpected source build

After installation, `pip check` verifies that the closed set satisfies the declared dependency relationships. If a future PyInstaller version adds or changes a dependency, standalone-build CI fails until the lock is updated deliberately.

The standalone-build workflow builds directly from the checked-out `src/` tree. It does not run `pip install .` first, so release packaging does not create a second isolated setuptools environment or an intermediate project wheel.

`pyproject.toml` still pins the setuptools backend because source/development packaging remains supported, but that build path is separate from the standalone executable path.

## Reproducibility boundary

The release workflow fixes the CPython patch level and all Python packages involved in the standalone build. That prevents dependency-version drift between release runs.

It does **not** claim byte-for-byte reproducible executables. GitHub-hosted runner images and their operating-system toolchains are provider-managed inputs, and PyInstaller/native-library output can contain platform-specific build details. A release's SHA-256 checksums and provenance attestations identify the exact artifacts that were produced and published.

If byte-reproducible builds ever become a requirement, the runner/toolchain layer would need a separately controlled build environment rather than overstating what hosted runners provide.

## What is bundled

The one-file executable contains the PyInstaller bootloader, a Python runtime, `imgconvert`, Pillow, and the native libraries/plugins needed by the selected Pillow wheel.

The application still behaves as a local CLI. Bundling does not add a server, background process, updater, or network dependency.

PyInstaller one-file executables extract their bundled runtime into a temporary location during process startup and remove it when the process exits normally. That startup detail is accepted in exchange for a single distributable file.

## Standalone build validation

The **Build & Release** workflow runs for pull requests, `master`, version tags, and manual dispatches. Every matrix build must:

1. provision CPython 3.14.7
2. install the exact closed release-build package set without dependency resolution or source builds
3. pass `pip check`
4. build a one-file executable directly from the checked-out source tree
5. run `--version` from that executable
6. use that executable to convert a real JPEG fixture to WebP
7. verify orientation normalization
8. verify output geometry and single-frame WebP format
9. verify controlled Artist/Copyright/XMP metadata
10. verify private EXIF/GPS absence
11. verify compatible ICC preservation
12. upload the proven executable as a temporary Actions artifact

This specifically tests standalone-build completeness such as Pillow WebP codec/plugin inclusion.

## Release trigger

Stable releases use tags in the form `vMAJOR.MINOR.PATCH`.

The release job fails unless:

- the tag is valid stable SemVer
- the tag exactly matches `imgconvert.__version__`
- the tagged commit is reachable from `master`
- every platform Standalone build job succeeds

After those gates, the workflow downloads the four independently built executables, writes `SHA256SUMS`, creates GitHub build-provenance attestations, and creates the GitHub Release.

A normal release sequence is:

```bash
# after the version-bearing PR is merged and master checks are green
git switch master
git pull --ff-only
git tag v2.1.0
git push origin v2.1.0
```

Do not move/reuse a published version tag. A correction receives a new version.

The release workflow's `master` ancestry test is defense in depth, not a substitute for repository governance. Protect `master` with required source/standalone-build checks so reviewed code cannot be bypassed by a direct push before a release tag is created.

## Checksums

`SHA256SUMS` contains one SHA-256 digest per release executable. Verify the downloaded file against that manifest before execution when integrity matters.

Examples:

```bash
sha256sum imgconvert-linux-x86_64
```

```powershell
Get-FileHash .\imgconvert-windows-x86_64.exe -Algorithm SHA256
```

## Build provenance

Tagged releases use GitHub artifact attestations backed by Sigstore. The attestation links the artifact digest to the GitHub repository/workflow that built it.

Verify online with GitHub CLI:

```bash
gh attestation verify ./imgconvert-linux-x86_64 -R bioszombie/imgconvert
```

Attestation proves build provenance; it does **not** prove that the program is vulnerability-free or that the photograph is safe to parse.

## OS code-signing status

The current release process does not hold commercial/OS signing identities:

- Windows executables are not Authenticode-signed.
- macOS executables are not signed with an Apple Developer ID and are not notarized.

Windows SmartScreen or macOS Gatekeeper may therefore require explicit user review/approval. Do not confuse GitHub/Sigstore provenance with Microsoft or Apple trust UI.

If broad third-party desktop distribution becomes a goal, add OS-native signing/notarization as a separate security/release project with protected signing credentials. It is not necessary to pretend those credentials exist for this personal publishing tool.

## Updating

There is no self-updater and the executable makes no network request to check for updates. Update deliberately by downloading a newer release, verifying it, and replacing the existing executable.

Dependabot watches the explicitly declared runtime, release-build, development, and GitHub Actions dependencies. An update that changes the release-build dependency closure must update the lock and pass all native Standalone build jobs before it can reach a release.
