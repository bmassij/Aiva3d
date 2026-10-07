#!/usr/bin/env python3
"""
Analyze handle_test reference photos with Qwen3-VL via local LM Studio.

Requires LM Studio running with a loaded vision model (default id from VISION_MODEL).

Example:
  set VISION_MODEL=qwen3-vl-8b-instruct
  .\\.venv\\Scripts\\python.exe scripts\\analyze_handle_reference_vision.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
    HARD_SOFT_CLEARANCE_MM,
)
from projects.work.handle_test.grip_ergonomic_design import recommend_grip_design
from aiva3d.ai.handle_vision_prompts import (  # noqa: E402
    HANDLE_PAIR_USER_TEMPLATE,
    HANDLE_SINGLE_USER_TEMPLATE,
    HANDLE_VISION_SYSTEM,
    METAL_LOOP_SILHOUETTE_SYSTEM,
    METAL_LOOP_SILHOUETTE_TEMPLATE,
)
from aiva3d.ai.lmstudio_client import LMStudioError  # noqa: E402
from aiva3d.ai.settings import load_settings  # noqa: E402
from aiva3d.ai.vision_provider import LMStudioVisionProvider, check_vision_available  # noqa: E402

REFERENCE_DIR = ROOT / "projects" / "work" / "handle_test" / "reference"
DEFAULT_PHOTOS = (
    "WhatsApp Image 2026-10-02 at 20.16.42.jpeg",
    "WhatsApp Image 2026-10-02 at 20.16.42 (1).jpeg",
)


def _resolve_photos(names: list[str]) -> list[Path]:
    out: list[Path] = []
    for name in names:
        p = REFERENCE_DIR / name
        if not p.is_file():
            raise FileNotFoundError(f"Reference photo missing: {p}")
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qwen3-VL analysis of handle reference photos")
    parser.add_argument(
        "--photo",
        action="append",
        dest="photos",
        help="Reference JPEG name under handle_test/reference/ (repeat for multiple)",
    )
    parser.add_argument(
        "--pair",
        action="store_true",
        help="Analyze both default photos in one multimodal request (recommended)",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=REFERENCE_DIR / "vision_analysis.md",
        help="Markdown report path",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=REFERENCE_DIR / "vision_analysis.json",
        help="JSON report path",
    )
    parser.add_argument(
        "--metal-loop",
        action="store_true",
        help="Map the bare-metal D-loop silhouette (oval vs stadium, hex in plane)",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    provider = LMStudioVisionProvider.from_env()

    print(f"LM Studio: {settings.lmstudio_base_url}")
    print(f"Vision model: {provider.model_id}")
    print(f"Reference dir: {REFERENCE_DIR}")

    try:
        check_vision_available(provider)
    except LMStudioError as exc:
        print(f"ERROR: {exc}")
        print("Start LM Studio and load qwen3-vl-8b-instruct (or set VISION_MODEL).")
        return 1

    if args.metal_loop:
        paths = _resolve_photos([DEFAULT_PHOTOS[0]])
        prompt = METAL_LOOP_SILHOUETTE_TEMPLATE.format(photo_name=paths[0].name)
        print(f"Sending metal-loop silhouette analysis: {paths[0].name}")
        result = provider.analyze_image(
            image_path=str(paths[0]),
            prompt=prompt,
            system=METAL_LOOP_SILHOUETTE_SYSTEM,
        )
        if args.out_md == REFERENCE_DIR / "vision_analysis.md":
            args.out_md = REFERENCE_DIR / "vision_metal_loop.md"
        if args.out_json == REFERENCE_DIR / "vision_analysis.json":
            args.out_json = REFERENCE_DIR / "vision_metal_loop.json"
    elif args.pair or not args.photos:
        paths = _resolve_photos(list(DEFAULT_PHOTOS))
        prompt = HANDLE_PAIR_USER_TEMPLATE.format(
            photo1_name=paths[0].name,
            photo2_name=paths[1].name,
        )
        print("Sending pair analysis (2 images)...")
        result = provider.analyze_images(
            image_paths=paths,
            prompt=prompt,
            system=HANDLE_VISION_SYSTEM,
        )
    else:
        paths = _resolve_photos(args.photos)
        if len(paths) == 1:
            prompt = HANDLE_SINGLE_USER_TEMPLATE.format(photo_name=paths[0].name)
            print(f"Sending single image: {paths[0].name}")
            result = provider.analyze_image(
                image_path=str(paths[0]),
                prompt=prompt,
                system=HANDLE_VISION_SYSTEM,
            )
        else:
            names = ", ".join(f"{i + 1}. {p.name}" for i, p in enumerate(paths))
            prompt = (
                f"Images in order: {names}\n\n"
                + HANDLE_PAIR_USER_TEMPLATE.format(
                    photo1_name=paths[0].name,
                    photo2_name=paths[1].name if len(paths) > 1 else paths[0].name,
                )
            )
            print(f"Sending {len(paths)} images...")
            result = provider.analyze_images(
                image_paths=paths,
                prompt=prompt,
                system=HANDLE_VISION_SYSTEM,
            )

    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["settings"] = {
        "lmstudio_base_url": settings.lmstudio_base_url,
        "vision_model": provider.model_id,
        "vision_temperature": settings.vision_temperature,
        "vision_max_tokens": settings.vision_max_tokens,
    }
    ergo = None
    if not args.metal_loop:
        ergo = recommend_grip_design(
            photo_length_mm=GRIP_LENGTH_MM,
            photo_outer_diameter_mm=GRIP_OUTER_DIAMETER_MM,
            photo_core_diameter_mm=HARD_CORE_DIAMETER_MM,
            clearance_mm=HARD_SOFT_CLEARANCE_MM,
        )
        result["ergonomic_design_python"] = ergo.to_dict()

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# Handle reference — Qwen3-VL analysis",
        "",
        f"- **Model:** {result['model']}",
        f"- **Generated:** {result['generated_at']}",
        f"- **Images:**",
    ]
    for img in result.get("images", []):
        md_lines.append(f"  - `{Path(img).name}`")
    md_lines.extend(["", "---", "", result.get("analysis", ""), ""])
    if ergo is not None:
        md_lines.extend(["", "---", "", ergo.markdown_nl(), ""])
    args.out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.out_json}")
    print("\n--- Analysis (preview) ---\n")
    preview = result.get("analysis", "")[:4000]
    try:
        print(preview)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(preview.encode("utf-8", errors="replace") + b"\n")
    if len(result.get("analysis", "")) > 4000:
        print("\n... (truncated; see markdown file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
