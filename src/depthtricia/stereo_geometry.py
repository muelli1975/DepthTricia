from __future__ import annotations

import numpy as np


def normalize_disparity(disparity: np.ndarray) -> np.ndarray:
    """Finite 0/100 extrema; near=1, far=0, flat scenes remain flat."""
    result = np.asarray(disparity, dtype=np.float32)
    if result.ndim != 2 or not np.isfinite(result).all():
        raise ValueError("Die Tiefenkarte enth�lt ung�ltige Werte.")
    near, far = float(result.max()), float(result.min())
    if near == far:
        return np.zeros_like(result)
    return np.clip((result - far) / (near - far), 0, 1)


def iw3_parameters(width: int, depth_shape: tuple[int, int], deviation: float,
                   window_position: float) -> tuple[float, float]:
    """iw3 measures strength against the long side, SplatTricia against width.

    Scale explicitly for portrait photos. Window 100%=near plane, 0%=far.
    The width/(width-1) endpoint convention is verified at the rendering stage.
    """
    height_d, width_d = depth_shape
    strength = deviation / 10 * width_d / max(height_d, width_d)
    return strength, window_position / 100


def shift_view_and_mask(view, mask, source_offset: float):
    """Translate a float BCHW view and its hole mask before inpainting.

    Positive source offsets move content left. Every sample outside the source
    is a hole, including fractional edge pixels; border colors are placeholders
    for the established inpainting model, never final output strips.
    """
    if not source_offset:
        return view, mask
    import torch
    import torch.nn.functional as F
    batch, _, height, width = view.shape
    if width < 2:
        raise ValueError("Stereoansichten ben�tigen mindestens zwei Pixel Breite.")
    y, x = torch.meshgrid(torch.linspace(-1, 1, height, device=view.device),
                          torch.linspace(-1, 1, width, device=view.device), indexing="ij")
    x = x + 2 * source_offset / (width - 1)
    grid = torch.stack((x, y), dim=-1).unsqueeze(0).expand(batch, -1, -1, -1)
    shifted = F.grid_sample(view.float(), grid, mode="bilinear",
                            padding_mode="border", align_corners=True)
    shifted_mask = F.grid_sample(mask.float(), grid, mode="bilinear",
                                 padding_mode="zeros", align_corners=True) > 0
    outside = ((x < -1) | (x > 1)).reshape(1, 1, height, width)
    return shifted, shifted_mask | outside

