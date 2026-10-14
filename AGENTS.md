# DepthTricia

Read DESIGN_STANDARD_STEREOTOOLS.txt before changing the inherited GUI.
The user's DepthTricia decisions override SplatTricia-specific SHARP rules:
15 permille default, DA2 Small / DA3 Mono Large / Depth Pro, edge fix 2/1,
1218 default for Depth Anything, mlbw_l2_inpaint + light_inpaint_v1.
No runtime network access except an explicitly confirmed model or runtime download.
Never silently lower depth resolution, disable inpainting, or change device.
Use established upstream inference only; no custom depth tiling, patch batching,
quantization, or undocumented numerical approximations.
Preserve the original ready.wav bytes. The new icon is supplied by Christoph.
Preserve inherited output paths, stereo-window controls and anaglyph math.
Distinguish implemented code from tested inference and a verified release.
Ship one common CUDA-enabled package with Automatic selecting CUDA when
available, otherwise CPU. No separate public CPU/GPU editions are planned.
Keep DA2 and DA3 bundled; Depth Pro remains an explicitly confirmed download.
Split large runtime libraries into verified standard ZIP assets below 2 GiB.
Install missing assets only after confirmation, with local ZIPs preferred.
Use one common application; do not mix CPU-build and CUDA-build libraries.
