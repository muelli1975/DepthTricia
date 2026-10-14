# DepthTricia

[Deutsch](README_DE.md)

DepthTricia converts individual 2D photographs or image folders to stereo 3D
using depth maps. It inherits SplatTricia's interface, stereo-window controls,
floating-window curtains, SBS/anaglyph outputs and metadata handling.

[Download DepthTricia 1.0](https://github.com/muelli1975/DepthTricia/releases/tag/v1.0)

Models: Depth Anything V2 Small, Depth Anything 3 Mono Large and
Depth Pro. Stereo generation uses iw3's `mlbw_l2_inpaint` with
`light_inpaint_v1`. Processing supports CPU and NVIDIA/CUDA.

Defaults: 15‰ deviation, 100% stereo-window position, horizontal/vertical
edge fix 2/1, and 1218 depth resolution for Depth Anything. Depth Pro uses its
native model resolution. Complete presets select model, device, resolution and
edge fix together: Standard uses DA3 / 1218 / Automatic, CPU uses DA2 / 518 / CPU,
Quick uses DA3 / 504 / Automatic, Fine uses DA3 / 2048 / Automatic, and Depth Pro
uses its native resolution / Automatic. All use edge fix 2/1. The selected
model and settings remain visible beside the preset list. Custom presets can
include resolutions from 196 to 4096 and custom edge settings.
Depth Anything internally rounds resolutions up to its 14-pixel grid (2048
becomes 2058); Depth Pro's resolution remains fixed for all presets.
The model-standard option displays its value: 518 for DA2, 504 for DA3;
Depth Pro uses a fixed internal 1536×1536 resolution.

Output is limited to 2160 pixels high by default, without upscaling smaller
photos. **Original size** keeps the full oriented source dimensions.
**Depth map (PNG)** optionally exports the used relative depth map as a 16-bit
grayscale PNG in `depth_maps`: near is white, far is black. It retains the
computed map dimensions and is not a metric depth-in-metres export.
Both checkboxes are under Options, start off and their choices are saved. Named depth presets and
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

CPU users should choose the CPU preset. DA3 at 1218/2048 and Depth Pro require
more time and memory; original-size output also increases inpainting memory.
No quality setting or device is reduced automatically after a memory error.
