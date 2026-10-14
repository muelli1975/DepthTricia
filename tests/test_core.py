from dataclasses import replace
import hashlib
import io
from pathlib import Path

import numpy as np
import pytest

from depthtricia.cache import cache_identity, cache_paths, load_depth, save_depth
from depthtricia.config import ProcessingConfig, DepthPreset
from depthtricia.downloads import DownloadCancelled, download_models
from depthtricia.model_catalog import ModelFile
from depthtricia.stereo_geometry import iw3_parameters, normalize_disparity


def test_depth_extrema_and_flat_scene():
    assert np.array_equal(normalize_disparity(np.array([[2, 4], [3, 2]])), [[0, 1], [.5, 0]])
    assert not normalize_disparity(np.ones((3, 4))).any()
    with pytest.raises(ValueError):
        normalize_disparity(np.array([[float("nan")]]))


def test_width_based_deviation_for_portrait_and_landscape():
    assert iw3_parameters(1920, (1218, 1820), 15, 100) == (1.5, 1)
    assert iw3_parameters(1080, (1820, 1218), 15, 50) == (1.5 * 1218 / 1820, .5)


def test_cache_reuses_depth_for_stereo_changes_but_not_depth_changes(tmp_path):
    source, checkpoint = tmp_path / "source.jpg", tmp_path / "model.pth"
    source.write_bytes(b"source")
    checkpoint.write_bytes(b"model")
    cfg = ProcessingConfig(tmp_path)
    identity = cache_identity(source, cfg, checkpoint)
    assert identity == cache_identity(source, replace(cfg, deviation_permille=20), checkpoint)
    assert identity == cache_identity(source, replace(cfg, save_depth_map=True, append_settings_to_filename=True), checkpoint)
    assert identity != cache_identity(source, replace(cfg, target_height=0), checkpoint)
    assert identity != cache_identity(source, replace(cfg, preset=DepthPreset(resolution=2048)), checkpoint)
    paths = cache_paths(tmp_path, "image", identity)
    data = np.array([[0, .5, 1]], dtype=np.float32)
    save_depth(*paths, data, identity)
    assert np.array_equal(load_depth(*paths, identity), data)
    paths[0].write_bytes(b"damaged")
    assert load_depth(*paths, identity) is None


def spec(data=b"weights"):
    return ModelFile("test.pth", "https://example.invalid/model", len(data), hashlib.sha256(data).hexdigest(), "MIT")


def test_download_requires_consent_before_any_io(tmp_path, monkeypatch):
    monkeypatch.setattr("depthtricia.downloads.urlopen", lambda *a, **kw: pytest.fail("Network access without consent"))
    target = tmp_path / "models"
    with pytest.raises(PermissionError):
        download_models(target, (spec(),), confirmed=False)
    assert not target.exists()


def test_download_checks_hash_before_replacing_existing_model(tmp_path, monkeypatch):
    target = tmp_path / "test.pth"
    target.write_bytes(b"old")
    monkeypatch.setattr("depthtricia.downloads.urlopen", lambda *a, **kw: io.BytesIO(b"damaged"))
    with pytest.raises(ValueError):
        download_models(tmp_path, (spec(),), confirmed=True)
    assert target.read_bytes() == b"old"
    assert not (tmp_path / "test.pth.partial").exists()
    monkeypatch.setattr("depthtricia.downloads.urlopen", lambda *a, **kw: io.BytesIO(b"weights"))
    download_models(tmp_path, (spec(),), confirmed=True)
    assert target.read_bytes() == b"weights"


def test_download_cancel_keeps_existing_model(tmp_path, monkeypatch):
    (tmp_path / "test.pth").write_bytes(b"old")
    monkeypatch.setattr("depthtricia.downloads.urlopen", lambda *a, **kw: pytest.fail("Cancelled download started"))
    with pytest.raises(DownloadCancelled):
        download_models(tmp_path, (spec(),), confirmed=True, cancelled=lambda: True)
    assert (tmp_path / "test.pth").read_bytes() == b"old"


@pytest.mark.parametrize('available', [False, True])
def test_automatic_device_and_explicit_cpu(monkeypatch, available):
    import sys
    from types import SimpleNamespace
    from depthtricia.runtime import select_device
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: available), device=lambda name: name))
    assert select_device('auto') == ('cuda' if available else 'cpu')
    assert select_device('cpu') == 'cpu'
    if available:
        assert select_device('cuda') == 'cuda'
    else:
        with pytest.raises(RuntimeError, match='NVIDIA/CUDA'):
            select_device('cuda')


def test_complete_preset_migration_preserves_own_names_and_old_cpu_choice():
    from depthtricia.config import BUILTIN_PRESETS
    from depthtricia.presets import restore_presets, preset_choices
    from depthtricia.i18n import Translator
    own, active, builtin, profile = restore_presets({
        'model_id': 'da2', 'device': 'cpu', 'builtin_preset': 'fine',
        'depth_presets': {'Standard': {'resolution': 1218, 'edge_x': 2, 'edge_y': 1}}})
    assert profile.model_id == 'da2' and profile.device == 'cpu'
    assert profile.resolution == 2048 and active in own and builtin is None
    assert own['Standard']['model_id'] == 'da2' and own['Standard']['device'] == 'cpu'
    choices = preset_choices(Translator().tr, own)
    assert choices['Standard'] == ('builtin', 'standard')
    assert ('own', 'Standard') in choices.values()
    own2, active2, builtin2, profile2 = restore_presets({
        'preset_schema': 1, 'model_id': 'da2', 'device': 'cpu', 'builtin_preset': 'standard',
        'depth_presets': own})
    assert profile2 == BUILTIN_PRESETS['standard']
    assert active2 == '' and builtin2 == 'standard' and own2 == own

