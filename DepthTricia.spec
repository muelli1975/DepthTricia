from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve()
data = collect_data_files('customtkinter')
data += [(str(ROOT / 'src/depthtricia/locales'), 'depthtricia/locales')]
data += [(str(ROOT / 'third_party/da3/src/depth_anything_3/configs'), 'depth_anything_3/configs')]
data += [(str(ROOT / 'third_party/da2/torchhub'), 'torchhub')]
hidden = ['torch', 'torchvision', 'PIL._tkinter_finder', 'depthtricia.gui',
          'depthtricia.preset_dialog', 'depthtricia.controller', 'depthtricia.depth_backend',
          'depthtricia.stereo_backend', 'pillow_heif', 'cv2', 'safetensors.torch',
          'omegaconf', 'einops', 'yaml', 'platformdirs', 'addict']
hidden += collect_submodules('timm')
# DA3 selects these inference modules through configuration/importlib.
hidden += ['depth_anything_3.model.da3', 'depth_anything_3.model.dinov2.dinov2',
           'depth_anything_3.model.dpt']
analysis = Analysis([str(ROOT / 'launcher.py')],
    pathex=[str(ROOT / 'src'), str(ROOT / 'third_party/nunif'),
            str(ROOT / 'third_party/da2'), str(ROOT / 'third_party/da3/src'),
            str(ROOT / 'third_party/depthpro/src')],
    binaries=[], datas=data, hiddenimports=hidden, hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=['av', 'matplotlib', 'tensorboard', 'ninja'], noarchive=False)
pyz = PYZ(analysis.pure)
icon = ROOT / 'assets/depthtricia.ico'
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='DepthTricia',
          debug=False, strip=False, upx=False, console=False,
          icon=str(icon) if icon.is_file() else None)
coll = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False,
               name='DepthTricia')
