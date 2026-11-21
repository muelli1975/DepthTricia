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
Keep DA2 and DA3 bundled in the main ZIP. Ship the original Apple CDN Depth Pro
checkpoint in its own model ZIP, installed with the confirmed package setup.
Split large runtime libraries into verified standard ZIP assets below 2 GiB.
Install missing assets only after confirmation, with local ZIPs preferred.
Use one common application; do not mix CPU-build and CUDA-build libraries.

## Agreed decisions and application startup

Treat Christoph's explicit decisions as requirements for implementation, test builds and releases. Preserve their intent when choosing tools or languages. Before editing, check the relevant agreements. Before building, check the actual diff, entry point and build command against them. If a concrete technical obstacle requires a departure, explain the conflict and obtain Christoph's agreement before implementing it.

Use the existing Python entry point (`launcher.py`) and `DepthTricia.spec` for the Windows application. Introducing an additional application starter, wrapper or bootstrap process requires Christoph's prior agreement in any language.
