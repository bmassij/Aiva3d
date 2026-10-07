"""Lightweight NL heuristics for handle_test parameters (no LLM)."""

from __future__ import annotations

import re
from copy import deepcopy

from projects.work.handle_test.parameters import HandleParameters

_THICKER = re.compile(r"\b(thicker|dicker|dikker|groter|bigger|wider)\b", re.I)
_THINNER = re.compile(r"\b(thinner|dunner|smaller|narrower)\b", re.I)
_RADIUS_NUM = re.compile(
    r"(?:radius|core|diameter|dikte|diameter)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:mm)?",
    re.I,
)
_WALL_NUM = re.compile(
    r"(?:wall|shell|layer|foam|vari(?:o)?shore|outer)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:mm)?",
    re.I,
)
_DELTA = 1.0


def apply_instruction(instruction: str, params: HandleParameters) -> tuple[HandleParameters, list[str]]:
    """Return adjusted parameters and human-readable change notes."""
    text = instruction.strip()
    if not text:
        return params, []

    updated = deepcopy(params)
    notes: list[str] = []

    for match in _RADIUS_NUM.finditer(text):
        val = float(match.group(1))
        if "diameter" in match.group(0).lower():
            val = val / 2.0
        updated.core_radius_mm = max(1.0, val)
        notes.append(f"Set core_radius_mm to {updated.core_radius_mm:.2f} from instruction.")

    for match in _WALL_NUM.finditer(text):
        val = float(match.group(1))
        updated.outer_radius_mm = updated.soft_inner_radius_mm + max(0.5, val)
        notes.append(
            f"Set soft wall thickness to {val:.2f} mm (outer_radius_mm={updated.outer_radius_mm:.2f})."
        )

    if _THICKER.search(text) and not notes:
        updated.core_radius_mm = min(40.0, updated.core_radius_mm + _DELTA)
        notes.append(f"Increased core_radius_mm by {_DELTA} mm (thicker grip).")

    if _THINNER.search(text) and not notes:
        updated.core_radius_mm = max(2.0, updated.core_radius_mm - _DELTA)
        notes.append(f"Decreased core_radius_mm by {_DELTA} mm (thinner grip).")

    if not notes:
        notes.append("Recorded instruction; parameters unchanged (no parseable deltas).")

    return updated, notes
