"""Install matching runtime files from verified ZIP assets, only after consent."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import tempfile
import zipfile

from .downloads import DownloadCancelled, download_models
from .model_catalog import FILES, ModelFile


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def destination(root, name):
    relative = PurePosixPath(name)
    if '\\' in name or relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe runtime path')
    is_library = relative.parts[:3] == ('_internal', 'torch', 'lib') and len(relative.parts) == 4
    is_depthpro = relative.parts == ('models', FILES['depthpro'].filename)
    if not (is_library or is_depthpro):
        raise ValueError('Unexpected runtime file location')
    result = root.joinpath(*relative.parts)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError('Runtime path escapes the application folder')
    return result


def manifest(root):
    path = root / 'runtime_manifest.json'
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    if data['version'] != 1 or not data['files'] or not data['archives']:
        raise ValueError('Invalid runtime manifest')
    files = set()
    for item in data['files']:
        destination(root, item['path'])
        if item['path'] in files or item['size'] <= 0 or len(item['sha256']) != 64:
            raise ValueError('Invalid runtime file record')
        if item['path'].startswith('models/'):
            spec = FILES['depthpro']
            if item['size'] != spec.size or item['sha256'] != spec.sha256:
                raise ValueError('Depth Pro package does not match the official checkpoint')
        files.add(item['path'])
    assigned = []
    for item in data['archives']:
        if Path(item['filename']).name != item['filename'] or not 0 < item['size'] < 2**31:
            raise ValueError('Invalid runtime archive')
        if not item['url'].startswith('https://github.com/muelli1975/DepthTricia/releases/download/'):
            raise ValueError('Unexpected runtime download source')
        assigned.extend(item['paths'])
    if len(assigned) != len(set(assigned)) or set(assigned) != files:
        raise ValueError('Runtime archives do not cover the expected files')
    return data


def signature(root, data):
    result = []
    for item in data['files']:
        stat = destination(root, item['path']).stat()
        if stat.st_size != item['size']:
            raise ValueError('Runtime file is incomplete')
        result.append([item['path'], stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns])
    return dict(manifest=digest(root / 'runtime_manifest.json'), files=result)


def missing_runtime(root):
    data = manifest(root)
    if data is None:
        return None
    try:
        if json.loads((root / 'runtime_verified.json').read_text()) == signature(root, data):
            return None
    except (OSError, ValueError, KeyError):
        pass
    return data


def install_runtime(root, *, confirmed, progress=None, cancelled=None):
    if not confirmed:
        raise PermissionError('Installation der Laufzeit wurde nicht bestätigt.')
    data = manifest(root)
    if data is None:
        return
    def check_cancelled():
        if cancelled and cancelled():
            raise DownloadCancelled('Installation abgebrochen.')
    check_cancelled()
    files = {item['path']: item for item in data['files']}
    for asset in data['archives']:
        check_cancelled()
        # Already installed archives, including a manually supplied checkpoint,
        # can be verified offline without reinstalling or downloading them.
        if all(destination(root, name).is_file()
               and destination(root, name).stat().st_size == files[name]['size']
               and digest(destination(root, name)) == files[name]['sha256'] for name in asset['paths']):
            continue
        archive = None
        for directory in (root / 'runtime_packages', root, root.parent):
            candidate = directory / asset['filename']
            if candidate.is_file() and candidate.stat().st_size == asset['size'] and digest(candidate) == asset['sha256']:
                archive = candidate
                break
        if archive is None:
            directory = root / 'runtime_packages'
            spec = ModelFile(asset['filename'], asset['url'], asset['size'], asset['sha256'], 'Bundled runtime licenses')
            download_models(directory, (spec,), confirmed=True, progress=progress, cancelled=cancelled)
            archive = directory / asset['filename']
        with tempfile.TemporaryDirectory(prefix='_runtime_stage_', dir=root) as staging:
            with zipfile.ZipFile(archive) as package:
                if set(package.namelist()) != set(asset['paths']) | {'LICENSES.txt'}:
                    raise ValueError('Runtime archive contents do not match the manifest')
                for name in asset['paths']:
                    check_cancelled()
                    item = files[name]
                    entry = package.getinfo(name)
                    if entry.file_size != item['size'] or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError('Unexpected runtime archive entry')
                    temporary = Path(staging) / PurePosixPath(name).name
                    value = hashlib.sha256()
                    received = 0
                    with package.open(entry) as source, temporary.open('wb') as output:
                        while block := source.read(4 * 1024 * 1024):
                            check_cancelled()
                            received += len(block)
                            if received > item['size']:
                                raise ValueError('Unexpected extracted runtime size')
                            value.update(block)
                            output.write(block)
                            if progress:
                                progress(PurePosixPath(name).name, received, item['size'])
                    if received != item['size'] or value.hexdigest() != item['sha256']:
                        raise ValueError('Runtime file checksum mismatch')
                check_cancelled()
                for name in asset['paths']:
                    target = destination(root, name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    (Path(staging) / PurePosixPath(name).name).replace(target)
    check_cancelled()
    (root / 'runtime_verified.json').write_text(json.dumps(signature(root, data)), encoding='utf-8')
