from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

CACHE_VERSION = 1


def fingerprint_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def model_signature(path: Path) -> dict:
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for offset in sorted({0, max(0, stat.st_size // 2 - 524288), max(0, stat.st_size - 1048576)}):
            handle.seek(offset)
            digest.update(handle.read(1048576))
    return {"name": path.name, "size": stat.st_size, "sample": digest.hexdigest()}


def cache_identity(source: Path, config, checkpoint: Path) -> dict:
    return {"version": CACHE_VERSION, "source": fingerprint_file(source),
            "model": config.model_id, "checkpoint": model_signature(checkpoint),
            "height": config.target_height, "resolution": config.preset.resolution,
            "edge_x": config.preset.edge_x, "edge_y": config.preset.edge_y,
            "pipeline": "iw3-normalized-disparity-v1"}


def cache_paths(directory: Path, key: str, identity: dict):
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:16]
    stem = f"{key}__{digest}"
    return directory / (stem + ".npy"), directory / (stem + ".json")


def load_depth(path: Path, record: Path, identity: dict) -> np.ndarray | None:
    try:
        meta = json.loads(record.read_text(encoding="utf-8"))
        if meta["identity"] != identity or meta["sha256"] != fingerprint_file(path):
            return None
        depth = np.load(path, allow_pickle=False)
        if depth.ndim != 2 or depth.dtype != np.float32 or not np.isfinite(depth).all():
            return None
        if depth.min() < 0 or depth.max() > 1:
            return None
        return depth
    except (OSError, ValueError, KeyError, TypeError):
        return None


def save_depth(path: Path, record: Path, depth: np.ndarray, identity: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    with partial.open("wb") as handle:
        np.save(handle, np.asarray(depth, dtype=np.float32), allow_pickle=False)
    partial.replace(path)
    meta = {"identity": identity, "sha256": fingerprint_file(path)}
    partial = record.with_name(record.name + ".partial")
    partial.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    partial.replace(record)


def clear_temporary_files(temp_dir: Path) -> None:
    if temp_dir.name != "_temp":
        raise ValueError("Nur der interne _temp-Ordner darf gelöscht werden.")
    if temp_dir.is_symlink():
        temp_dir.unlink()
    elif temp_dir.exists():
        shutil.rmtree(temp_dir)
