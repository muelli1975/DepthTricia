# Development status

This is the initial implementation, not a validated Windows release.

Implemented: the inherited SplatTricia interface and stereo controls; local
DA2 Small, DA3 Mono Large and Depth Pro loading; resolution/edge presets;
mlbw_l2_inpaint with light_inpaint_v1; SBS/anaglyph JPEG output; depth caching;
explicitly confirmed, checksum-verified model downloads; portable Windows build.
The supplied icon and original ready.wav are preserved byte for byte.

## Verified locally

- Thirteen regression tests cover depth normalization, width-based deviation,
  window backshift, cache invalidation, download consent, checksum failure and
  cancellation, automatic CPU/CUDA selection and verified runtime installation.
- A complete CPU run with DA2 Small at depth resolution 1218 generated both
  stereo/anaglyph outputs with the real inpainting models. A second run reused
  the saved depth map without loading the depth model.
- DA3 Mono Large completed the same CPU depth/stereo/inpainting output path
  at 1218. A smaller 392-depth inference was checked separately.
- GUI startup and preset editing were checked on a headless Linux display.
- Test inference used already downloaded local weights with runtime network
  connections blocked. No model account, token or online loader was needed.

These checks use a synthetic image, not a representative quality benchmark.
CPU timing on this development host does not predict target Windows timing.

## Required before a public release

- Validate Windows 10/11 on user hardware and NVIDIA/CUDA inference.
- Run DA3 at 2048 and Depth Pro on suitable target hardware. Full-precision
  Depth Pro CPU inference exceeded this test environment's 8 GiB RAM limit;
  it remains unverified here. Its native inference path is preserved.
- Compare foreground boundaries, thin objects, sky and disocclusion filling
  against iw3 on representative photos, including portrait orientations.
- Validate online runtime/model downloads from the published release and
  interrupted installation on target machines.

## Verified Windows package

Build [38527703368](https://github.com/muelli1975/DepthTricia/actions/runs/38527703368)
at source `be27d6a6b93cf264cab00163e6667b4f9f831907` passed all 13 tests and
the frozen executable smoke test. The GUI started before runtime installation;
verified local runtime ZIPs were installed, then DA2 CPU inference, stereo
inpainting, output dimensions, metadata and cache reuse succeeded offline.
DA3 configuration and Depth Pro imports also passed; these are not full
Depth Pro or CUDA inference tests.

| Asset | Size (decimal MB) |
| --- | ---: |
| DepthTricia_1.0.zip, with DA2 and DA3 | 1666.6 |
| DepthTricia_Runtime_1.0_01.zip | 644.6 |
| DepthTricia_Runtime_1.0_02.zip | 740.2 |
| DepthTricia_Runtime_1.0_03.zip | 494.1 |
| DepthTricia_Runtime_1.0_04.zip | 490.5 |

All five ZIP files are below the individual GitHub release-asset limit.

## Hardware and numerical policy

Use the established upstream model implementations and inpainting. No custom
depth tiling, patch batching or quantization. CPU inference uses float32;
CUDA precision follows the corresponding upstream inference implementation.
The selected depth resolution is rounded upward to the model's required
multiple of 14. Depth Pro uses its native model resolution.

The depth model is released before the stereo/inpainting model is loaded.
Images are processed sequentially; depth maps are stored on disk and reused
for changed stereo settings. Depth Pro checkpoint loading uses PyTorch's
documented mmap option; this changes loading, not inference mathematics.

There is no automatic quality reduction after an out-of-memory error. The
user can explicitly choose DA2 Small or a lower-resolution preset instead.
The inherited SplatTricia working-image height limit remains 2160 pixels;
depth resolution and output-image resolution are separate settings.

## Deviation calibration

`scripts/check_deviation.py` measures the actual CPU stereo/inpainting renderer
using horizontal intensity ramps and separate constant depth endpoints (0/1).
The median difference is measured in the image interior, before uint8/JPEG.
With 15 permille, window 100% and no backshift:

| Image | Target span | Measured span | Measured permille |
| --- | ---: | ---: | ---: |
| Landscape, width 1024, depth width 1218 | 15.360 px | 15.304 px | 14.945 |
| Portrait, width 256, depth height 1218 | 3.840 px | 3.821 px | 14.925 |

These results validate the width-based conversion in the controlled test,
not exact disparity of every feature in a real photo. Learned backward warping,
occlusion boundaries, inpainting and JPEG affect correspondence measurement.
No experimental calibration correction is applied to upstream warping.

## Portable runtime split

The first complete CUDA ZIP exceeded GitHub's 2 GiB individual release-asset
limit even without DA3. The common application now groups its matching large
runtime files into normal ZIP assets under that limit. Files are not altered,
and no CPU/CUDA binary mixing or numerical changes are involved.

The GUI asks before installing missing runtime files. Verified local ZIPs are
used before downloads. Every archive and extracted file is checked against
the build manifest; cancellation leaves previously installed files intact
within the current archive. Partially completed installations can be retried.
The Windows workflow starts the frozen GUI before restoring the runtime from
local ZIPs, then exercises CPU inference and metadata/cache handling. Its
actual result must be checked before describing the package as validated.

The online URLs target a future `v1.0` release. Until matching assets are
published, development testers must supply the local ZIPs from the artifact.

The complete distribution now also supplies the original Apple CDN Depth Pro
checkpoint in `DepthTricia_Models_DepthPro_1.0.zip`. The package manifest pins
its known size/SHA-256; only this specific model path is allowed alongside the
runtime library paths. Local packages are preferred, installed archives are
verified without re-downloading, and the GUI does not request a second model
download for a checkpoint already provided by the confirmed package setup.
The frozen smoke test checks checkpoint installation and SHA-256, but remains
an inference test of DA2, not full Depth Pro inference. The earlier five-ZIP
size table above records the previous build without the Depth Pro model ZIP.

Pushes to main run source checks and create a Windows development artifact.
The workflow does not publish a stable release automatically.

Output additions: the Original size checkbox selects target_height=0; the
default remains 2160. The optional depth PNG directly quantizes the used
normalized disparity to 16-bit grayscale without resizing or modifying the
float32 NPY cache. Export and filename options do not invalidate the cache;
changing the image working size does. Settings filenames include a fixed
ASCII model tag. Model-standard labels share the inference defaults and
update on model changes, with Depth Pro's fixed resolution disabled.
The frozen smoke test covers these controls, the 1100/1280-wide header, preset
resolution semantics, output names and PNG values/dimensions, including PNG
export on a subsequent cache hit. It writes GUI settings only to a temporary
folder, and packaging excludes settings/logs from the public ZIP.

Built-in Quick/Standard/Fine presets use resolutions 0/1218/2040 and edge fix
2/1. Their selection is stored by a language-independent builtin_preset key;
own preset values and names remain in depth_presets and are not overwritten.
Model-standard labels track model changes without replacing the stored zero.
The editable resolution field remains available for custom presets.
