from pathlib import Path
import sys

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parent
        sys.path.insert(0, str(root / "src"))
    from depthtricia.gui import main
    raise SystemExit(main(root))
