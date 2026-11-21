"""Build a relocatable Windows test app with Python sources for Triton's JIT."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "build" / "DepthTricia-Test"
DIST = ROOT / "dist" / "DepthTricia-Windows-Test"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from collect_licenses import collect
from depthtricia.downloads import verify_model
from depthtricia.model_catalog import FILES


def copy(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)
    return dst


def assemble():
    APP.mkdir(parents=True)
    for name in ("src", "assets", "licenses", "tools", "third_party"):
        shutil.copytree(ROOT / name, APP / name, copy_function=copy,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "checkpoints"))
    for name in ("README.md", "README_DE.md", "THIRD_PARTY.md", "LICENSE.txt", "launcher.py"):
        copy(ROOT / name, APP / name)
    python = APP / "python"
    base = Path(sys.base_prefix)
    for name in ("DLLs", "Lib", "tcl", "include", "libs"):
        shutil.copytree(base / name, python / name, copy_function=copy,
                        ignore=shutil.ignore_patterns("site-packages", "__pycache__", "test", "tests", "idle_test"))
    for pattern in ("*.exe", "*.dll", "LICENSE*.txt", "*.pyd"):
        for path in base.glob(pattern):
            copy(path, python / path.name)
    shutil.copytree(Path(sys.prefix) / "Lib/site-packages", python / "Lib/site-packages",
                    copy_function=copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    collect(APP / "LICENSES.txt")
    (APP / "models").mkdir()
    for spec in FILES.values():
        verify_model(ROOT / "models", spec)
        copy(ROOT / "models" / spec.filename, APP / "models" / spec.filename)
    compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    subprocess.run([str(compiler), "/nologo", "/target:winexe", "/platform:x64", "/reference:System.Windows.Forms.dll",
                    "/win32icon:" + str(ROOT / "assets/depthtricia.ico"), "/out:" + str(APP / "DepthTricia.exe"),
                    str(ROOT / "scripts/model_test/Launcher.cs")], check=True)
    (APP / "BUILD_INFO.json").write_text(json.dumps({
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "packages": subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines(),
    }, indent=2), encoding="utf-8")


def pack():
    DIST.mkdir(parents=True)
    groups = {}
    for p in sorted(APP.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or p.suffix == ".pyc" or p.name.endswith(".verified.json"):
            continue
        rel = p.relative_to(APP)
        if rel.parts[0] == "python":
            group = "Laufzeit"
        elif rel.as_posix() in ("models/depth_pro.pt", "models/moge3-vitl.pt"):
            group = "MoGe3" if rel.name.startswith("moge3") else "DepthPro"
        else:
            group = "Programm"
        groups.setdefault(group, []).append(p)
    sums = {}
    for group, paths in groups.items():
        batches = [[]]
        size = 0
        for p in paths:
            n = p.stat().st_size
            if batches[-1] and size + n > 1750_000_000:
                batches.append([])
                size = 0
            batches[-1].append(p)
            size += n
        for number, batch in enumerate(batches, 1):
            target = DIST / f"DepthTricia-Test-{group}-{number:02}.zip"
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
                for p in batch:
                    archive.write(p, p.relative_to(APP))
            if target.stat().st_size >= 2**31:
                raise RuntimeError(f"{target.name} exceeds 2 GiB")
            with target.open("rb") as f:
                sums[target.name] = hashlib.file_digest(f, "sha256").hexdigest()
            print(target.name, target.stat().st_size, flush=True)
    (DIST / "SHA256.json").write_text(json.dumps(sums, indent=2))
    for name in ("Testbuild_entpacken.cmd", "Entpacken.ps1"):
        shutil.copyfile(ROOT / "scripts/model_test" / name, DIST / name)


if __name__ == "__main__":
    {"assemble": assemble, "pack": pack}[sys.argv[1]]()
