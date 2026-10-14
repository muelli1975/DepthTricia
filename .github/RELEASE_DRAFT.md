DepthTricia turns 2D photos into stereo 3D with local depth models and learned
inpainting. This first release includes DA2 Small, DA3 Mono Large and Depth Pro
support, SBS/anaglyph JPEG output, metadata copying and reusable depth maps.

- One portable Windows package for NVIDIA and CPU. Automatic uses CUDA when
  available, otherwise CPU; no separate CUDA toolkit or Python is needed.
- Complete presets: Standard (DA3, 1218), CPU (DA2, 518), Quick (DA3, 504),
  Fine (DA3, 2048) and Depth Pro (native). All use edge fix 2/1. Custom presets
  save model, device, resolution and edge fix; model/settings remain visible.
- Defaults: 15% deviation and 100% stereo-window position. Stereo generation
  uses `mlbw_l2_inpaint` with `light_inpaint_v1`.
- Additional setback moves the whole scene behind the stereo window. Newly
  exposed borders are filled with the same inpainting as internal holes.
- Original-size output or the default maximum height of 2160 pixels. Optional
  16-bit relative depth PNGs retain the computed map dimensions. Settings
  filenames can include the selected model. Keep `settings.json` when updating.
- Local processing without accounts, tokens or network checks. Missing runtime
  packages/models are installed or downloaded only after confirmation.

Download `DepthTricia_1.0.zip`, extract it and start `DepthTricia.exe`. On first
processing, confirm the installation of matching runtime packages. DA2 and DA3
are in the main ZIP; the original Apple Depth Pro checkpoint is supplied in
`DepthTricia_Models_DepthPro_1.0.zip` and installed with the runtime packages.
For offline setup, download all six ZIP files into one folder, extract only
the main ZIP and leave the remaining ZIPs beside the extracted DepthTricia folder.
All archives are below 2 GiB; archives and installed files are checksum-verified.

CPU users should select the CPU preset. DA3 at high resolution, Depth Pro and
original-size inpainting need more memory and processing time. Quality or
hardware settings are never reduced automatically.

The Windows executable is checked for GUI/preset handling, offline DA2 CPU
conversion, inpainting, metadata, depth PNG export and cache reuse. The build
also checks DA3 configuration and the installed Depth Pro checkpoint. These
checks do not constitute full Depth Pro or CUDA inference validation on all
hardware. Source snapshots and complete third-party license notices are included;
original DepthTricia code is MIT licensed, models retain their own licenses.

