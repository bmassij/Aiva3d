"""Configurable routing from task type to LM Studio model identifier."""

from __future__ import annotations

from aiva3d.ai.settings import AISettings, load_settings
from aiva3d.ai.types import ModelTask


def model_for_task(task: ModelTask, settings: AISettings | None = None) -> str:
    settings = settings or load_settings()
    mapping = {
        ModelTask.VISION: settings.vision_model,
        ModelTask.CAD_CODE: settings.cadquery_model,
        ModelTask.GENERAL_REASONING: settings.general_reasoning_model,
        ModelTask.GENERAL_CODING: settings.general_coding_model,
    }
    return mapping[task]
