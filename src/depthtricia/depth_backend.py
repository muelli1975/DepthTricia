from __future__ import annotations
from dataclasses import replace
import time

import numpy as np

from .config import ProcessingConfig
from .model_catalog import FILES, MODEL_STANDARD_RESOLUTIONS
from .runtime import prepare_imports
from .stereo_geometry import normalize_disparity


class DepthSession:
    """Local weights only; no torch.hub/Hugging Face network loader."""
    def __init__(self, config: ProcessingConfig, device):
        import torch
        prepare_imports(config.app_dir)
        start = time.perf_counter()
        self.config, self.device = config, device
        self.model = None
        checkpoint = config.models_dir / FILES[config.model_id].filename
        if config.model_id == "da2":
            from depth_anything.dpt import DPT_DINOv2
            self.model = DPT_DINOv2(encoder="v2_vits", localhub=True)
            self.model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True), strict=True)
        elif config.model_id == "da3":
            from depth_anything_3.cfg import create_object, load_config
            from depth_anything_3.registry import MODEL_REGISTRY
            from safetensors.torch import load_file
            self.model = create_object(load_config(MODEL_REGISTRY["da3mono-large"]))
            state = load_file(str(checkpoint), device="cpu")
            state = {key[len("model."):]: value for key, value in state.items() if key.startswith("model.")}
            self.model.load_state_dict(state, strict=True)
        else:
            from depth_pro.depth_pro import create_model_and_transforms, DEFAULT_MONODEPTH_CONFIG_DICT
            settings = replace(DEFAULT_MONODEPTH_CONFIG_DICT, checkpoint_uri=str(checkpoint))
            precision = torch.float16 if device.type == "cuda" else torch.float32
            self.model, self.transform = create_model_and_transforms(config=settings, device=device, precision=precision)
        self.model = self.model.eval().to(device)
        self.load_seconds = time.perf_counter() - start

    def infer(self, rgb: np.ndarray) -> np.ndarray:
        import torch
        from iw3.dilation import dilate_edge
        from iw3.depth_anything_model import batch_preprocess
        from nunif.device import autocast
        x = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).float().div_(255).unsqueeze(0).to(self.device)
        edge = (self.config.preset.edge_x, self.config.preset.edge_y)
        with torch.inference_mode():
            if self.config.model_id == "depthpro":
                prepared = self.transform(__import__("PIL.Image", fromlist=["Image"]).fromarray(rgb))
                depth = self.model.infer(prepared)["depth"]
                disparity = depth.clamp(1e-4, 1e4).reciprocal().reshape(1, 1, *depth.shape[-2:])
            else:
                default = MODEL_STANDARD_RESOLUTIONS[self.config.model_id]
                resolution = self.config.preset.resolution or default
                resolution = ((resolution + 13) // 14) * 14
                x = batch_preprocess(x, lower_bound=resolution, limit_resolution=False)
                # Match iw3's documented DA3 inference precision on capable GPUs.
                amp_dtype = (torch.bfloat16 if self.config.model_id == "da3"
                             and self.device.type == "cuda" and torch.cuda.is_bf16_supported()
                             else None)
                with autocast(device=self.device, enabled=self.device.type == "cuda", dtype=amp_dtype):
                    if self.config.model_id == "da2":
                        disparity = self.model(x).unsqueeze(1).float()
                    else:
                        out = self.model(x.unsqueeze(1))
                        depth, sky = out["depth"].float(), out["sky"].float()
                        sky_weight = (sky.clamp(0.3, 1) - 0.3) / 0.7
                        disparity = (depth + 0.2).reciprocal() * (1 - sky_weight)
                        if ((sky <= 0.3).sum()).item() < 10:
                            disparity = torch.zeros_like(disparity)
            disparity = disparity.float().reshape(1, 1, *disparity.shape[-2:])
            if any(edge):
                disparity = dilate_edge(disparity, edge)
            return normalize_disparity(disparity[0, 0].cpu().numpy())

    def close(self):
        self.model = None
        import gc
        gc.collect()
        if self.device.type == "cuda":
            import torch
            torch.cuda.empty_cache()
