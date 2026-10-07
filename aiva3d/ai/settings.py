"""Environment-backed configuration for Aiva3D AI providers."""

from __future__ import annotations

import os
from dataclasses import dataclass


CADQUERY_SYSTEM_PROMPT = (
    "You are a CAD design assistant. Given a description of a mechanical part, "
    "respond with a complete CadQuery (Python) script that builds it. Use "
    "millimeters. The script must import cadquery as cq and assign the final "
    "single-solid model to a variable named result. Respond with only the code."
)

DEFAULT_CADQUERY_STOP_TOKEN = ""


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class AISettings:
    lmstudio_base_url: str
    cadquery_model: str
    vision_model: str
    general_reasoning_model: str
    general_coding_model: str
    cadquery_temperature: float
    cadquery_max_tokens: int
    cadquery_stop_token: str
    max_cad_repair_attempts: int
    cadquery_license_note: str
    vision_temperature: float
    vision_max_tokens: int

    @classmethod
    def from_env(cls) -> "AISettings":
        base = os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234").rstrip("/")
        return cls(
            lmstudio_base_url=base,
            cadquery_model=os.environ.get(
                "CADQUERY_MODEL",
                "qwen2.5-coder-7b-cadquery",
            ),
            vision_model=os.environ.get("VISION_MODEL", "qwen3-vl-8b-instruct"),
            general_reasoning_model=os.environ.get(
                "GENERAL_REASONING_MODEL",
                "Qwen3.6-35B-A3B",
            ),
            general_coding_model=os.environ.get(
                "GENERAL_CODING_MODEL",
                "Qwen2.5-Coder-14B-Instruct",
            ),
            cadquery_temperature=_float("CADQUERY_TEMPERATURE", 0.2),
            cadquery_max_tokens=_int("CADQUERY_MAX_TOKENS", 2048),
            cadquery_stop_token=os.environ.get(
                "CADQUERY_STOP_TOKEN",
                DEFAULT_CADQUERY_STOP_TOKEN,
            ),
            max_cad_repair_attempts=_int("MAX_CAD_REPAIR_ATTEMPTS", 3),
            cadquery_license_note=(
                "Qwen2.5-Coder-7B-CadQuery is described as CC-BY-NC-SA-4.0 "
                "(non-commercial). Do not use commercially without permission."
            ),
            vision_temperature=_float("VISION_TEMPERATURE", 0.2),
            vision_max_tokens=_int("VISION_MAX_TOKENS", 4096),
        )


def load_settings() -> AISettings:
    return AISettings.from_env()
