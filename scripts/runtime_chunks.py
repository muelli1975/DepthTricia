"""Group intact runtime files into standard ZIP assets below GitHub's limit."""
from pathlib import Path
import hashlib
import json
import zipfile


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def split_runtime(application: Path, tag='v1.0', group_bytes=1024**3, *, include_depthpro=False):
    directory = application / '_internal/torch/lib'
    paths = sorted(path for path in directory.iterdir() if path.is_file())
    if not paths:
        raise RuntimeError('PyTorch runtime files are missing')
    groups, current, size = [], [], 0
    for path in paths:
        if current and size + path.stat().st_size > group_bytes:
            groups.append(current)
            current, size = [], 0
        current.append(path)
        size += path.stat().st_size
    if current:
        groups.append(current)
    packages = [(f'DepthTricia_Runtime_1.0_{index:02d}.zip', group)
                for index, group in enumerate(groups, 1)]
    if include_depthpro:
        checkpoint = application / 'models/depth_pro.pt'
        if not checkpoint.is_file():
            raise RuntimeError('Depth Pro checkpoint is missing')
        packages.append(('DepthTricia_Models_DepthPro_1.0.zip', [checkpoint]))
    files, archives = [], []
    for filename, group in packages:
        target = application.parent / filename
        members = []
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
            notices = (application / 'LICENSES.txt').read_text(encoding='utf-8')
            for path in sorted((application / 'licenses').glob('*')):
                if path.is_file():
                    notices += '\n\n[' + path.name + ']\n' + path.read_text(encoding='utf-8')
            package.writestr('LICENSES.txt', notices)
            for path in group:
                name = path.relative_to(application).as_posix()
                members.append(name)
                files.append(dict(path=name, size=path.stat().st_size, sha256=digest(path)))
                package.write(path, name)
        if target.stat().st_size >= 2**31:
            raise RuntimeError(f'{target.name} exceeds 2 GiB; reduce group size or split the offending native file.')
        archives.append(dict(filename=target.name, size=target.stat().st_size, sha256=digest(target),
            paths=members, url=f'https://github.com/muelli1975/DepthTricia/releases/download/{tag}/{target.name}'))
        print(f'{target.name}: {target.stat().st_size / 1e6:.1f} MB', flush=True)
    data = dict(version=1, files=files, archives=archives)
    (application / 'runtime_manifest.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    for _, group in packages:
        for path in group:
            path.unlink()
    (application / 'runtime_verified.json').unlink(missing_ok=True)
    return data
