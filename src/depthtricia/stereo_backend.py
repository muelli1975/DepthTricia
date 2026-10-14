from __future__ import annotations
import numpy as np

from .config import ProcessingConfig
from .model_catalog import FILES
from .runtime import prepare_imports
from .stereo_geometry import iw3_parameters, shift_view_and_mask


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
        with torch.inference_mode():
            left, right = self._infer_pair(x, depth)
        def rgb8(tensor):
            return tensor[0].permute(1, 2, 0).clamp(0, 1).mul(255).round().to(torch.uint8).cpu().numpy()
        return rgb8(left), rgb8(right)

    def _infer_pair(self, x, depth):
        """Use upstream warping/inpainting with scene translation between them."""
        strength, convergence = iw3_parameters(x.shape[-1], depth.shape[-2:],
                                              self.config.deviation_permille,
                                              self.config.window_position_percent)
        enable_amp = self.device.type == "cuda"
        if not self.config.window_back_permille:
            return self.model.infer(x, depth, divergence=strength, convergence=convergence,
                                    synthetic_view="both", inner_dilation=0, outer_dilation=0,
                                    max_width=None, enable_amp=enable_amp)
        from iw3.mlbw_inpaint import apply_divergence, MASK_MLBW_THRESHOLD
        from iw3.backward_warp import postprocess_hole_mask
        from nunif.device import autocast
        left, right, left_logits, right_logits = apply_divergence(
            self.model.mask_mlbw, x, depth, strength, convergence, False, "both", enable_amp)
        # Match upstream left-eye orientation during mask postprocessing.
        left_mask = postprocess_hole_mask(left_logits.flip(-1), left.shape[-2:],
                                          MASK_MLBW_THRESHOLD).flip(-1)
        right_mask = postprocess_hole_mask(right_logits, right.shape[-2:], MASK_MLBW_THRESHOLD)
        offset = x.shape[-1] * self.config.window_back_permille / 2000
        left, left_mask = shift_view_and_mask(left, left_mask, offset)
        right, right_mask = shift_view_and_mask(right, right_mask, -offset)
        with autocast(device=self.device, enabled=enable_amp):
            left = self.model.model.infer(left.flip(-1), left_mask.flip(-1)).flip(-1)
            right = self.model.model.infer(right, right_mask)
        return left, right

    def close(self):
        self.model = None
        import gc
        gc.collect()
        if self.device.type == "cuda":
            import torch
            torch.cuda.empty_cache()

