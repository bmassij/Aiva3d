"""Structured design record for NL instructions and provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DesignRecord:
    """Internal representation of a CAD session (not a substitute for parameters.py)."""

    original_instruction: str = ""
    reference_data: List[str] = field(default_factory=list)
    measured_data: Dict[str, str] = field(default_factory=dict)
    assumed_data: Dict[str, str] = field(default_factory=dict)
    calculated_data: Dict[str, str] = field(default_factory=dict)
    design_requirements: List[str] = field(default_factory=list)
    change_log: List[str] = field(default_factory=list)
    updated_at: str = ""

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_instruction": self.original_instruction,
            "reference_data": list(self.reference_data),
            "measured_data": dict(self.measured_data),
            "assumed_data": dict(self.assumed_data),
            "calculated_data": dict(self.calculated_data),
            "design_requirements": list(self.design_requirements),
            "change_log": list(self.change_log),
            "updated_at": self.updated_at,
        }


HANDLE_CUSTOMER_TEXT = (
    "Maar ze motte zo diek waere wie un handvat. Wuurt in hard en zacht geprint dus "
    "binnen en boete kant van de greep. Met varioshore. Schuim en neet schuim zekmaar. "
    "Kiek ff wat de richtlijnen zien veur un handvat rechttoe rechtaan. values zijn 1 bij 1 cm"
)


def design_record_from_handle_customer_text(text: str | None = None) -> DesignRecord:
    """Seed a design record from the handle_test customer description (no invented measurements)."""
    source = (text or HANDLE_CUSTOMER_TEXT).strip()
    rec = DesignRecord(original_instruction=source)
    rec.reference_data = [
        "Photographs of existing handle/grip with 1 cm graph paper grid (upload to reference/).",
        "Grid scale: 1 square = 10 mm.",
    ]
    rec.measured_data = {
        "note": "No photo-based dimensions committed until reference images are measured in the UI.",
    }
    rec.assumed_data = {
        "centerline_points_mm": "Placeholder spline until traced from photos (low confidence).",
        "core_radius_mm": "Ergonomic hard-core radius — tune against photos (low confidence).",
        "soft_wall_thickness_mm": "VariShore material wall (outer_radius − soft_inner_radius).",
    }
    rec.calculated_data = {
        "outer_radius_mm": "authoritative grip OD / 2 (30 mm → 15 mm)",
    }
    rec.design_requirements = [
        "Grip thickness similar to existing handvat (from photos when available).",
        "Dual-material: hard inner core + soft outer VariShore/foam shell.",
        "Do not remodel full metal assembly — grip/handle only.",
        "Straightforward handle geometry; follow visible grip shape via centerline.",
        "Units: millimeters internally; graph paper 1 cm = 10 mm.",
    ]
    rec.touch()
    return rec
