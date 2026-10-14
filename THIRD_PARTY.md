# Third-party components

DepthTricia's original code and documentation are MIT licensed.
Reusing a third-party component does not relicense that component.

| Component / model | License | Source |
| --- | --- | --- |
| nunif / iw3 original code, MaskMLBW and LightInpaint weights | MIT | https://github.com/nagadomi/nunif |
| Depth Anything V2 Small weights | Apache 2.0 | https://huggingface.co/depth-anything/Depth-Anything-V2-Small |
| DA3 Mono Large weights | Apache 2.0 | https://huggingface.co/depth-anything/DA3MONO-LARGE |
| Depth Pro code and weights | Apple Sample Code License | https://github.com/apple-aiml-research/ml-depth-pro |
| Depth Anything iw3 adapters / DINOv2 | Respective Apache-2.0 notices | https://github.com/nagadomi/Depth-Anything_iw3 |
| Depth Anything 3 iw3 adapter | Apache 2.0 and upstream notices | https://github.com/nagadomi/Depth-Anything-3_iw3 |

Nagadomi confirmed the license of his original model weights:
https://github.com/nagadomi/nunif/issues/718#issuecomment-5149794923
and use in another GUI:
https://github.com/nagadomi/nunif/discussions/720

Pinned upstream source revisions are recorded in `dependencies.json`.
`scripts/prepare_runtime.py` prepares inference-only package initializers and
redirects iw3's local hub/configuration folder to DepthTricia's `models`.
Stereo model mathematics and learned weights are not modified.
DepthTricia loads all checkpoints by explicit local paths and never invokes
the upstream online model loaders.

The complete copied license texts, NOTICE and Apple ACKNOWLEDGEMENTS are
included under `licenses`. Runtime packages also retain their license texts.
PyAV and FFmpeg are not required for this still-image application.
ExifTool 13.59 x64 is bundled unchanged apart from renaming its launcher to
`exiftool.exe` as documented by its author. Its accompanying files and license
texts remain under `tools/exiftool_files` (including Strawberry Perl notices).
Source and installation documentation: https://exiftool.org/ .
The build-time archive URL and SHA-256 are pinned in `scripts/prepare_tools.py`.
