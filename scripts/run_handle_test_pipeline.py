"""Build, validate, and export handle_test hard/soft parts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exporters.pipeline import export_3mf, export_step, export_stl
from projects.work.handle_test.model import build
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import validate_handle_pair


def main() -> int:
    params = default_parameters()
    hard, soft = build(params)
    stats = validate_handle_pair(hard, soft, params)
    print("Validation:", stats)

    for label, workpiece in (("hard", hard), ("soft", soft)):
        base = f"handle_test_{label}"
        step = export_step(workpiece, base)
        stl = export_stl(workpiece, base)
        mf3 = export_3mf(workpiece, base)
        print(f"{label}: STEP {step.path} ({step.bytes_written} B)")
        print(f"{label}: STL  {stl.path} ({stl.bytes_written} B)")
        print(f"{label}: 3MF  {mf3.path} ({mf3.bytes_written} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
