DepthTricia converts 2D photos to stereo 3D using DA2 Small, DA3 Mono Large
or Depth Pro. One common Windows package uses CUDA when available,
otherwise CPU. Stereo generation uses mlbw_l2_inpaint with light_inpaint_v1.
Output can use original photo dimensions or the default 2160-pixel height
limit. Optional 16-bit grayscale depth PNGs are saved in depth_maps. Settings
filenames include the selected model. Model-standard preset resolutions are
shown numerically; named presets and the two output choices remain local in
settings.json, which should be retained when updating.
Quick, Standard and Fine presets select model-standard, 1218 and 2040 depth
resolution with edge fix 2/1. Custom resolutions can be entered and saved.
Depth Pro keeps its fixed native resolution.

This is a development draft. The frozen Windows executable passed CPU
conversion, runtime installation, GUI/preset startup, metadata copying and
cache reuse. CUDA inference, full Depth Pro inference and representative
photo quality still require target-system validation.

For offline testing, download all six ZIP files into one folder. Extract
DepthTricia_1.0.zip and leave the runtime and model ZIPs beside the resulting DepthTricia
folder. Start DepthTricia.exe; choose a photo and confirm runtime installation.
Matching local packages are used without downloading. DA2 and DA3 are in the
main ZIP. The original Apple CDN Depth Pro checkpoint is included in
DepthTricia_Models_DepthPro_1.0.zip and installed with the runtime packages after
confirmation. Its complete license texts and provenance are included.

Once this release is published on tag v1.0, the main application can download
missing runtime ZIPs after confirmation. All assets must come from this exact
build; archive and extracted-file hashes are verified. No CUDA toolkit or
Python installation is needed by the user.
