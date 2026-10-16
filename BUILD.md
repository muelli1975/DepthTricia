# Build and development

Windows 10/11 x64, Python 3.12. No native CUDA extension or CUDA toolkit is
needed; PyTorch supplies the runtime. The portable app needs no Python install.

Create a virtual environment and install the matching PyTorch build:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
.venv\Scripts\python -m pip install -r requirements.txt pyinstaller==6.16.0
.venv\Scripts\python scripts/prepare_runtime.py
.venv\Scripts\python scripts/prepare_tools.py
.venv\Scripts\python run_depthtricia.py
```

For a CPU-only development/build environment use the same torch/torchvision
versions with `--index-url https://download.pytorch.org/whl/cpu` instead.
The CUDA-enabled Windows package is intended to support CPU execution too;
the frozen executable is checked on CPU by the Windows build workflow.
Automatic selects an available CUDA GPU, otherwise CPU. The intended public
download is one common package, with no separate CPU/GPU editions.

Model downloads are opt-in in the application. For developer/build use:

```powershell
.venv\Scripts\python scripts/download_models.py da2 da3 depthpro --confirm
```

The complete release includes Depth Pro in its own model ZIP. Its checkpoint
is obtained from the direct Apple CDN URL in the original upstream download
script, with the license basis recorded in `licenses/DepthPro-SOURCE.md`.
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

The common package uses one matching CUDA-enabled PyTorch build for both
GPU and CPU execution. Large files from `_internal/torch/lib` are grouped
unchanged into standard `DepthTricia_Runtime_1.0_XX.zip` archives. Each archive
and the main `DepthTricia_1.0.zip` must be below 2 GiB. `BUILD_INFO.json` records
the runtime and source revision; `runtime_manifest.json` pins archive and
individual-file SHA-256 hashes. CPU-build libraries are never mixed into the
CUDA build.

The main ZIP attempts to include DA2 Small, DA3 Mono Large and shared
inpainting models. If necessary DA3 is omitted and remains available through
the confirmed model download. Depth Pro is packaged separately as
`DepthTricia_Models_DepthPro_1.0.zip`, with complete license texts and provenance.
It is installed by the same confirmed, checksum-verified package installer.

At Start, missing runtime files trigger a confirmation before installation.
Matching ZIPs in `runtime_packages`, the application folder or its parent are
used first. Otherwise the confirmed installer downloads the release assets.
After installation processing is offline. Files are staged and checked before
replacement; interrupted installations can be retried.

The build prepares URLs for tag `v1.0`. The release workflow publishes only
the matching main ZIP and runtime archives after source checks and the frozen
Windows test pass. Maintenance corrections retain version 1.0 and replace the
matching verified assets together. Development testing uses the local runtime
ZIPs from the build artifact; put them beside the extracted DepthTricia folder.

The workflow assembles the folder, then runs `DepthTricia.exe --smoke-test
REPORT.json` before compressing it. This checks GUI startup, preset editing,
DA3 configuration, Depth Pro imports and checkpoint installation/hash,
real DA2 CPU conversion, inpainting,
output dimensions, ExifTool metadata copying and depth-cache reuse, with
Python network connections blocked. It does not validate CUDA inference or
full Depth Pro inference.

The source snapshot contains the exact tracked application/build files and
the installed requirements lock. Pinned upstream inference source is included
separately in `third_party`, with full license texts in `licenses`.
