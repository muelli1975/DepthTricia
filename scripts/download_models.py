"""Build/development download; a separate explicit --confirm is required."""
from pathlib import Path
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from depthtricia.model_catalog import required_files, missing_files
from depthtricia.downloads import download_models

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+", choices=["da2", "da3", "depthpro"])
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    specs = {spec.filename: spec for model in args.models for spec in missing_files(ROOT / "models", model)}
    print("Download:", ", ".join(specs), flush=True)
    download_models(ROOT / "models", tuple(specs.values()), confirmed=args.confirm)
