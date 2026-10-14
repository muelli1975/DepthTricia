"""Build-time download of the official, pinned Windows ExifTool distribution."""
from pathlib import Path
import hashlib
import io
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://downloads.sourceforge.net/project/exiftool/exiftool-13.59_64.zip"
SHA256 = "44b512b25af500724ba579d0a53c8fc5851628b692dd5e5d94ae4a15c2cba9ec"


def prepare():
    with urllib.request.urlopen(URL, timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError("ExifTool archive checksum mismatch")
    tools = ROOT / "tools"
    tools.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for entry in archive.infolist():
            relative = Path(entry.filename).relative_to("exiftool-13.59_64")
            if ".." in relative.parts or relative.is_absolute():
                raise RuntimeError("Unsafe ExifTool archive path")
            destination = tools / relative
            if entry.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
    (tools / "exiftool(-k).exe").replace(tools / "exiftool.exe")
    print("Prepared ExifTool 13.59 x64 with its accompanying files and licenses.")


if __name__ == "__main__":
    prepare()
