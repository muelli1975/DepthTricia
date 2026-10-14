from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from .model_catalog import ModelFile


class DownloadCancelled(RuntimeError):
    pass


def verify_model(directory: Path, spec: ModelFile) -> None:
    path = directory / spec.filename
    stat = path.stat()
    if stat.st_size != spec.size:
        raise ValueError(f"Modell ist unvollständig: {spec.filename}")
    record = path.with_name(path.name + ".verified.json")
    signature = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                 "ctime_ns": stat.st_ctime_ns, "sha256": spec.sha256}
    try:
        if json.loads(record.read_text()) == signature:
            return
    except (OSError, ValueError):
        pass
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != spec.sha256:
        raise ValueError(f"Modell-Prüfsumme stimmt nicht: {spec.filename}")
    try:
        record.write_text(json.dumps(signature), encoding="utf-8")
    except OSError:
        pass  # Read-only supplied models remain usable.


def download_models(directory: Path, files: tuple[ModelFile, ...], *,
                    confirmed: bool, progress=None, cancelled=None) -> None:
    """The GUI asks first. This function never obtains or assumes consent."""
    if not confirmed:
        raise PermissionError("Modelldownload wurde nicht bestätigt.")
    directory.mkdir(parents=True, exist_ok=True)
    for spec in files:
        if cancelled and cancelled():
            raise DownloadCancelled("Download abgebrochen.")
        destination = directory / spec.filename
        partial = destination.with_name(destination.name + ".partial")
        received = 0
        digest = hashlib.sha256()
        try:
            request = Request(spec.url, headers={"User-Agent": "DepthTricia/1.0"})
            with urlopen(request, timeout=30) as response, partial.open("wb") as handle:
                while True:
                    if cancelled and cancelled():
                        raise DownloadCancelled("Download abgebrochen.")
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    received += len(block)
                    if received > spec.size:
                        raise ValueError(f"Unerwartete Modellgröße: {spec.filename}")
                    digest.update(block)
                    handle.write(block)
                    if progress:
                        progress(spec.filename, received, spec.size)
            if received != spec.size or digest.hexdigest() != spec.sha256:
                raise ValueError(f"Modelldownload ist unvollständig oder beschädigt: {spec.filename}")
            if cancelled and cancelled():
                raise DownloadCancelled("Download abgebrochen.")
            partial.replace(destination)
        finally:
            partial.unlink(missing_ok=True)
