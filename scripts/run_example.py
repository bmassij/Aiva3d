"""Run an example script from projects/examples by name."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a projects/examples script")
    parser.add_argument("name", nargs="?", default="test_mounting_plate", help="Script stem without .py")
    args = parser.parse_args()
    path = ROOT / "projects" / "examples" / f"{args.name}.py"
    if not path.exists():
        raise SystemExit(f"Not found: {path}")
    runpy.run_path(str(path), run_name="__main__")


if __name__ == "__main__":
    main()
