"""Tensor checks run in the Windows build with its actual PyTorch runtime."""
from contextlib import nullcontext
from dataclasses import replace
import sys
from types import SimpleNamespace
import pytest

torch = pytest.importorskip("torch")
from depthtricia.config import ProcessingConfig
from depthtricia.stereo_backend import StereoSession
from depthtricia.stereo_geometry import shift_view_and_mask


@pytest.mark.parametrize("height,width,back", [(16, 1000, 10), (40, 200, 10), (300, 100, 10)])
def test_width_based_translation_and_missing_edges(height, width, back):
    view = torch.arange(width).float().reshape(1, 1, 1, width).expand(1, 3, height, width)
    mask = torch.zeros((1, 1, height, width), dtype=torch.bool)
    offset = width * back / 2000
    left, left_mask = shift_view_and_mask(view, mask, offset)
    right, right_mask = shift_view_and_mask(view, mask, -offset)
    margin = int(offset) + 2
    assert torch.allclose(left[..., margin:-margin] - right[..., margin:-margin],
                          torch.full_like(left[..., margin:-margin], width * back / 1000), atol=0.001)
    assert left_mask[..., -1].all() and right_mask[..., 0].all()
    assert not left_mask[..., 0].any() and not right_mask[..., -1].any()
    assert left.shape == right.shape == view.shape
    assert left_mask.dtype == right_mask.dtype == torch.bool


def test_fractional_shift_preserves_internal_holes_and_zero_is_unchanged():
    view = torch.ones((1, 3, 4, 100))
    mask = torch.zeros((1, 1, 4, 100), dtype=torch.bool)
    mask[..., 50] = True
    unchanged, unchanged_mask = shift_view_and_mask(view, mask, 0)
    assert unchanged is view and unchanged_mask is mask
    _, shifted_mask = shift_view_and_mask(view, mask, .5)
    assert shifted_mask[..., 49:51].all()
    assert shifted_mask[..., -1].all()
    assert not shifted_mask[..., :49].any()


def test_backshift_fills_both_edges_before_rgb_conversion(tmp_path, monkeypatch):
    calls = []
    def warp(model, x, depth, *args):
        logits = torch.zeros((1, 1, *x.shape[-2:]))
        logits[..., 50] = 1
        return x.clone(), x.clone(), logits.clone(), logits.clone()
    def fill(view, mask):
        calls.append((view.clone(), mask.clone()))
        return torch.where(mask, torch.full_like(view, .75), view)
    monkeypatch.setitem(sys.modules, "iw3", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "iw3.mlbw_inpaint", SimpleNamespace(apply_divergence=warp, MASK_MLBW_THRESHOLD=.15))
    monkeypatch.setitem(sys.modules, "iw3.backward_warp", SimpleNamespace(postprocess_hole_mask=lambda logits, size, threshold: logits > threshold))
    monkeypatch.setitem(sys.modules, "nunif", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "nunif.device", SimpleNamespace(autocast=lambda **kw: nullcontext()))
    session = StereoSession.__new__(StereoSession)
    session.config = ProcessingConfig(tmp_path, window_back_permille=20)
    session.device = torch.device("cpu")
    session.model = SimpleNamespace(mask_mlbw=object(), model=SimpleNamespace(infer=fill))
    view = torch.full((1, 3, 16, 100), .25)
    depth = torch.ones((1, 1, 32, 200))
    left, right = session._infer_pair(view, depth)
    assert len(calls) == 2
    assert left[..., -1].eq(.75).all() and right[..., 0].eq(.75).all()
    assert left[..., 49].eq(.75).all() and right[..., 51].eq(.75).all()
    assert left[..., 20].eq(.25).all() and right[..., 20].eq(.25).all()
    session.config = replace(session.config, window_back_permille=0)
    session.model = SimpleNamespace(infer=lambda *args, **kw: (view, view))
    zero_left, zero_right = session._infer_pair(view, depth)
    assert zero_left is view and zero_right is view
