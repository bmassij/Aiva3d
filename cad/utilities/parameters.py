"""Parametric metadata and provenance for dimensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class DataProvenance(str, Enum):
    """How a numeric value was obtained."""

    MEASURED = "measured"
    ASSUMED = "assumed"
    CALCULATED = "calculated"


@dataclass
class Dimension:
    """A named value with units and explicit provenance."""

    name: str
    value: float
    unit: str = "mm"
    provenance: DataProvenance = DataProvenance.ASSUMED
    notes: str = ""

    def as_mm(self) -> float:
        if self.unit != "mm":
            raise ValueError(f"Dimension {self.name}: unit conversion from {self.unit} not implemented")
        return float(self.value)


@dataclass
class ParametricModelMeta:
    """Metadata attached to a parametric model for documentation and future AI layers."""

    name: str
    description: str = ""
    dimensions: Dict[str, Dimension] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dimensions": {
                k: {
                    "value": d.value,
                    "unit": d.unit,
                    "provenance": d.provenance.value,
                    "notes": d.notes,
                }
                for k, d in self.dimensions.items()
            },
            "assumptions": list(self.assumptions),
        }
