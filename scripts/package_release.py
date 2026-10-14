"""Assemble portable files; measure the ZIP before deciding model bundling."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from depthtricia.model_catalog import FILES
from depthtricia.downloads import verify_model


def zip_folder(folder, target):
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                archive.write(path, folder.name + '/' + path.relative_to(folder).as_posix())


def package(include_da3=True):
    application = ROOT / 'dist/DepthTricia'
    if not (application / 'DepthTricia.exe').is_file():
        raise RuntimeError('Windows executable is missing.')
    for folder in ['assets', 'licenses', 'third_party']:
        shutil.copytree(ROOT / folder, application / folder, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
    for name in ['README.md', 'README_DE.md', 'LICENSE.txt', 'THIRD_PARTY.md']:
        shutil.copyfile(ROOT / name, application / name)
    if not (ROOT / 'tools/exiftool.exe').is_file():
        raise RuntimeError('ExifTool is missing. Run scripts/prepare_tools.py.')
    shutil.copytree(ROOT / 'tools', application / 'tools', dirs_exist_ok=True)
    source = application / 'source'
    source.mkdir(exist_ok=True)
    tracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    for name in filter(None, tracked):
        original = ROOT / name
        if original.is_file():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
    lock = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '--format=freeze'], text=True)
    (source / 'requirements-lock.txt').write_text(lock, encoding='utf-8')
    from collect_licenses import collect
    collect(application / 'LICENSES.txt')
    models = application / 'models'
    models.mkdir(exist_ok=True)
    for key in ['da2', 'warp', 'inpaint'] + (['da3'] if include_da3 else []):
        spec = FILES[key]
        verify_model(ROOT / 'models', spec)
        shutil.copyfile(ROOT / 'models' / spec.filename, models / spec.filename)
    target = ROOT / 'dist/DepthTricia_1.0.zip'
    zip_folder(application, target)
    if target.stat().st_size >= 2**31 and include_da3:
        (models / FILES['da3'].filename).unlink()
        zip_folder(application, target)
        print('DA3 did not fit in the main ZIP; the confirmed model downloader remains available.')
    if target.stat().st_size >= 2**31:
        raise RuntimeError('Application ZIP exceeds GitHub\'s 2 GiB asset limit.')
    print(f'{target.name}: {target.stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--without-da3', action='store_true')
    package(not parser.parse_args().without_da3)
