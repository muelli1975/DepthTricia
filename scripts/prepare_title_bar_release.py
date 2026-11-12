"""Verify the released portable runtime and replace only the application code."""
import argparse
from copy import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / '.github/title-bar-update.json'
SOURCE_ARCHIVE = 'DepthTricia_1.0.zip'
SOURCE_PREFIX = 'DepthTricia/'
PORTABLE = ROOT / 'portable/DepthTricia'
DOWNLOADS = ROOT / 'released-inputs'
CANDIDATE = ROOT / 'title-bar-release'
SOURCE_FILES = (
    'src/depthtricia/gui.py', 'src/depthtricia/titlebar.py', 'DESIGN_STANDARD_STEREOTOOLS.txt',
    'TitleBarRelease.spec', 'scripts/prepare_title_bar_release.py',
    'scripts/publish_title_bar_update.py', '.github/title-bar-update.json',
    '.github/workflows/title-bar-release.yml', '.github/workflows/windows-build.yml',
)


def digest(path):
    with path.open('rb') as source:
        return 'sha256:' + hashlib.file_digest(source, 'sha256').hexdigest()


def download(plan, name):
    DOWNLOADS.mkdir(exist_ok=True)
    subprocess.run(['gh', 'release', 'download', plan['tag'], '--repo', plan['repository'],
                    '--pattern', name, '--dir', str(DOWNLOADS)], check=True)
    path = DOWNLOADS / name
    assert digest(path) == plan['assets'][name], name
    return path


def path_parts(name):
    path = PurePosixPath(name)
    assert not path.is_absolute() and '..' not in path.parts and ':' not in name and '\\' not in name, name
    return path.parts


def extract(archive, directory, allowed=None):
    with zipfile.ZipFile(archive) as package:
        names = {info.filename for info in package.infolist() if not info.is_dir()}
        if allowed is not None:
            assert names - {'LICENSES.txt'} == set(allowed), archive.name
        else:
            assert all(name.startswith(SOURCE_PREFIX) for name in names)
        for info in package.infolist():
            if info.is_dir() or (allowed is not None and info.filename == 'LICENSES.txt'):
                continue
            dest = directory.joinpath(*path_parts(info.filename))
            dest.parent.mkdir(parents=True, exist_ok=True)
            with package.open(info) as source, dest.open('xb') as output:
                shutil.copyfileobj(source, output, 4 * 1024 * 1024)


def prepare(plan):
    extract(download(plan, SOURCE_ARCHIVE), PORTABLE.parent)
    manifest = json.loads((PORTABLE / 'runtime_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['archives']:
        name = item['filename']
        path = download(plan, name)
        assert path.stat().st_size == item['size'] and digest(path) == 'sha256:' + item['sha256'], name
        extract(path, PORTABLE, item['paths'])
        path.unlink()
    for item in manifest['files']:
        path = PORTABLE.joinpath(*path_parts(item['path']))
        assert path.stat().st_size == item['size'] and digest(path) == 'sha256:' + item['sha256'], item['path']


def package():
    from PyInstaller.archive.readers import CArchiveReader

    executable = PORTABLE / 'DepthTricia.exe'
    modules = CArchiveReader(str(executable)).open_embedded_archive('PYZ.pyz')
    assert 'depthtricia.titlebar' in modules.toc
    info = json.loads((PORTABLE / 'BUILD_INFO.json').read_text(encoding='utf-8'))
    info['source_commit'] = os.environ['GITHUB_SHA']
    metadata = PORTABLE / 'BUILD_INFO.json'
    metadata.write_text(json.dumps(info, indent=2), encoding='utf-8')
    replacements = {
        SOURCE_PREFIX + 'DepthTricia.exe': executable,
        SOURCE_PREFIX + 'BUILD_INFO.json': metadata,
        **{SOURCE_PREFIX + 'source/' + name: ROOT / name for name in SOURCE_FILES},
    }
    CANDIDATE.mkdir(exist_ok=True)
    target = CANDIDATE / SOURCE_ARCHIVE
    with zipfile.ZipFile(DOWNLOADS / SOURCE_ARCHIVE) as original:
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as result:
            for entry in original.infolist():
                if entry.filename in replacements:
                    result.write(replacements.pop(entry.filename), entry.filename)
                else:
                    with original.open(entry) as source, result.open(copy(entry), 'w') as output:
                        shutil.copyfileobj(source, output, 4 * 1024 * 1024)
            for name, path in replacements.items():
                result.write(path, name)
        with zipfile.ZipFile(target) as result:
            assert result.testzip() is None
            name = SOURCE_PREFIX + 'runtime_manifest.json'
            assert original.read(name) == result.read(name)
            assert result.read(SOURCE_PREFIX + 'source/src/depthtricia/titlebar.py') == (ROOT / 'src/depthtricia/titlebar.py').read_bytes()
    assert target.stat().st_size < 2**31


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'package'))
    if parser.parse_args().stage == 'prepare':
        prepare(json.loads(PLAN.read_text(encoding='utf-8')))
    else:
        package()
