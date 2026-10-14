from pathlib import Path
import sys

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parent
        sys.path.insert(0, str(root / "src"))
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        import json
        import traceback
        report_path = Path(sys.argv[2]).resolve()
        try:
            from depthtricia.smoke_test import run
            report = {"ok": True, **run(root)}
        except Exception:
            report = {"ok": False, "traceback": traceback.format_exc()}
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(0 if report["ok"] else 1)
    from depthtricia.gui import main
    raise SystemExit(main(root))
