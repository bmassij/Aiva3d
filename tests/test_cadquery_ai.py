"""Tests for CadQuery LM Studio provider, validation, and pipeline (no LM Studio required)."""

from __future__ import annotations

import pytest

from aiva3d.ai.cadquery_provider import CadQueryProvider, mock_chat_response
from aiva3d.ai.code_validator import validate_cadquery_code
from aiva3d.ai.geometry_engine import centerline_pixels_to_mm, landmarks_to_cad_specification
from aiva3d.ai.geometry_validator import validate_geometry_against_spec
from aiva3d.ai.lmstudio_client import LMStudioError
from aiva3d.ai.pipeline import run_cadquery_pipeline
from aiva3d.ai.router import model_for_task
from aiva3d.ai.sandbox_runner import execute_cadquery_in_subprocess
from aiva3d.ai.settings import CADQUERY_SYSTEM_PROMPT, AISettings
from aiva3d.ai.types import CadSpecification, GeometryValidationResult, ModelTask
from aiva3d.ai.vision_provider import LMStudioVisionProvider, vision_unavailable_message


VALID_BOX = """
import cadquery as cq
result = cq.Workplane("XY").box(10, 20, 30)
"""

DANGEROUS = """
import cadquery as cq
import os
os.system("echo pwned")
result = cq.Workplane("XY").box(1,1,1)
"""

NO_RESULT = """
import cadquery as cq
part = cq.Workplane("XY").box(1,1,1)
"""


@pytest.fixture
def ai_settings(monkeypatch: pytest.MonkeyPatch) -> AISettings:
    monkeypatch.setenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")
    monkeypatch.setenv("CADQUERY_MODEL", "test-cadquery-model")
    monkeypatch.setenv("CADQUERY_TEMPERATURE", "0.15")
    monkeypatch.setenv("CADQUERY_MAX_TOKENS", "512")
    monkeypatch.setenv("CADQUERY_STOP_TOKEN", "")
    monkeypatch.setenv("MAX_CAD_REPAIR_ATTEMPTS", "3")
    return AISettings.from_env()


def test_provider_initializes(ai_settings: AISettings) -> None:
    provider = CadQueryProvider(settings=ai_settings, chat_fn=mock_chat_response("x"))
    assert provider.model_id == "test-cadquery-model"


def test_system_prompt_exact() -> None:
    assert "import cadquery as cq" in CADQUERY_SYSTEM_PROMPT
    assert "variable named result" in CADQUERY_SYSTEM_PROMPT


def test_stop_token_configurable(ai_settings: AISettings) -> None:
    provider = CadQueryProvider(settings=ai_settings, chat_fn=mock_chat_response(""))
    assert provider.stop_token == ""


def test_temperature_and_max_tokens(ai_settings: AISettings) -> None:
    assert ai_settings.cadquery_temperature == pytest.approx(0.15)
    assert ai_settings.cadquery_max_tokens == 512


def test_model_routing(ai_settings: AISettings) -> None:
    assert model_for_task(ModelTask.CAD_CODE, ai_settings) == "test-cadquery-model"
    assert model_for_task(ModelTask.VISION, ai_settings) == ai_settings.vision_model


def test_generated_code_parsed_from_markdown() -> None:
    wrapped = "```python\n" + VALID_BOX + "\n```"
    result = validate_cadquery_code(wrapped)
    assert result.ok
    assert "import cadquery" in result.cleaned_code


def test_dangerous_code_rejected() -> None:
    result = validate_cadquery_code(DANGEROUS)
    assert not result.ok
    assert any("Forbidden" in e for e in result.errors)


def test_missing_result_rejected() -> None:
    result = validate_cadquery_code(NO_RESULT)
    assert not result.ok


def test_valid_cadquery_executes_in_subprocess() -> None:
    code_val = validate_cadquery_code(VALID_BOX)
    assert code_val.ok
    geom = execute_cadquery_in_subprocess(code_val.cleaned_code, timeout_s=120.0)
    assert geom.valid
    assert geom.solid_count == 1
    assert geom.volume and geom.volume > 0


