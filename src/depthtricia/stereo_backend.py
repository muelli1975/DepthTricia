from __future__ import annotations
import numpy as np

from .config import ProcessingConfig
from .model_catalog import FILES
from .runtime import prepare_imports
from .stereo_geometry import iw3_parameters, shift_pair


class StereoSession:
    def __init__(self, config: ProcessingConfig, device):
        prepare_imports(config.app_dir)
        from nunif.models import load_model
        from iw3 import inpaint_utils
        from iw3.mlbw_inpaint import MLBWInpaintImage
        device_id = 0 if device.type == "cuda" else -1
        warp, _ = load_model(str(config.models_dir / FILES["warp"].filename), device_ids=[device_id], weights_only=True)
        warp = warp.eval()
        warp.delta_output = True
        # Replace the URL catalogue with the checked local image checkpoint.
        inpaint_utils.INPAINT_MODELS = {"light_inpaint_v1": {
            "image": str(config.models_dir / FILES["inpaint"].filename), "video": None}}
        self.model = MLBWInpaintImage(name="light_inpaint_v1", device_id=device_id, mask_mlbw=warp)
        self.config, self.device = config, device

    def render(self, rgb: np.ndarray, disparity: np.ndarray):
        import torch
        x = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).float().div_(255).unsqueeze(0).to(self.device)
        depth = torch.from_numpy(np.ascontiguousarray(disparity)).reshape(1, 1, *disparity.shape).to(self.device)
        strength, convergence = iw3_parameters(rgb.shape[1], disparity.shape,
                                              self.config.deviation_permille,
                                              self.config.window_position_percent)
        with torch.inference_mode():
            left, right = self.model.infer(x, depth, divergence=strength, convergence=convergence,
                                          synthetic_view="both", inner_dilation=0, outer_dilation=0,
                                          max_width=None, enable_amp=self.device.type == "cuda")
        def rgb8(tensor):
            return tensor[0].permute(1, 2, 0).clamp(0, 1).mul(255).round().to(torch.uint8).cpu().numpy()
        return shift_pair(rgb8(left), rgb8(right), self.config.window_back_permille)

    def close(self):
        self.model = None
        import gc
        gc.collect()
        if self.device.type == "cuda":
            import torch
            torch.cuda.empty_cache()
