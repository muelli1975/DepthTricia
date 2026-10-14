from pathlib import Path
import argparse
from .config import ProcessingConfig, DepthPreset
from .controller import ProcessingController


def main():
    parser = argparse.ArgumentParser(description="DepthTricia local image conversion")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--app-dir", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--model", choices=["da2", "da3", "depthpro"], default="da3")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--resolution", type=int, default=1218)
    parser.add_argument("--deviation", type=float, default=15)
    parser.add_argument("--window", type=float, default=100)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--rebuild-depth", action="store_true")
    args = parser.parse_args()
    config = ProcessingConfig(app_dir=args.app_dir.resolve(), model_id=args.model, device=args.device,
                              preset=DepthPreset(resolution=args.resolution), deviation_permille=args.deviation,
                              window_position_percent=args.window, exiftool_path=args.app_dir / "tools/exiftool.exe")
    def progress(event):
        print(event.current, event.total, event.item_key, event.fallback_message, flush=True)
    items = ProcessingController(config, progress).run(args.input, args.output, args.recursive, args.rebuild_depth)
    return 0 if all(item.status == "ok" for item in items) else 1


if __name__ == "__main__":
    raise SystemExit(main())
