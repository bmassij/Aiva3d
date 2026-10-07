"""Ergonomic design check (guidance only — does not override photo measurements)."""

from __future__ import annotations

from dataclasses import dataclass

from projects.work.handle_test.design_constants import GRIP_OUTER_DIAMETER_MM


@dataclass
class ErgonomicAssessment:
    measured_od_mm: float
    ergonomic_range_mm: str
    status: str
    summary: str
    optional_variant_note: str
    references_note: str


def assess_grip_od(measured_od_mm: float = GRIP_OUTER_DIAMETER_MM) -> ErgonomicAssessment:
    """Compare measured OD to common cylindrical grip guidance (~30–45 mm, ~35 mm often cited)."""
    lo, hi = 30.0, 45.0
    if measured_od_mm < lo:
        status = "below_common_range"
        summary = (
            f"Measured {measured_od_mm:.1f} mm OD is below the commonly cited {lo:.0f}–{hi:.0f} mm range "
            "for cylindrical power grips, but matches the photographed sleeve (authoritative)."
        )
    elif measured_od_mm <= hi:
        status = "within_or_near_range"
        summary = (
            f"Measured {measured_od_mm:.1f} mm OD lies within or near the lower portion of the "
            f"{lo:.0f}–{hi:.0f} mm ergonomic band cited for cylindrical tool handles."
        )
    else:
        status = "above_common_range"
        summary = f"Measured {measured_od_mm:.1f} mm OD exceeds typical upper guidance ({hi:.0f} mm)."

    return ErgonomicAssessment(
        measured_od_mm=measured_od_mm,
        ergonomic_range_mm=f"{lo:.0f}–{hi:.0f} mm (cylindrical / power-grip guidance)",
        status=status,
        summary=summary,
        optional_variant_note=(
            "Optional ergonomic variant (not applied): outer OD ~35 mm could be evaluated for larger hands "
            "or higher grip force — only as a separate design branch, not replacing photo reconstruction."
        ),
        references_note=(
            "General guidance: ISO 11228 / tool-handle literature and grip studies often cite ~30–45 mm "
            "cylindrical handles; ~35 mm reported comfortable in some maximum-grip tests. Hand size, task, "
            "and compressible outer layer strongly affect perceived comfort."
        ),
    )
