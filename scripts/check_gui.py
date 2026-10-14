from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from depthtricia.gui_check import check
print(json.dumps(check(ROOT), indent=2))
