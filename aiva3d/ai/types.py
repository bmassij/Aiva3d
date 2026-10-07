"""Shared types for the multi-model CAD pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ModelTask(str, Enum):
    """Which local model to use for a task."""

    VISION = "vision"
    CAD_CODE = "cad_code"
    GENERAL_REASONING = "general_reasoning"
    GENERAL_CODING = "general_coding"


@dataclass
class CadSpecification:
    """Structured geometry intent for the CadQuery code model (not vision)."""

    description: str
    units: str = "mm"
    constraints: List[str] = field(default_factory=list)
    dimensions: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_text(self) -> str:
        lines = [self.description.strip(), f"Units: {self.units}."]
        if self.dimensions:
            lines.append("Dimensions (mm unless noted):")
            for key, val in sorted(self.dimensions.items()):
                lines.append(f"- {key}: {val}")
        if self.constraints:
            lines.append("Constraints:")
            for c in self.constraints:
                lines.append(f"- {c}")
        lines.append(
            "The final result must be one valid solid assigned to variable `result`."
        )
        return "\n".join(lines)


@dataclass
class CodeValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cleaned_code: str = ""


@dataclass
class GeometryValidationResult:
    valid: bool
    solid_count: int = 0
    bbox: Dict[str, float] = field(default_factory=dict)
    volume: Optional[float] = None
    center_of_mass: Optional[Dict[str, float]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class CadGenerationResult:
    success: bool
    code: str = ""
    code_validation: Optional[CodeValidationResult] = None
    geometry: Optional[GeometryValidationResult] = None
    repair_attempts: int = 0
    model_id: str = ""
    errors: List[str] = field(default_factory=list)
