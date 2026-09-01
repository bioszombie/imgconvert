# Distribution and releases

## Goal

Release users should not need to synchronize Python versions, virtual environments, Pillow wheels, or build tools. GitHub Releases are therefore the primary distribution channel.

Python packaging remains useful for development, but it is not the normal installation contract.

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

## What is bundled

The one-file executable contains the PyInstaller bootloader, a Python runtime, `imgconvert`, Pillow, and the native libraries/plugins needed by the selected Pillow wheel.

The application still behaves as a local CLI. Bundling does not add a server, background process, updater, or network dependency.

PyInstaller one-file executables extract their bundled runtime into a temporary location during process startup and remove it when the process exits normally. That startup detail is accepted in exchange for a single distributable file.

## Package validation

The `Package` workflow runs for pull requests, `master`, version tags, and manual dispatches. Every matrix build must:

1. install the pinned release build inputs
2. build a one-file executable
3. run `--version` from that executable
4. use that executable to convert a real JPEG fixture to WebP
5. verify orientation normalization
6. verify output geometry and single-frame WebP format
7. verify controlled Artist/Copyright/XMP metadata
8. verify private EXIF/GPS absence
9. verify compatible ICC preservation
10. upload the proven executable as a workflow artifact

This specifically tests packaging completeness such as Pillow WebP codec/plugin inclusion.

## Release trigger

Stable releases use tags in the form `vMAJOR.MINOR.PATCH`.

The release job fails unless:

- the tag is valid stable SemVer
- the tag exactly matches `imgconvert.__version__`
- the tagged commit is reachable from `master`
- every platform package job succeeds

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

Dependabot proposes updates to the runtime, build, development, and GitHub Actions dependencies. Those changes must pass both source CI and package CI before they reach a release.
