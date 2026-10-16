"""Compare the adapter with the pinned iw3 math without loading large weights."""
from pathlib import Path

import pytest


@pytest.fixture
def runtime():
    torch = pytest.importorskip("torch")
    root = Path(__file__).resolve().parents[1]
    if not (root / "third_party/nunif").is_dir():
        pytest.skip("Prepared upstream inference source is required")
    from depthtricia.runtime import prepare_imports
    prepare_imports(root)
    from iw3.depth_pro_model import batch_infer
    from depthtricia.depth_backend import _infer_depthpro_native

    class NativeModel(torch.nn.Module):
        img_size = 64
        device = torch.device("cpu")

        def __init__(self, dtype):
            super().__init__()
            self.anchor = torch.nn.Parameter(torch.zeros((), dtype=dtype))
            self.last_input = None

        def forward(self, x):
            self.last_input = x.clone()
            # Spatial variation and a nontrivial FOV exercise reciprocal/FOV
            # handling as well as the native and small-source output sizes.
            depth = (x[:, :1] + 1.2).clamp_min(.05)
            fov = torch.full((x.shape[0], 1), 63., dtype=x.dtype, device=x.device)
            return depth, fov

    return torch, NativeModel, batch_infer, _infer_depthpro_native


@pytest.mark.parametrize("height,width", [(96, 144), (144, 96), (32, 48), (96, 32)])
def test_native_depthpro_matches_iw3_inverse_depth(runtime, height, width):
    torch, NativeModel, batch_infer, infer = runtime
    model = NativeModel(torch.float16)
    x = torch.linspace(0, 1, height * width).reshape(1, 1, height, width).expand(1, 3, -1, -1)
    original = x.clone()
    with torch.inference_mode():
        actual = infer(model, x)
        expected = batch_infer(model, x, flip_aug=False, edge_dilation=0,
                               force_disparity=True, device=model.device)
    assert torch.equal(actual, expected)
    expected_size = (height, width) if min(height, width) < model.img_size else (64, 64)
    assert actual.shape == (1, 1, *expected_size)
    assert torch.equal(x, original)
    assert model.last_input.shape[-2:] == (64, 64)


def test_native_depthpro_preserves_existing_cpu_precision(runtime):
    torch, NativeModel, _, infer = runtime
    model = NativeModel(torch.float32)
    with torch.inference_mode():
        result = infer(model, torch.full((1, 3, 96, 144), .25))
    assert model.last_input.dtype == torch.float32
    assert result.dtype == torch.float32
    assert torch.allclose(model.last_input, torch.full_like(model.last_input, -.5))
