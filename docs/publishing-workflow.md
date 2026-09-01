# Publishing workflow

`imgconvert` and `ll_flask_app` have separate responsibilities on purpose.

## Boundary

`imgconvert` owns **source preparation**:

```text
edited photograph
       |
       v
   imgconvert
       |
       v
canonical source WebP
```

`ll_flask_app` owns **site publication**:

```text
canonical source WebP
       |
       +--> site content model / intrinsic geometry
       |
       +--> 480 / 800 / 1200 / 1600 build-time derivatives
       |
       +--> NGINX static publication
       v
browser
```

The converter does not need to know Flask routes, gallery templates, Docker images, Cloudflare, or deployment environments. The website does not need to know how the photographer exported a JPEG/TIFF before publication.

## Recommended manual sequence

1. Finish exposure, crop, color, retouching, and RAW development in the photo editor.
2. Export an RGB JPEG, PNG, TIFF, or WebP.
3. Run a released `imgconvert` executable against the edited export.
4. Review the reported dimensions/file-size change and visually inspect the WebP at 100% and normal browser size.
5. Copy the accepted WebP into the website's active category directory.
6. Add/update the corresponding `site_content.py` entry and record the exact width/height printed by `imgconvert` (or returned by `--json`).
7. Run `python scripts/build_responsive_images.py --check` in `ll_flask_app`.
8. Run the website test suite and normal PR workflow.
9. The website build creates responsive derivatives; do not commit those derivatives manually.

The publication workflow is intentionally manual at the repository boundary. A photograph is editorial content and should receive a human visual review before it becomes website source material.

## Source sizing

The default publication source is capped at 3200 pixels wide. This is intentionally larger than the website's largest generated derivative (1600 px), leaving a higher-resolution terminal `srcset` candidate without automatically committing the full camera export.

No image is ever upscaled. `--no-resize` keeps the oriented input dimensions when a particular photograph needs the original width.

The source cap is a publishing default, not an artistic rule. If the website layout or display strategy changes, update this value deliberately and test the resulting source sizes rather than accumulating one-off magic numbers.

## Metadata boundary

The checked-in WebP is public content, so its metadata is treated as public too.

`imgconvert` applies orientation to pixels, preserves a compatible ICC profile, discards inherited EXIF/XMP, writes controlled creator/copyright fields, and verifies that GPS metadata is absent.

The website's responsive builder independently applies the same privacy principle to generated derivatives. This defense in depth means both the checked-in source and generated responsive copies have a deliberate public metadata contract.

## Naming

The output filename uses the input stem. `imgconvert` does not invent descriptive titles or slugs because that is editorial information, not image-processing information.

Rename the edited export before conversion when a descriptive public filename is desired. Batch inputs that would map to the same output stem are rejected rather than silently overwriting one another.

## What does not cross this boundary

`imgconvert` does not modify `ll_flask_app`, commit files, create responsive variants, publish Docker images, or deploy the website. Conversely, the website build does not normalize the photographer's original editor export into the canonical checked-in source.
