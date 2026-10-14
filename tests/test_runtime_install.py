import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from depthtricia import runtime_install
from depthtricia.downloads import DownloadCancelled


@pytest.fixture
def split_app(tmp_path):
    app = tmp_path / 'DepthTricia'
    libraries = app / '_internal/torch/lib'
    libraries.mkdir(parents=True)
    (libraries / 'a.dll').write_bytes(b'first library')
    (libraries / 'b.dll').write_bytes(b'second library')
    (app / 'LICENSES.txt').write_text('Test license')
    path = Path(__file__).resolve().parents[1] / 'scripts/runtime_chunks.py'
    spec = importlib.util.spec_from_file_location('runtime_chunks', path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    data = builder.split_runtime(app, group_bytes=16)
    return app, data


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
