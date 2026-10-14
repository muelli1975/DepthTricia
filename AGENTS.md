# DepthTricia

Read DESIGN_STANDARD_STEREOTOOLS.txt before changing the inherited GUI.
The user's DepthTricia decisions override SplatTricia-specific SHARP rules:
15 permille default, DA2 Small / DA3 Mono Large / Depth Pro, edge fix 2/1,
1218 default for Depth Anything, mlbw_l2_inpaint + light_inpaint_v1.
No runtime network access except an explicitly confirmed model download.
Never silently lower depth resolution, disable inpainting, or change device.
Use established upstream inference only; no custom depth tiling, patch batching,
quantization, or undocumented numerical approximations.
Preserve the original ready.wav bytes. The new icon is supplied by Christoph.
Preserve inherited output paths, stereo-window controls and anaglyph math.
Distinguish implemented code from tested inference and a verified release.
