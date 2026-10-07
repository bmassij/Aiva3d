"""

Photographic reference metal handle (OriginalMetalHandle).



Plan-view reconstruction only. Rod OD = measured bare metal (11.1 mm).

Does not include printable HardCore / SoftGrip shells.

"""



from __future__ import annotations



import cadquery as cq



from projects.work.handle_test.design_constants import HARD_CORE_DIAMETER_MM

from projects.work.handle_test.loop_plan import LoopPlan, load_loop_plan

from projects.work.handle_test.measurements_loader import (

    centerline_sleeve_shape_mm,

    load_measurements_doc,

    right_leg_centerline_full_mm,

)

from projects.work.handle_test.model import _sweep_circular
from projects.work.handle_test.parameters import HandleParameters

from projects.work.handle_test.reference_dimensions import (

    Confidence,

    load_reference_dimensions,

)


__all__ = [
    "build_metal_rod_context",
    "build_original_metal_handle",
    "build_reference_compound",
    "reference_metadata",
]


def build_metal_rod_context(params: HandleParameters | None = None) -> cq.Workplane:
    """Bestaande ronde staaf onder de tuinslang (Ø 11,1 mm); zelfde pad als print-greep."""
    from projects.work.handle_test.model import build_hard_core
    from projects.work.handle_test.parameters import default_parameters

    return build_hard_core(params or default_parameters())





def _build_loop_frame(

    plan: LoopPlan,

    leg_pts: list[tuple[float, float]],

    radius: float,

) -> list[cq.Workplane]:

    """Top bar, left leg, bottom arc — connects to right leg at origin / leg bottom."""

    y_top = plan.plan_height_mm

    leg_bottom = leg_pts[0]

    segments: list[cq.Workplane] = []

    if leg_bottom[0] > 0.5:

        segments.append(_segment_sweep((0.0, 0.0), leg_bottom, radius))

    leg_top = leg_pts[-1]

    segments.append(_segment_sweep((leg_top[0], y_top), (plan.top_bar_left_x_mm, y_top), radius))

    segments.append(

        _segment_sweep(

            (plan.top_bar_left_x_mm, y_top),

            (plan.left_leg_bottom_x_mm, plan.left_leg_arc_split_y_mm),

            radius,

        )

    )

    ctrl = plan.bottom_arc_control_local()

    end_local = (-plan.left_leg_bottom_x_mm, -plan.left_leg_arc_split_y_mm)

    arc_local = cq.Workplane("XY").moveTo(0, 0).threePointArc(ctrl, end_local)

    segments.append(

        _sweep_circular(arc_local, radius).translate(

            (plan.left_leg_bottom_x_mm, plan.left_leg_arc_split_y_mm, 0)

        )

    )

    return segments





def _wire_from_points(points: list[tuple[float, float]]) -> cq.Workplane:

    if len(points) < 2:

        raise ValueError("path requires at least two points")

    wp = cq.Workplane("XY").moveTo(points[0][0], points[0][1])

    if len(points) == 3:

        return wp.threePointArc((points[1][0], points[1][1]), (points[2][0], points[2][1]))

    if len(points) >= 5:

        a, b, c = points[0], points[1], points[2]

        d, e = points[3], points[-1]

        w0 = cq.Workplane("XY").moveTo(a[0], a[1]).threePointArc((b[0], b[1]), (c[0], c[1]))

        w1 = cq.Workplane("XY").moveTo(c[0], c[1]).threePointArc((d[0], d[1]), (e[0], e[1]))

        return w0.add(w1)

    return wp.polyline(points[1:])





def _segment_sweep(a: tuple[float, float], b: tuple[float, float], radius: float) -> cq.Workplane:

    """Sweep along segment; translate because CadQuery pipe anchors path at origin."""

    dx = b[0] - a[0]

    dy = b[1] - a[1]

    wire = cq.Workplane("XY").moveTo(0, 0).lineTo(dx, dy)

    return _sweep_circular(wire, radius).translate((a[0], a[1], 0))




def build_original_metal_handle(

    grip_centerline: list[tuple[float, float]] | None = None,

) -> cq.Workplane:

    """

    Reference metal: continuous D-loop rod (fused) from photo loop plan + sleeve leg shape.



    Production grip centerline may include anchor_y; reference leg uses sleeve shape only.

    """

    _ = grip_centerline  # API compatibility; reference uses photo sleeve shape for the right leg

    doc = load_measurements_doc()

    sleeve_pts = centerline_sleeve_shape_mm(doc)

    plan = load_loop_plan(doc)

    leg_pts = right_leg_centerline_full_mm(sleeve_pts, plan.plan_height_mm)

    radius = HARD_CORE_DIAMETER_MM / 2.0

    segments = _build_loop_frame(plan, leg_pts, radius)



    fused = _sweep_circular(_wire_from_points(leg_pts), radius)

    for seg in segments:

        fused = fused.union(seg)

    return fused





def build_reference_compound(

    grip_centerline: list[tuple[float, float]] | None = None,

) -> cq.Workplane:

    """Alias for OriginalMetalHandle reference solid."""

    return build_original_metal_handle(grip_centerline)





def reference_metadata() -> dict:

    dims = load_reference_dimensions()

    return {

        "role": "reference_only",

        "source": "photographic reconstruction",

        "grid_mm": 10.0,

        "confidence_summary": {

            "rod_diameter": Confidence.MEASURED.value,

            "loop_bbox": Confidence.MEASURED.value,

            "loop_path": Confidence.INFERRED.value,

        },

        "dimensions": dims.to_dict(),

    }


