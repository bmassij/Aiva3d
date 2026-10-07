import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import re
import zipfile

from aiva3d.freecad.fcstd_view import ensure_visible_camera

p = Path(r"D:\AI\3d\projects\work\handle_test\exports\handle_assembly.FCStd")
print("patched", ensure_visible_camera(p))
with zipfile.ZipFile(p) as z:
    gui = z.read("GuiDocument.xml").decode("utf-8")
m = re.search(r'<Camera settings="([^"]*)"/>', gui)
print(m.group(1) if m else "NO CAMERA")
