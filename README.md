# DepthTricia

[Deutsch](README_DE.md)

DepthTricia converts individual 2D photographs or image folders to stereo 3D
using depth maps. It inherits SplatTricia's interface, stereo-window controls,
floating-window curtains, SBS/anaglyph outputs and metadata handling.

**Development build — not yet a verified Windows release.**

Models: Depth Anything V2 Small, Depth Anything 3 Mono Large and optional
Depth Pro. Stereo generation uses iw3's `mlbw_l2_inpaint` with
`light_inpaint_v1`. Processing supports CPU and NVIDIA/CUDA.

Defaults: 15‰ deviation, 100% stereo-window position, horizontal/vertical
edge fix 2/1, and 1218 depth resolution for Depth Anything. Depth Pro uses its
native model resolution. Presets allow model-standard, 1218, 2048 or custom
depth resolution and custom edge settings.

Models are stored visibly in `models`. Missing models can be downloaded only
after explicit confirmation. Existing models are loaded locally without
network checks, accounts, tokens or a Hugging Face cache dependency.

One common Windows package selects CUDA when available, otherwise CPU.
Large runtime files are supplied as additional ZIP assets. At first processing,
DepthTricia asks before installing or downloading missing runtime packages.
Local ZIPs beside the application are used first; afterwards it works offline.

Output folders: `sbs`, `anaglyph`, `_temp` (reusable depth maps).
Changing stereo settings reuses depth maps; changing the source, depth model,
depth resolution or edge fix invalidates the corresponding cache.

See [BUILD.md](BUILD.md) to run from source and build the portable Windows app.
See [DEVELOPMENT.md](DEVELOPMENT.md) for validation status and remaining work.

Original DepthTricia code is MIT licensed. Third-party code and model weights
retain their respective licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).
