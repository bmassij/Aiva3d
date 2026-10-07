"""LM Studio diagnostic for the CadQuery fine-tune (requires local model)."""

from __future__ import annotations

import argparse
import json
import sys

from aiva3d.ai.cadquery_provider import CadQueryProvider
from aiva3d.ai.code_validator import validate_cadquery_code
from aiva3d.ai.lmstudio_client import LMStudioError
from aiva3d.ai.pipeline import run_cadquery_pipeline
from aiva3d.ai.sandbox_runner import execute_cadquery_in_subprocess
from aiva3d.ai.settings import load_settings
from aiva3d.ai.types import CadSpecification

FLANGE_PROMPT = (
    "Design a 60mm diameter flange, 10mm thick, with a 20mm bore and six 6mm bolt "
    "holes on a 44mm circle."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test Qwen2.5-Coder-7B-CadQuery via LM Studio")
    parser.add_argument(
        "--prompt",
        default=FLANGE_PROMPT,
        help="Mechanical part description for the CadQuery model",
    )
    parser.add_argument(
        "--no-repair",
        action="store_true",
        help="Disable repair loop (single attempt)",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    provider = CadQueryProvider.from_env()
    spec = CadSpecification(
        description=args.prompt,
        dimensions={
            "diameter": 60.0,
            "thickness": 10.0,
            "bore": 20.0,
        },
        constraints=[
            "Six 6mm bolt holes on a 44mm pitch circle.",
            "Single solid assigned to result.",
        ],
    )

    print(f"LM Studio: {settings.lmstudio_base_url}")
    print(f"CadQuery model: {provider.model_id}")
    print(f"License note: {settings.cadquery_license_note}")
    print(f"System prompt (first line): {provider.system_prompt.splitlines()[0]}...")
    print(f"Stop token: {provider.stop_token!r}")
    print(f"temperature={settings.cadquery_temperature} max_tokens={settings.cadquery_max_tokens}")

    try:
        if args.no_repair:
            raw = provider.generate_code(spec)
            code_val = validate_cadquery_code(raw)
            if not code_val.ok:
                print("Code validation FAILED:", code_val.errors)
                return 2
            geom = execute_cadquery_in_subprocess(code_val.cleaned_code)
            report = {
                "success": geom.valid and geom.solid_count == 1,
                "code_validation": {"ok": code_val.ok, "errors": code_val.errors},
                "geometry": {
                    "valid": geom.valid,
                    "solid_count": geom.solid_count,
                    "bbox": geom.bbox,
                    "volume": geom.volume,
                    "errors": geom.errors,
                },
            }
        else:
            result = run_cadquery_pipeline(spec, provider=provider)
            report = {
                "success": result.success,
                "repair_attempts": result.repair_attempts,
                "errors": result.errors,
                "geometry": None
                if result.geometry is None
                else {
                    "valid": result.geometry.valid,
                    "solid_count": result.geometry.solid_count,
                    "bbox": result.geometry.bbox,
                    "volume": result.geometry.volume,
                    "errors": result.geometry.errors,
                },
            }
    except LMStudioError as exc:
        print(f"LM Studio error: {exc}")
        return 1

    print(json.dumps(report, indent=2))
    return 0 if report.get("success") else 3


if __name__ == "__main__":
    sys.exit(main())
