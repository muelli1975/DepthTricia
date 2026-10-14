from __future__ import annotations
import os
import sys
from pathlib import Path


def prepare_imports(app_dir: Path):
    vendor = app_dir / "third_party"
    required = ("nunif", "da2", "da3", "depthpro")
    for name in required:
        if not (vendor / name).is_dir():
            raise RuntimeError("Lokale Laufzeit fehlt. Bitte scripts/prepare_runtime.py ausführen.")
    os.environ["DEPTHTRICIA_MODEL_DIR"] = str(app_dir / "models")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["XFORMERS_DISABLED"] = "1"
    for path in (vendor / "nunif", vendor / "da2", vendor / "da3/src", vendor / "depthpro/src"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def select_device(requested: str):
    import torch
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("NVIDIA/CUDA ist nicht verfügbar. Bitte CPU oder Automatisch auswählen.")
    return torch.device("cuda" if requested != "cpu" and torch.cuda.is_available() else "cpu")