def test_bbox_and_volume_present() -> None:
    geom = execute_cadquery_in_subprocess(VALID_BOX.strip())
    assert geom.bbox.get("x") == pytest.approx(10.0, abs=0.5)
    assert geom.bbox.get("y") == pytest.approx(20.0, abs=0.5)
    assert geom.bbox.get("z") == pytest.approx(30.0, abs=0.5)


def test_multiple_solids_detected() -> None:
    metrics = GeometryValidationResult(valid=True, solid_count=2, bbox={"x": 10, "y": 10, "z": 10})
    spec = CadSpecification(description="test")
    out = validate_geometry_against_spec(metrics, spec, require_single_solid=True)
    assert not out.valid
    assert any("one solid" in e for e in out.errors)


def test_invalid_geometry_spec_mismatch() -> None:
    metrics = GeometryValidationResult(
        valid=True,
        solid_count=1,
        bbox={"x": 50.0, "y": 10.0, "z": 10.0},
        volume=1000.0,
    )
    spec = CadSpecification(description="flange", dimensions={"diameter": 60.0})
    out = validate_geometry_against_spec(metrics, spec, bbox_tolerance_mm=2.0)
    assert not out.valid


def test_repair_loop_limited(ai_settings: AISettings) -> None:
    calls = {"n": 0}

    def flaky_chat(**kwargs):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        if calls["n"] < 3:
            return DANGEROUS
        return VALID_BOX

    provider = CadQueryProvider(settings=ai_settings, chat_fn=flaky_chat)
    result = run_cadquery_pipeline(
        CadSpecification(description="box"),
        provider=provider,
        max_attempts=3,
    )
    assert result.success
    assert result.repair_attempts == 2


def test_repair_loop_stops_at_max(ai_settings: AISettings) -> None:
    provider = CadQueryProvider(settings=ai_settings, chat_fn=mock_chat_response(DANGEROUS))
    result = run_cadquery_pipeline(
        CadSpecification(description="bad"),
        provider=provider,
        max_attempts=2,
    )
    assert not result.success
    assert result.repair_attempts == 2


def test_lm_studio_unavailable_clear_error(ai_settings: AISettings) -> None:
    def fail_chat(**kwargs):  # type: ignore[no-untyped-def]
        raise LMStudioError("offline")

    provider = CadQueryProvider(settings=ai_settings, chat_fn=fail_chat)
    result = run_cadquery_pipeline(CadSpecification(description="x"), provider=provider, max_attempts=1)
    assert not result.success
    assert "offline" in result.errors[0]


def test_mock_provider_without_lm_studio(ai_settings: AISettings) -> None:
    provider = CadQueryProvider(settings=ai_settings, chat_fn=mock_chat_response(VALID_BOX))
    text = provider.generate_code(CadSpecification(description="box"))
    assert "cadquery" in text


def test_geometry_engine_landmarks(ai_settings: AISettings) -> None:
    spec = landmarks_to_cad_specification(
        {"grip_length_mm": 130.0, "source": "measurements"},
        part_description="Curved sleeve",
    )
    assert "130" in spec.to_prompt_text()
    assert spec.dimensions["grip_length"] == 130.0


def test_centerline_pixel_conversion() -> None:
    pts = centerline_pixels_to_mm([(100, 200)], origin_px=(100, 200), mm_per_px_x=0.1, mm_per_px_y=0.1)
    assert pts == [(0.0, 0.0)]


def test_vision_separate_from_cadquery() -> None:
    assert "Do not send photos" in vision_unavailable_message()
    provider = LMStudioVisionProvider.from_env(
        vision_fn=lambda **kwargs: "mock analysis"
    )
    out = provider.analyze_image(image_path=__file__, prompt="grid")
    assert out["analysis"] == "mock analysis"


def test_license_note_present(ai_settings: AISettings) -> None:
    assert "NC" in ai_settings.cadquery_license_note.upper()


def test_env_model_not_hardcoded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CADQUERY_MODEL", "custom-id-xyz")
    settings = AISettings.from_env()
    assert settings.cadquery_model == "custom-id-xyz"
