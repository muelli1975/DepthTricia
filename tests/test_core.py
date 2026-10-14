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
from depthtricia.stereo_geometry import iw3_parameters, normalize_disparity, shift_pair


def test_depth_extrema_and_flat_scene():
    assert np.array_equal(normalize_disparity(np.array([[2, 4], [3, 2]])), [[0, 1], [.5, 0]])
    assert not normalize_disparity(np.ones((3, 4))).any()
    with pytest.raises(ValueError):
        normalize_disparity(np.array([[float("nan")]]))


def test_width_based_deviation_for_portrait_and_landscape():
    assert iw3_parameters(1920, (1218, 1820), 15, 100) == (1.5, 1)
    assert iw3_parameters(1080, (1820, 1218), 15, 50) == (1.5 * 1218 / 1820, .5)


def test_window_backshift_direction():
    image = np.zeros((16, 1000, 3), dtype=np.uint8)
    image[:, 500] = 255
    left, right = shift_pair(image, image, 10)
    assert np.argmax(left[8, :, 0]) == 495
    assert np.argmax(right[8, :, 0]) == 505


def test_cache_reuses_depth_for_stereo_changes_but_not_depth_changes(tmp_path):
    source, checkpoint = tmp_path / "source.jpg", tmp_path / "model.pth"
    source.write_bytes(b"source")
    checkpoint.write_bytes(b"model")
    cfg = ProcessingConfig(tmp_path)
    identity = cache_identity(source, cfg, checkpoint)
    assert identity == cache_identity(source, replace(cfg, deviation_permille=20), checkpoint)
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
