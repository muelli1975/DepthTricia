# Development status

This is the initial implementation, not a validated Windows release.

Implemented: the inherited SplatTricia interface and stereo controls; local
DA2 Small, DA3 Mono Large and Depth Pro loading; resolution/edge presets;
mlbw_l2_inpaint with light_inpaint_v1; SBS/anaglyph JPEG output; depth caching;
explicitly confirmed, checksum-verified model downloads; portable Windows build.
The supplied icon and original ready.wav are preserved byte for byte.

## Verified locally

- Seven regression tests cover depth normalization, width-based deviation,
  window backshift, cache invalidation, download consent, checksum failure and
  cancellation.
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

- Validate the frozen Windows executable, Windows 10/11 and NVIDIA/CUDA.
- Test CPU execution from the CUDA-enabled portable package.
- Run DA3 at 2048 and Depth Pro on suitable target hardware. Full-precision
  Depth Pro CPU inference exceeded this test environment's 8 GiB RAM limit;
  it remains unverified here. Its native inference path is preserved.
- Compare foreground boundaries, thin objects, sky and disocclusion filling
  against iw3 on representative photos, including portrait orientations.
- Verify metadata, download cancellation and restart, and final ZIP contents.
- Confirm the measured archive size and whether DA3 fits alongside the runtime.

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

Pushes to main run source checks and create a Windows development artifact.
The workflow does not publish a stable release automatically.
