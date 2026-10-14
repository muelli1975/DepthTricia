# Development status

## Scene setback correction

Nonzero window_back_permille translates both float stereo views and their
postprocessed hole masks before LightInpaintV1 inference. Each eye moves by
half the requested width-based pixel disparity: left content moves left,
right content moves right. Fractional pixels are retained. Out-of-source
samples are explicitly marked as holes and filled together with internal
disocclusions. No black-border translation is applied to completed outputs.
The zero-backshift path uses the unchanged upstream MLBWInpaintImage.infer.
The depth cache, deviation, floating-window curtains and model precision stay
unchanged. Tensor checks cover translation/masks and inpainting call order;
the frozen smoke test measures near/far endpoints in landscape and portrait.
These checks must pass before the paused 1.0 release is published.
The near-point label includes the additional setback and displays its distance
behind the window when the value is positive; this is checked in DE/EN.

Validation notes for DepthTricia 1.0. Target-hardware results remain separate
from the automated Windows package checks below.

Implemented: the inherited SplatTricia interface and stereo controls; local
DA2 Small, DA3 Mono Large and Depth Pro loading; resolution/edge presets;
mlbw_l2_inpaint with light_inpaint_v1; SBS/anaglyph JPEG output; depth caching;
explicitly confirmed, checksum-verified model downloads; portable Windows build.
The supplied icon and original ready.wav are preserved byte for byte.

## Verified locally

- Regression tests cover depth normalization, width-based deviation,
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

## Measured CPU stages, 2026-10-14

`scripts/benchmark_cpu.py` measures the unchanged production depth and stereo
paths in sequential fresh worker processes. Host: AMD EPYC 9V74, Linux,
8-thread CPU quota, PyTorch 2.8.0+cpu, FP32, edge fix 2/1, 15 permille,
window 100%. Eight threads are a benchmark setting, not an application cap.
Input: Depth Anything V2's public `assets/examples/demo01.jpg`, resized by
the normal image loader to 1624�1080. Medians of three calls; model loading,
JPEG saving and metadata copying are excluded from the per-image times.

| Model / resolution | Depth (s) | Stereo + inpainting (s) | LightInpaint part (s) | Depth / stereo peak process RSS (MB) |
| --- | ---: | ---: | ---: | ---: |
| DA2 Small / standard 518 | 0.72 | 2.93 | 2.40 | 801 / 1241 |
| DA3 Mono Large / standard 504 | 5.02 | 2.75 | 2.31 | 2941 / 1293 |
| DA3 Mono Large / 1218 | 53.64 | 5.37 | 2.54 | 5151 / 1308 |

The LightInpaint column times both unmodified `LightInpaintV1.infer` calls,
including their preprocessing. It is contained in the stereo column and must
not be added to it. Mask postprocessing, warping and RGB conversion are in
the remaining stereo time. RSS includes Python/PyTorch, model loading and
inference buffers; the two worker peaks are separate and are not additive.
The example is a performance measurement, not a depth-quality benchmark or
a speed guarantee for older Windows CPUs.

A real offline controller test also completed DA2 -> DA3 -> DA2 on the same
photo. It created two distinct depth caches and model-tagged outputs; the
third call reused the first DA2 cache without depth inference.

Photo source: https://github.com/DepthAnything/Depth-Anything-V2/blob/main/assets/examples/demo01.jpg

## Further target-hardware validation

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

The online URLs target the matching `v1.0` release; downloads become available
only once all verified assets have been uploaded and the release is published.

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
The one-time 1.0 release workflow publishes only after matching source checks,
Windows GUI checks, frozen CPU conversion and archive verification pass.
A published v1.0 cannot be replaced by subsequent builds.

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

Built-in Quick/Standard/Fine presets use resolutions 0/1218/2048 and edge fix
2/1. Their selection is stored by a language-independent builtin_preset key;
own preset values and names remain in depth_presets and are not overwritten.
Model-standard labels track model changes without replacing the stored zero.
The editable resolution field remains available for custom presets.

## Complete inference presets

The header preset list owns model, device, resolution and edge fix. Standard,
CPU, Quick, Fine and Depth Pro have edge fix 2/1. Standard/Quick/Fine/Depth Pro
select Automatic; CPU selects DA2 Small explicitly on CPU. Model/device/resolution
are visible alongside the list. Creating/editing a custom profile opens the
modeless editor; built-ins are unchanged. Custom profiles remain in settings.json.
Legacy profiles inherit their former model/device; separate legacy selections
are retained as a custom profile when they differ from a new built-in.
Original-size and PNG options share one row under Options. At insufficient
window height, the main cards can be scrolled without hiding controls.
Automated Windows GUI checks exercise DE/EN, 100%/150% scaling, complete preset
switching, custom names/resolutions, settings persistence and busy states.

