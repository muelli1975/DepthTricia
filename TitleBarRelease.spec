# Rebuild the application code with the exact released Windows dependencies.
from pathlib import Path
import importlib.util

from PyInstaller.archive.readers import CArchiveReader
from PyInstaller.config import CONF

root = Path(SPECPATH).resolve()
original = CArchiveReader(str(root / 'portable/DepthTricia/DepthTricia.exe'))
previous = original.open_embedded_archive('PYZ.pyz')
entries, code = [], {}
for name, item in previous.toc.items():
    if name == 'depthtricia' or name.startswith('depthtricia.'):
        continue
    kind = item[0]
    source = '-' if kind == 3 else ('__init__.py' if kind == 1 else 'module.py')
    entries.append((name, source, 'PYMODULE'))
    if kind != 3:
        code[name] = previous.extract(name)

for path in sorted((root / 'src/depthtricia').rglob('*.py')):
    relative = path.relative_to(root / 'src').with_suffix('')
    parts = relative.parts[:-1] if relative.name == '__init__' else relative.parts
    name = '.'.join(parts)
    entries.append((name, str(path), 'PYMODULE'))
    code[name] = compile(path.read_bytes(), relative.as_posix() + '.py', 'exec', optimize=0)

CONF.setdefault('code_cache', {})[id(entries)] = code
pyz = PYZ(entries)
hook_dir = root / 'build/title-bar-hooks'
hook_dir.mkdir(parents=True, exist_ok=True)
hooks = []
for name, item in original.toc.items():
    if item[-1] == 's' and name not in {'pyiboot01_bootstrap', 'launcher'}:
        path = hook_dir / (name + '.pyc')
        path.write_bytes(importlib.util.MAGIC_NUMBER + b'\0' * 12 + original.extract(name))
        hooks.append((name, str(path), 'PYSOURCE'))
exe = EXE(pyz, hooks, [('launcher', str(root / 'launcher.py'), 'PYSOURCE')], [],
          exclude_binaries=True, name='DepthTricia', console=False, debug=False,
          strip=False, upx=False, bootloader_ignore_signals=False,
          icon=str(root / 'assets/depthtricia.ico'), contents_directory='_internal')
coll = COLLECT(exe, [], name='DepthTricia', strip=False, upx=False)
