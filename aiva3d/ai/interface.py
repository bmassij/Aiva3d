"""Public AI orchestration entry points."""

from __future__ import annotations

from aiva3d.ai.cadquery_provider import CadQueryProvider
from aiva3d.ai.geometry_engine import landmarks_to_cad_specification
from aiva3d.ai.pipeline import run_cadquery_pipeline
from aiva3d.ai.router import model_for_task
from aiva3d.ai.settings import AISettings, CADQUERY_SYSTEM_PROMPT, load_settings
from aiva3d.ai.types import (
    CadGenerationResult,
    CadSpecification,
    CodeValidationResult,
    GeometryValidationResult,
    ModelTask,
)
from aiva3d.ai.vision_provider import LMStudioVisionProvider, vision_unavailable_message

__all__ = [
    "AISettings",
    "CADQUERY_SYSTEM_PROMPT",
    "CadGenerationResult",
    "CadQueryProvider",
    "CadSpecification",
    "CodeValidationResult",
    "GeometryValidationResult",
    "LMStudioVisionProvider",
    "ModelTask",
    "landmarks_to_cad_specification",
    "load_settings",
    "model_for_task",
    "run_cadquery_pipeline",
    "vision_unavailable_message",
]
