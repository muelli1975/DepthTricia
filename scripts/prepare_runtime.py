"""Developer/build step only. Runtime never downloads Python source."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def prepare(local_sources: Path | None = None):
    dependencies = json.loads((ROOT / "dependencies.json").read_text())
    vendor = ROOT / "third_party"
    vendor.mkdir(exist_ok=True)
    for name, spec in dependencies.items():
        destination = vendor / name
        if local_sources:
            source = local_sources / name
            actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
            if actual != spec["commit"]:
                raise RuntimeError(f"Unexpected source revision for {name}")
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        else:
            if not destination.exists():
                subprocess.run(["git", "clone", "--no-checkout", "https://github.com/" + spec["repo"] + ".git", str(destination)], check=True)
            subprocess.run(["git", "-C", str(destination), "checkout", "--force", "--detach", spec["commit"]], check=True)
    # Only inference is used. Suppress eager training/loss imports, not math.
    nunif = vendor / "nunif"
    (nunif / "nunif/__init__.py").write_text('# DepthTricia inference-only packaging; see THIRD_PARTY.md.\n')
    (nunif / "nunif/modules/__init__.py").write_text('# Explicit inference module imports only.\n')
    (nunif / "iw3/models/__init__.py").write_text(
        'from .mlbw import MLBW\nfrom .light_inpaint_v1 import LightInpaintV1\nfrom .depth_aa import DepthAA\n')
    (nunif / "iw3/hub_dir.py").write_text(
        'import os\nHUB_MODEL_DIR = os.environ["DEPTHTRICIA_MODEL_DIR"]\n')
    path = nunif / "iw3/inpaint_utils.py"
    text = path.read_text()
    original = 'path.join(ensure_home_dir("iw3"), "inpaint_models.yml")'
    if original not in text:
        raise RuntimeError("Upstream inpaint configuration changed")
    path.write_text(text.replace(original, 'path.join(HUB_MODEL_DIR, "inpaint_models.yml")'))
    # Map the checked local checkpoint rather than duplicating it in RAM while
    # loading. The model remains in the explicitly selected numerical precision.
    path = vendor / "depthpro/src/depth_pro/depth_pro.py"
    text = path.read_text()
    original = 'torch.load(config.checkpoint_uri, map_location="cpu")'
    replacement = 'torch.load(config.checkpoint_uri, map_location="cpu", weights_only=True, mmap=True)'
    if original not in text:
        raise RuntimeError("Upstream Depth Pro checkpoint loader changed")
    path.write_text(text.replace(original, replacement))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-sources", type=Path)
    prepare(parser.parse_args().local_sources)
