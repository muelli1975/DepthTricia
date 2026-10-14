import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from depthtricia import runtime_install
from depthtricia.downloads import DownloadCancelled
from depthtricia.model_catalog import FILES, ModelFile, missing_files


def runtime_builder():
    path = Path(__file__).resolve().parents[1] / 'scripts/runtime_chunks.py'
    spec = importlib.util.spec_from_file_location('runtime_chunks', path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


@pytest.fixture
def split_app(tmp_path):
    app = tmp_path / 'DepthTricia'
    libraries = app / '_internal/torch/lib'
    libraries.mkdir(parents=True)
    (libraries / 'a.dll').write_bytes(b'first library')
    (libraries / 'b.dll').write_bytes(b'second library')
    (app / 'LICENSES.txt').write_text('Test license')
    data = runtime_builder().split_runtime(app, group_bytes=16)
    return app, data


@pytest.fixture
def full_app(tmp_path, monkeypatch):
    app = tmp_path / 'DepthTricia'
    library = app / '_internal/torch/lib/a.dll'
    checkpoint = app / 'models/depth_pro.pt'
    library.parent.mkdir(parents=True)
    checkpoint.parent.mkdir()
    library.write_bytes(b'library')
    weights = b'official checkpoint fixture'
    checkpoint.write_bytes(weights)
    monkeypatch.setitem(FILES, 'depthpro', ModelFile('depth_pro.pt', FILES['depthpro'].url,
        len(weights), hashlib.sha256(weights).hexdigest(), 'Apple-ASCL'))
    (app / 'LICENSES.txt').write_text('Runtime licenses')
    (app / 'licenses').mkdir()
    (app / 'licenses/DepthPro-LICENSE.txt').write_text('Apple license fixture')
    data = runtime_builder().split_runtime(app, include_depthpro=True)
    return app, data, weights


def deny_download(*args, **kwargs):
    raise AssertionError('Unexpected download')


def test_runtime_requires_consent_and_restores_verified_local_parts(split_app, monkeypatch):
    app, data = split_app
    monkeypatch.setattr(runtime_install, 'download_models', deny_download)
    with pytest.raises(PermissionError):
        runtime_install.install_runtime(app, confirmed=False)
    assert not (app / '_internal/torch/lib/a.dll').exists()
    assert runtime_install.missing_runtime(app) is not None
    runtime_install.install_runtime(app, confirmed=True)
    assert (app / '_internal/torch/lib/a.dll').read_bytes() == b'first library'
    assert (app / '_internal/torch/lib/b.dll').read_bytes() == b'second library'
    assert runtime_install.missing_runtime(app) is None
    (app / '_internal/torch/lib/a.dll').write_bytes(b'wrong library')
    assert runtime_install.missing_runtime(app) is not None
    runtime_install.install_runtime(app, confirmed=True)
    assert (app / '_internal/torch/lib/a.dll').read_bytes() == b'first library'


def test_runtime_checks_file_hash_before_replacing_existing_library(split_app):
    app, data = split_app
    target = app / '_internal/torch/lib/a.dll'
    target.write_bytes(b'old library')
    data['files'][0]['sha256'] = hashlib.sha256(b'wrong expected file').hexdigest()
    (app / 'runtime_manifest.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='checksum'):
        runtime_install.install_runtime(app, confirmed=True)
    assert target.read_bytes() == b'old library'
    assert not list(app.glob('_runtime_stage_*'))


def test_cancelled_runtime_install_keeps_existing_library(split_app):
    app, data = split_app
    target = app / '_internal/torch/lib/a.dll'
    target.write_bytes(b'old library')
    cancel = False
    def progress(*args):
        nonlocal cancel
        cancel = True
    with pytest.raises(DownloadCancelled):
        runtime_install.install_runtime(app, confirmed=True, progress=progress, cancelled=lambda: cancel)
    assert target.read_bytes() == b'old library'
    assert not list(app.glob('_runtime_stage_*'))


def test_runtime_manifest_rejects_path_escape(split_app):
    app, data = split_app
    data['files'][0]['path'] = '../outside.dll'
    (app / 'runtime_manifest.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='path'):
        runtime_install.install_runtime(app, confirmed=True)
    assert not (app.parent / 'outside.dll').exists()


def test_depthpro_installs_from_local_package_with_license_and_no_second_download(full_app, monkeypatch):
    import zipfile
    app, data, weights = full_app
    monkeypatch.setattr(runtime_install, 'download_models', deny_download)
    assert not (app / 'models/depth_pro.pt').exists()
    assert FILES['depthpro'] in missing_files(app / 'models', 'depthpro')
    assert FILES['depthpro'] not in missing_files(app / 'models', 'depthpro', bundled_files=data['files'])
    archive = data['archives'][-1]
    assert archive['filename'] == 'DepthTricia_Models_DepthPro_1.0.zip'
    with zipfile.ZipFile(app.parent / archive['filename']) as package:
        assert b'Apple license fixture' in package.read('LICENSES.txt')
    with pytest.raises(PermissionError):
        runtime_install.install_runtime(app, confirmed=False)
    runtime_install.install_runtime(app, confirmed=True)
    assert (app / 'models/depth_pro.pt').read_bytes() == weights
    assert runtime_install.missing_runtime(app) is None


def test_installed_runtime_does_not_need_old_zips_when_depthpro_is_added(full_app, monkeypatch):
    app, data, weights = full_app
    library = app / '_internal/torch/lib/a.dll'
    library.write_bytes(b'library')
    original_stat = library.stat().st_mtime_ns
    (app.parent / data['archives'][0]['filename']).unlink()
    monkeypatch.setattr(runtime_install, 'download_models', deny_download)
    runtime_install.install_runtime(app, confirmed=True)
    assert library.stat().st_mtime_ns == original_stat
    assert (app / 'models/depth_pro.pt').read_bytes() == weights


@pytest.mark.parametrize('field,value', [('size', 1), ('sha256', '0' * 64)])
def test_model_manifest_must_match_official_checkpoint(full_app, field, value):
    app, data, weights = full_app
    data['files'][-1][field] = value
    (app / 'runtime_manifest.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='official checkpoint'):
        runtime_install.install_runtime(app, confirmed=True)
    assert not (app / 'models/depth_pro.pt').exists()
