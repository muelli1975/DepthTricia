from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelFile:
    filename: str
    url: str
    size: int
    sha256: str
    license: str


DEPTH_MODELS = {"da2": "Depth Anything V2 Small", "da3": "Depth Anything 3 Mono Large", "depthpro": "Depth Pro"}
FILES = {
    "da2": ModelFile("depth_anything_v2_vits.pth", "https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth", 99218434, "715fade13be8f229f8a70cc02066f656f2423a59effd0579197bbf57860e1378", "Apache-2.0"),
    "da3": ModelFile("da3mono-large.safetensors", "https://huggingface.co/depth-anything/DA3MONO-LARGE/resolve/main/model.safetensors", 1336734448, "7a799a7f95eb8d4c404c2ca8be3dc3276b350a417ddc4420db72ba850cc0e960", "Apache-2.0"),
    "depthpro": ModelFile("depth_pro.pt", "https://huggingface.co/apple/DepthPro/resolve/main/depth_pro.pt", 1904446787, "3eb35ca68168ad3d14cb150f8947a4edf85589941661fdb2686259c80685c0ce", "Apple-ASCL"),
    "warp": ModelFile("iw3_mask_mlbw_l2_d1_20250903.pth", "https://github.com/nagadomi/nunif/releases/download/0.0.0/iw3_mask_mlbw_l2_d1_20250903.pth", 958587, "fe3ab406ba102662550e34798eac03c0e14b9486bcdc460b0b0e4b97dccfb1b7", "MIT"),
    "inpaint": ModelFile("iw3_light_inpaint_v1_20250919.pth", "https://github.com/nagadomi/nunif/releases/download/0.0.0/iw3_light_inpaint_v1_20250919.pth", 9070711, "8b1a85df321ede3ea45d0b37a7f2c509e941687c062e1d584aab8808c253db6d", "MIT"),
}


def required_files(model_id: str) -> tuple[ModelFile, ...]:
    if model_id not in DEPTH_MODELS:
        raise ValueError("Unbekanntes Tiefenmodell.")
    return FILES[model_id], FILES["warp"], FILES["inpaint"]


def missing_files(directory: Path, model_id: str) -> tuple[ModelFile, ...]:
    return tuple(spec for spec in required_files(model_id)
                 if not (directory / spec.filename).is_file()
                 or (directory / spec.filename).stat().st_size != spec.size)
