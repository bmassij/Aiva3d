"""Build CadSpecification for the handle project from UI parameters."""

from __future__ import annotations

from projects.work.handle_test.measurements_loader import authoritative_grip, load_measurements_doc
from projects.work.handle_test.parameters import HandleParameters

from aiva3d.ai.types import CadSpecification


def handle_params_to_cad_spec(params: HandleParameters) -> CadSpecification:
    doc = load_measurements_doc()
    grip = authoritative_grip(doc)
    length_mm = float(grip.get("length_mm") or 130.0)
    od_mm = params.outer_radius_mm * 2.0
    core_mm = params.core_radius_mm * 2.0
    wall_mm = params.soft_wall_thickness_mm

    return CadSpecification(
        description=(
            "Curved handle grip for metal D-loop outer leg: hard inner sleeve on ~{:.1f} mm rod "
            "with {:.2f} mm radial clearance, soft VariShore outer shell {:.1f} mm OD, "
            "~{:.0f} mm arc length along centerline. Rounded end caps. Single valid solid in `result`."
        ).format(core_mm, params.clearance_mm, od_mm, length_mm),
        dimensions={
            "length": length_mm,
            "outer_diameter": od_mm,
            "core_diameter": core_mm,
            "soft_wall": wall_mm,
        },
        constraints=[
            "Follow arc centerline points (not full D-loop metal handle).",
            "Millimeters only.",
            "One solid assigned to variable result.",
            "Do not model the existing metal D-loop — only the printable grip sleeve.",
        ],
        metadata={"centerline_points_mm": params.centerline_points_mm[:8]},
    )
