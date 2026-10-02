"""Preview a template or example by importing its build() function."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from preview.viewer import preview_matplotlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        default="projects.examples.test_mounting_plate",
        help="Python module path relative to project root",
    )
    parser.add_argument("--title", default="preview")
    parser.add_argument("--no-show", action="store_true", help="Save PNG only")
    args = parser.parse_args()
    mod = importlib.import_module(args.module)
    if not hasattr(mod, "build"):
        raise SystemExit(f"{args.module} has no build() function")
    model = mod.build()
    path = preview_matplotlib(model, title=args.title, show=not args.no_show)
    print(path)


if __name__ == "__main__":
    main()
