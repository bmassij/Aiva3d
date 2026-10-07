"""Regenerate reference_measurements.json and calibrated overlays from photos."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projects.work.handle_test.grid_measure import save_reference_measurements


def main() -> int:
    project = ROOT / "projects" / "work" / "handle_test"
    path = save_reference_measurements(project)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
