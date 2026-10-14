# DepthTricia

[Deutsch](README_DE.md)

DepthTricia converts individual 2D photographs or image folders to stereo 3D
using depth maps. It inherits SplatTricia's interface, stereo-window controls,
floating-window curtains, SBS/anaglyph outputs and metadata handling.

**Development build — not yet a verified Windows release.**

Models: Depth Anything V2 Small, Depth Anything 3 Mono Large and
Depth Pro. Stereo generation uses iw3's `mlbw_l2_inpaint` with
`light_inpaint_v1`. Processing supports CPU and NVIDIA/CUDA.

Defaults: 15‰ deviation, 100% stereo-window position, horizontal/vertical
edge fix 2/1, and 1218 depth resolution for Depth Anything. Depth Pro uses its
native model resolution. Presets Quick, Standard and Fine use model-standard,
1218 and 2048 respectively, with edge fix 2/1. Custom values from 196 to 4096
and custom edge settings can be saved under a separate preset name.
Depth Anything internally rounds resolutions up to its 14-pixel grid (2048
becomes 2058); Depth Pro's resolution remains fixed for all presets.
The model-standard option displays its value: 518 for DA2, 504 for DA3;
Depth Pro uses a fixed internal 1536×1536 resolution.

Output is limited to 2160 pixels high by default, without upscaling smaller
photos. **Original size output** keeps the full oriented source dimensions.
**Save depth map** optionally exports the used relative depth map as a 16-bit
grayscale PNG in `depth_maps`: near is white, far is black. It retains the
computed map dimensions and is not a metric depth-in-metres export.
Both checkboxes start off and their choices are saved. Named depth presets and
these options are stored locally in `settings.json` in the application folder;
keep that file when updating. With settings in filenames enabled, outputs
include the model tag, e.g. `scene_DA3MonoLarge_d15_w100_o0_sbs.jpg`.

Models are stored visibly in `models`. Missing models can be downloaded only
after explicit confirmation. Existing models are loaded locally without
network checks, accounts, tokens or a Hugging Face cache dependency.

One common Windows package selects CUDA when available, otherwise CPU.
Large runtime files are supplied as additional ZIP assets. At first processing,
DepthTricia asks before installing or downloading missing runtime packages.
Local ZIPs beside the application are used first; afterwards it works offline.
DA2 and DA3 are in the main ZIP. The original Apple Depth Pro checkpoint is
included in `DepthTricia_Models_DepthPro_1.0.zip` and installed with the runtime
packages after confirmation. Download all six ZIPs from the same release into
one folder, extract only `DepthTricia_1.0.zip`, and leave the other ZIPs beside
the extracted application folder for offline installation.

Output folders: `sbs`, `anaglyph`, `_temp` (reusable depth maps).
The `.npy` files in `_temp` preserve normalized 32-bit floating-point depth
values for computation; the optional PNG is a separate graphic export.
Changing stereo settings reuses depth maps; changing the source, depth model,
depth resolution or edge fix invalidates the corresponding cache.

See [BUILD.md](BUILD.md) to run from source and build the portable Windows app.
See [DEVELOPMENT.md](DEVELOPMENT.md) for validation status and remaining work.

Original DepthTricia code is MIT licensed. Third-party code and model weights
retain their respective licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).
