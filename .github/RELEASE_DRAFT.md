# DepthTricia 1.0

Convert 2D photographs into stereo 3D with local depth estimation and inpainting.

- Choose Depth Anything V2 Small, Depth Anything 3 Mono Large or Depth Pro.
- Export SBS and anaglyph JPEGs, with optional 16-bit depth-map PNGs.
- Adjust deviation, stereo-window position and scene setback; reuse cached depth maps.
- Use built-in or custom presets with CPU or NVIDIA processing.
- Correct Depth Pro preprocessing and transparent-image handling.
- German and English interface.

## Installation

64-bit Windows is required. CPU processing is supported; a compatible NVIDIA graphics card enables CUDA acceleration. No separate Python installation or CUDA toolkit is required.

Download and extract `DepthTricia_1.0.zip`, then start `DepthTricia.exe`. On first processing, confirm installation of the matching runtime packages. DA2 and DA3 are included in the main ZIP; Depth Pro is supplied in its separate model ZIP.

For offline setup, download **all seven ZIP files** into one folder. **Extract only the main ZIP** and leave the remaining ZIPs beside the extracted `DepthTricia` folder. Local packages are used first.

When updating, replace the application and obtain all matching runtime ZIPs from this release. Keep `settings.json`. For CPU processing, choose the CPU preset; the Fine preset remains experimental. High-resolution processing needs more memory and time.
