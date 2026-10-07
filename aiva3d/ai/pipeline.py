"""End-to-end CadQuery generation with validation and bounded repair loop."""

from __future__ import annotations

from aiva3d.ai.cadquery_provider import CadQueryProvider
from aiva3d.ai.code_validator import validate_cadquery_code
from aiva3d.ai.geometry_validator import validate_geometry_against_spec
from aiva3d.ai.lmstudio_client import LMStudioError
from aiva3d.ai.sandbox_runner import execute_cadquery_in_subprocess
from aiva3d.ai.types import CadGenerationResult, CadSpecification


def run_cadquery_pipeline(
    spec: CadSpecification,
    provider: CadQueryProvider | None = None,
    *,
    max_attempts: int | None = None,
) -> CadGenerationResult:
    """
    LLM → static validation → subprocess execution → geometry validation → optional repair.
    """
    provider = provider or CadQueryProvider.from_env()
    attempts_limit = max_attempts if max_attempts is not None else provider.settings.max_cad_repair_attempts
    repair_hint = ""
    last_code = ""
    last_errors: list[str] = []

    for attempt in range(1, attempts_limit + 1):
        try:
            raw = provider.generate_code(spec, extra_user_hint=repair_hint)
        except LMStudioError as exc:
            return CadGenerationResult(
                success=False,
                repair_attempts=attempt - 1,
                model_id=provider.model_id,
                errors=[str(exc)],
            )

        code_val = validate_cadquery_code(raw)
        if not code_val.ok:
            last_errors = code_val.errors
            last_code = code_val.cleaned_code
            repair_hint = _repair_message(code_val.errors, stage="code")
            continue

        metrics = execute_cadquery_in_subprocess(code_val.cleaned_code)
        geom = validate_geometry_against_spec(metrics, spec)
        if geom.valid:
            return CadGenerationResult(
                success=True,
                code=code_val.cleaned_code,
                code_validation=code_val,
                geometry=geom,
                repair_attempts=attempt - 1,
                model_id=provider.model_id,
            )

        last_errors = geom.errors
        last_code = code_val.cleaned_code
        repair_hint = _repair_message(geom.errors, stage="geometry")

    return CadGenerationResult(
        success=False,
        code=last_code,
        repair_attempts=attempts_limit,
        model_id=provider.model_id,
        errors=last_errors or ["CadQuery pipeline failed without specific errors."],
    )


def _repair_message(errors: list[str], *, stage: str) -> str:
    joined = "; ".join(errors[:8])
    return (
        f"Previous attempt failed {stage} validation: {joined}. "
        "Fix the CadQuery script. Keep `import cadquery as cq` and assign one solid to `result`."
    )
