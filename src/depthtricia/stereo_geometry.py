from __future__ import annotations

import numpy as np


def normalize_disparity(disparity: np.ndarray) -> np.ndarray:
    """Finite 0/100 extrema; near=1, far=0, flat scenes remain flat."""
    result = np.asarray(disparity, dtype=np.float32)
    if result.ndim != 2 or not np.isfinite(result).all():
        raise ValueError("Die Tiefenkarte enthält ungültige Werte.")
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


def shift_pair(left: np.ndarray, right: np.ndarray, back_permille: float):
    """Symmetric stereo-window backshift; black outside the source frame."""
    if not back_permille:
        return left, right
    from PIL import Image
    offset = left.shape[1] * back_permille / 2000
    def shift(image, amount):
        return np.asarray(Image.fromarray(image).transform(
            (image.shape[1], image.shape[0]), Image.Transform.AFFINE,
            (1, 0, amount, 0, 1, 0), Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0))).copy()
    return shift(left, offset), shift(right, -offset)
