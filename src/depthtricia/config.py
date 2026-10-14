from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class DepthPreset:
    resolution: int = 1218  # 0 selects the model's standard
    edge_x: int = 2
    edge_y: int = 1

    def validate(self) -> None:
        if self.resolution != 0 and not 196 <= self.resolution <= 4096:
            raise ValueError("Tiefenauflösung muss zwischen 196 und 4096 liegen.")
        if not (0 <= self.edge_x <= 8 and 0 <= self.edge_y <= 8):
            raise ValueError("Edge Fix muss zwischen 0 und 8 liegen.")


@dataclass(frozen=True)
class InferencePreset:
    model_id: str = "da3"
    device: str = "auto"
    resolution: int = 1218
    edge_x: int = 2
    edge_y: int = 1

    @property
    def depth_preset(self) -> DepthPreset:
        return DepthPreset(self.resolution, self.edge_x, self.edge_y)

    def validate(self) -> None:
        from .model_catalog import DEPTH_MODELS
        self.depth_preset.validate()
        if self.model_id not in DEPTH_MODELS or self.device not in {"auto", "cuda", "cpu"}:
            raise ValueError("Ungültiges Modell oder Berechnungsgerät.")


BUILTIN_PRESETS = {
    "standard": InferencePreset(),
    "cpu": InferencePreset(model_id="da2", device="cpu", resolution=0),
    "quick": InferencePreset(resolution=0),
    "fine": InferencePreset(resolution=2048),
    "depthpro": InferencePreset(model_id="depthpro", resolution=0),
}


@dataclass(frozen=True)
class ProcessingConfig:
    app_dir: Path
    model_id: str = "da3"
    device: str = "auto"
    preset: DepthPreset = DepthPreset()
    exiftool_path: Path | None = None
    target_height: int = 2160
    deviation_permille: float = 15.0
    window_position_percent: float = 100.0
    window_back_permille: float = 0.0
    float_left_permille: float = 0.0
    float_right_permille: float = 0.0
    float_top_permille: float = 0.0
    float_bottom_permille: float = 0.0
    gray_anaglyph: bool = False
    append_settings_to_filename: bool = False
    jpeg_quality_sbs: int = 95
    jpeg_quality_anaglyph: int = 90
    copy_metadata: bool = True
    save_depth_map: bool = False

    @property
    def models_dir(self) -> Path:
        return self.app_dir / "models"

    def validate(self) -> None:
        from .model_catalog import DEPTH_MODELS
        self.preset.validate()
        if self.model_id not in DEPTH_MODELS or self.device not in {"auto", "cuda", "cpu"}:
            raise ValueError("Ungültiges Modell oder Berechnungsgerät.")
        numbers = [self.deviation_permille, self.window_position_percent,
                   self.window_back_permille, self.float_left_permille,
                   self.float_right_permille, self.float_top_permille,
                   self.float_bottom_permille]
        if not all(isfinite(v) for v in numbers):
            raise ValueError("Einstellungen müssen endliche Zahlen sein.")
        if not 0 < self.deviation_permille <= 50:
            raise ValueError("Deviation muss zwischen 0 und 50 ‰ liegen.")
        if not 0 <= self.window_position_percent <= 100 or self.target_height < 0:
            raise ValueError("Ungültige Scheinfensterlage oder Ausgabehöhe.")
        if any(v < 0 for v in numbers[2:]):
            raise ValueError("Vorhänge und Rückversatz dürfen nicht negativ sein.")
        if self.window_back_permille and self.window_position_percent != 100:
            raise ValueError("Rückversatz ist nur bei Scheinfensterlage 100 % möglich.")
        if self.float_top_permille and self.float_bottom_permille:
            raise ValueError("Oben und unten können nicht gleichzeitig aktiv sein.")
        if (self.float_top_permille or self.float_bottom_permille) and (self.float_left_permille or self.float_right_permille):
            raise ValueError("Seitliche und kippende Vorhänge können nicht kombiniert werden.")
        if not all(1 <= q <= 100 for q in (self.jpeg_quality_sbs, self.jpeg_quality_anaglyph)):
            raise ValueError("Ungültige JPEG-Qualität.")
