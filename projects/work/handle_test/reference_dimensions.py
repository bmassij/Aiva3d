"""
Photo-supported reference handle dimensions (mm).

Each quantity carries a confidence class: KNOWN, MEASURED, CALCULATED, INFERRED, UNKNOWN.
Reference geometry is for context only — not production manufacturing data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Tuple

from projects.work.handle_test.design_constants import (
    GRID_SQUARE_MM,
    GRIP_LENGTH_MM,
    HARD_CORE_DIAMETER_MM,
)
from projects.work.handle_test.measurements_loader import load_measurements_doc


class Confidence(str, Enum):
    KNOWN = "KNOWN"
    MEASURED = "MEASURED"
    CALCULATED = "CALCULATED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DimensionRecord:
    name: str
    value_mm: float | None
    confidence: Confidence
    source: str
    notes: str = ""


@dataclass
class ReferenceDimensions:
    """Documented reference-handle metrology (not printable grip)."""

    records: List[DimensionRecord] = field(default_factory=list)
    unknown_limitations: List[str] = field(default_factory=list)
    grip_centerline_points_mm: List[Tuple[float, float]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimensions": [
                {
                    "name": r.name,
                    "value_mm": r.value_mm,
                    "confidence": r.confidence.value,
                    "source": r.source,
                    "notes": r.notes,
                }
                for r in self.records
            ],
            "unknown_limitations": list(self.unknown_limitations),
            "grip_centerline_points_mm": [list(p) for p in self.grip_centerline_points_mm],
        }


def load_reference_dimensions(
    grip_centerline: List[Tuple[float, float]] | None = None,
) -> ReferenceDimensions:
    doc = load_measurements_doc()
    grip = doc.get("grip") or {}
    items = {m["name"]: m for m in doc.get("all_measurements") or []}

    loop_h = float(items.get("metal_loop_rope_plan_height_mm", {}).get("value_mm") or 0)
    if loop_h <= 0:
        loop_h = float(items.get("metal_loop_bbox_height_mm", {}).get("value_mm") or 0)
    loop_w = float(items.get("metal_loop_bbox_width_mm", {}).get("value_mm") or 0)

    from projects.work.handle_test.measurements_loader import centerline_for_cad

    cl = list(grip_centerline or centerline_for_cad(doc))

    records = [
        DimensionRecord("grid_square_mm", GRID_SQUARE_MM, Confidence.KNOWN, "physical graph paper"),
        DimensionRecord(
            "metal_rod_diameter_mm",
            HARD_CORE_DIAMETER_MM,
            Confidence.MEASURED,
            "bare-metal photo grid (~1.1 squares × 10 mm)",
        ),
        DimensionRecord(
            "grip_length_on_leg_mm",
            GRIP_LENGTH_MM,
            Confidence.MEASURED,
            "sleeved photo: 11 grid squares × 10 mm",
        ),
        DimensionRecord(
            "metal_loop_plan_height_mm",
            loop_h if loop_h > 0 else None,
            Confidence.MEASURED if loop_h > 0 else Confidence.UNKNOWN,
            "bare-metal dark mask bbox × local grid",
        ),
        DimensionRecord(
            "metal_loop_plan_width_mm",
            loop_w if loop_w > 0 else None,
            Confidence.MEASURED if loop_w > 0 else Confidence.UNKNOWN,
            "bare-metal dark mask bbox × local grid",
        ),
        DimensionRecord(
            "grip_leg_axis_x_mm",
            None,
            Confidence.INFERRED,
            "Photo trace: right D-leg centerline offset outward (not a straight X=0 line)",
        ),
        DimensionRecord(
            "square_bar_cross_section_mm",
            None,
            Confidence.UNKNOWN,
            "photos show rectangular stock at top; depth/thickness not measurable in plan view",
        ),
        DimensionRecord(
            "weld_geometry_mm",
            None,
            Confidence.UNKNOWN,
            "join regions not dimensioned from photos",
        ),
        DimensionRecord(
            "out_of_plane_bend_mm",
            None,
            Confidence.UNKNOWN,
            "only plan-view photographs available",
        ),
    ]

    limitations = [
        "Bottom D-loop curve uses photo `metal_loop` plan parameters (loop ROI, excludes square shaft).",
        "Left-leg length and bottom arc control points are INFERRED from bare-metal mask rows.",
        "Square/rectangular top bar modeled as round tube envelope only where rod path is used.",
        "No back-side or hidden bend geometry is modeled.",
    ]

    return ReferenceDimensions(records=records, unknown_limitations=limitations, grip_centerline_points_mm=cl)
