# Build and development

Windows 10/11 x64, Python 3.12. No native CUDA extension or CUDA toolkit is
needed; PyTorch supplies the runtime. The portable app needs no Python install.

Create a virtual environment and install the matching PyTorch build:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu126
.venv\Scripts\python -m pip install -r requirements.txt pyinstaller==6.16.0
.venv\Scripts\python scripts/prepare_runtime.py
.venv\Scripts\python scripts/prepare_tools.py
.venv\Scripts\python run_depthtricia.py
```

For a CPU-only development/build environment use the same torch/torchvision
versions with `--index-url https://download.pytorch.org/whl/cpu` instead.
The CUDA-enabled Windows package is intended to support CPU execution too;
that target-system behavior requires Windows validation.

Model downloads are opt-in in the application. For developer/build use:

```powershell
.venv\Scripts\python scripts/download_models.py da2 da3 --confirm
```

Depth Pro is optional: select it in the GUI and explicitly confirm its download,
or use `scripts/download_models.py depthpro --confirm` while developing.
All files are checked against recorded SHA-256 hashes before use.

Build the portable package:

```powershell
.venv\Scripts\python -m PyInstaller --noconfirm --clean DepthTricia.spec
.venv\Scripts\python scripts/package_release.py
```

`scripts/prepare_tools.py` downloads the official ExifTool 13.59 x64 distribution
at build time, verifies its SHA-256 and preserves its accompanying files and
licenses. This build step is not a runtime download.
The image pipeline does not require PyAV/FFmpeg.
The sound and icon are copied without conversion.

The main ZIP attempts to include DA2 Small, DA3 Mono Large and the shared
inpainting models. If it exceeds GitHub's individual-file limit, DA3 is omitted
and can be downloaded through the explicit confirmation flow. Depth Pro stays
optional. The finished archive is measured rather than estimated.

The source snapshot contains the exact tracked application/build files and
the installed requirements lock. Pinned upstream inference source is included
separately in `third_party`, with full license texts in `licenses`.
