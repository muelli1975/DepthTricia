from __future__ import annotations
import traceback
from pathlib import Path

from .cache import cache_identity, cache_paths, load_depth, save_depth
from .config import ProcessingConfig
from .downloads import verify_model
from .image_input import collect_images, load_work_image, make_item_key
from .metadata import copy_metadata_to_outputs
from .model_catalog import FILES, missing_files, required_files
from .models import ProcessingItem, ProgressEvent
from .naming import build_output_suffix
from .output_writer import save_depth_png
from .runtime import select_device


class ProcessingCancelled(RuntimeError):
    pass


class ProcessingController:
    def __init__(self, config: ProcessingConfig, event_callback=None, cancel_callback=None):
        self.config, self.event_callback, self.cancel_callback = config, event_callback, cancel_callback

    def _emit(self, stage, key, message, current=0, total=0, item_key="", **details):
        if self.event_callback:
            self.event_callback(ProgressEvent(stage, key, message, current, total, item_key, details))

    def _check_cancelled(self):
        if self.cancel_callback and self.cancel_callback():
            raise ProcessingCancelled("Verarbeitung wurde abgebrochen.")

    def run(self, input_path: Path, output_dir: Path, recursive=False, rebuild_depth=False, limit=0):
        from .depth_backend import DepthSession
        from .stereo_backend import StereoSession
        from .renderer import write_outputs
        self.config.validate()
        missing = missing_files(self.config.models_dir, self.config.model_id)
        if missing:
            raise FileNotFoundError("Lokale Modelle fehlen: " + ", ".join(s.filename for s in missing))
        for spec in required_files(self.config.model_id):
            self._check_cancelled()
            self._emit("verifying", "progress.verifying", "Prüfe lokale Modelle …", filename=spec.filename)
            verify_model(self.config.models_dir, spec)
        device = select_device(self.config.device)
        images = collect_images(input_path, recursive, output_dir)
        if limit < 0:
            raise ValueError("limit darf nicht negativ sein.")
        if limit:
            images = images[:limit]
        if not images:
            raise RuntimeError(f"Keine Bilder gefunden: {input_path}")
        import torch
        device_name = torch.cuda.get_device_name(0) if device.type == "cuda" else "CPU"
        self._emit("start", "progress.start", "Verarbeitung gestartet.", total=len(images), count=len(images), device=device_name)
        directories = {key: output_dir / key for key in ("_temp", "sbs", "anaglyph")}
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)
        suffix = build_output_suffix(self.config)
        items, records, pending = [], {}, []
        checkpoint = self.config.models_dir / FILES[self.config.model_id].filename
        for index, source in enumerate(images, 1):
            self._check_cancelled()
            key = make_item_key(source, input_path)
            identity = cache_identity(source, self.config, checkpoint)
            paths = cache_paths(directories["_temp"], key, identity)
            item = ProcessingItem(source, key, directories["sbs"] / f"{key}{suffix}_sbs.jpg",
                                  directories["anaglyph"] / f"{key}{suffix}_anaglyph.jpg",
                                  depth_png_path=output_dir / "depth_maps" / f"{key}{suffix}_depth.png"
                                  if self.config.save_depth_map else None)
            items.append(item)
            records[key] = paths, identity
            if rebuild_depth or load_depth(*paths, identity) is None:
                pending.append(item)
            self._emit("preparing", "progress.preparing", "Prüfe Tiefenkarten-Cache …", index, len(images), key)
        if pending:
            self._emit("model_loading", "progress.model_loading", "Lade Tiefenmodell …")
            session = DepthSession(self.config, device)
            try:
                self._emit("model_ready", "progress.model_ready", "Tiefenmodell geladen.", load_seconds=session.load_seconds)
                for index, item in enumerate(pending, 1):
                    self._check_cancelled()
                    self._emit("inference", "progress.inference", "Berechne Tiefenkarte …", index, len(pending), item.key)
                    try:
                        rgb = load_work_image(item.source_path, self.config.target_height)
                        depth = session.infer(rgb)
                        self._check_cancelled()
                        paths, identity = records[item.key]
                        save_depth(*paths, depth, identity)
                        self._emit("inference_done", "progress.inference_done", "Tiefenkarte gespeichert.", index, len(pending), item.key)
                    except ProcessingCancelled:
                        raise
                    except Exception as exc:
                        item.status = "fehler_inferenz"
                        self._emit("item_error", "progress.item_error", str(exc), index, len(pending), item.key,
                                   error=str(exc), traceback=traceback.format_exc())
            finally:
                session.close()
            self._emit("model_released", "progress.model_released", "Tiefenmodell freigegeben.")
        else:
            self._emit("inference_skipped", "progress.cache_used", "Vorhandene Tiefenkarten werden verwendet.")
        self._check_cancelled()
        stereo = StereoSession(self.config, device)
        try:
            for index, item in enumerate(items, 1):
                self._check_cancelled()
                if item.status.startswith("fehler"):
                    continue
                self._emit("rendering", "progress.rendering", "Erzeuge Stereoansichten mit Inpainting …", index, len(items), item.key)
                try:
                    paths, identity = records[item.key]
                    depth = load_depth(*paths, identity)
                    if depth is None:
                        raise RuntimeError("Die zwischengespeicherte Tiefenkarte ist nicht gültig.")
                    rgb = load_work_image(item.source_path, self.config.target_height)
                    left, right = stereo.render(rgb, depth)
                    self._check_cancelled()
                    def progress(step, fraction):
                        self._emit("render_step", "progress." + step, step, index, len(items), item.key, step_fraction=fraction)
                    seconds = write_outputs(left, right, item, self.config, progress)
                    if item.depth_png_path is not None:
                        save_depth_png(depth, item.depth_png_path)
                    item.status = "ok"
                    if self.config.copy_metadata:
                        self._emit("metadata", "progress.metadata", "Übertrage Metadaten …", index, len(items), item.key)
                        result = copy_metadata_to_outputs(self.config.exiftool_path, item.source_path, (item.sbs_path, item.anaglyph_path))
                        if result.error:
                            self._emit("item_warning", "progress.metadata_warning", result.error, index, len(items), item.key, error=result.error)
                    self._emit("rendering_done", "progress.rendering_done", "Ausgaben gespeichert.", index, len(items), item.key, anaglyph_seconds=seconds)
                except ProcessingCancelled:
                    raise
                except Exception as exc:
                    item.status = "fehler_rendering"
                    self._emit("item_error", "progress.item_error", str(exc), index, len(items), item.key,
                               error=str(exc), traceback=traceback.format_exc())
        finally:
            stereo.close()
        ok = sum(item.status == "ok" for item in items)
        self._emit("finished", "progress.finished", "Verarbeitung abgeschlossen.", ok, len(items), ok=ok, total_count=len(items))
        return items
