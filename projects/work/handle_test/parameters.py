"""
Parametric handle/grip — all dimensions in millimeters.

Provenance and confidence are explicit. Update centerline points from graph-paper photos
(1 square = 10 mm). Do not treat ASSUMED values as measured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from cad.utilities.parameters import DataProvenance, Dimension

# --- Centerline in XZ plane (mm): (x, z) along grip length ---
# ASSUMED placeholder until traced from reference photos.
CENTERLINE_POINTS_MM: List[Tuple[float, float]] = [
    (0.0, 0.0),
    (45.0, 6.0),
    (90.0, 14.0),
    (135.0, 10.0),
    (180.0, 0.0),
]

DIMENSIONS = {
    "grip_length_mm": Dimension(
        "grip_length_mm",
        180.0,
        provenance=DataProvenance.ASSUMED,
        notes="End-to-end along X from placeholder centerline; remeasure from photos.",
    ),
    "core_radius_mm": Dimension(
        "core_radius_mm",
        11.0,
        provenance=DataProvenance.ASSUMED,
        notes="Hard inner grip radius; tune to photo cross-section.",
    ),
    "outer_layer_thickness_mm": Dimension(
        "outer_layer_thickness_mm",
        4.0,
        provenance=DataProvenance.ASSUMED,
        notes="VariShore / foam shell wall thickness.",
    ),
    "bend_radius_mm": Dimension(
        "bend_radius_mm",
        25.0,
        provenance=DataProvenance.ASSUMED,
        notes="Approximate spline bend; derived visually when photos available.",
    ),
    "clearance_mm": Dimension(
        "clearance_mm",
        0.2,
        provenance=DataProvenance.CALCULATED,
        notes="Interface clearance between hard and soft (print).",
    ),
}


@dataclass
class HandleParameters:
    centerline_points_mm: List[Tuple[float, float]] = field(default_factory=lambda: list(CENTERLINE_POINTS_MM))
    core_radius_mm: float = 11.0
    outer_layer_thickness_mm: float = 4.0
    clearance_mm: float = 0.2

    @property
    def outer_radius_mm(self) -> float:
        return self.core_radius_mm + self.outer_layer_thickness_mm

    @property
    def inner_cut_radius_mm(self) -> float:
        return self.core_radius_mm + self.clearance_mm

    def summary(self) -> dict:
        return {
            "centerline_points_mm": self.centerline_points_mm,
            "core_radius_mm": self.core_radius_mm,
            "outer_layer_thickness_mm": self.outer_layer_thickness_mm,
            "outer_radius_mm": self.outer_radius_mm,
            "clearance_mm": self.clearance_mm,
        }


def default_parameters() -> HandleParameters:
    return HandleParameters(
        centerline_points_mm=list(CENTERLINE_POINTS_MM),
        core_radius_mm=float(DIMENSIONS["core_radius_mm"].value),
        outer_layer_thickness_mm=float(DIMENSIONS["outer_layer_thickness_mm"].value),
        clearance_mm=float(DIMENSIONS["clearance_mm"].value),
    )
