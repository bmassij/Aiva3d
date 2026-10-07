"""
Printable D-loop copied from the bare-metal photo.

Rod centerline is MEASURED from the photo inner oval (1 grid square = 10 mm = 1 cm).
Hex is INFERRED in the loop plane (~2.2 squares across flats). Square shaft stub is ASSUMED.

The metal loop is one solid (no click). Click/slider lives only on the grip
clamshell that wraps the right leg.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from cad.utilities.validation import assert_valid_solid, solid_volume
from projects.work.handle_test.design_constants import (
    HARD_CORE_DIAMETER_MM,
    HUB_ACROSS_FLATS_MM,
    HUB_THICKNESS_MM,
    SHAFT_SQUARE_MM,
    SHAFT_STUB_MM,
)

BARE_METAL_PHOTO = (
    Path(__file__).resolve().parent / "reference" / "WhatsApp Image 2026-10-02 at 20.16.42.jpeg"
)


@dataclass(frozen=True)
class LoopEllipse:
    """Bounding ellipse of the photo-traced centerline (right X=0, bottom Y=0)."""

    a_mm: float
    b_mm: float
    cx_mm: float
    cy_mm: float
    rod_radius_mm: float

    @property
    def left_xy(self) -> tuple[float, float]:
        return (self.cx_mm - self.a_mm, self.cy_mm)

    @property
    def right_xy(self) -> tuple[float, float]:
        return (self.cx_mm + self.a_mm, self.cy_mm)


def photo_centerline_xy() -> list[tuple[float, float]]:
    """MEASURED oval centerline from the bare-metal photo (1 square = 10 mm)."""
    import cv2

    from projects.work.handle_test.grid_measure import extract_loop_centerline_xy_mm

    rgb = cv2.cvtColor(cv2.imread(str(BARE_METAL_PHOTO)), cv2.COLOR_BGR2RGB)
    trace = extract_loop_centerline_xy_mm(rgb, rod_diameter_mm=HARD_CORE_DIAMETER_MM)
    return [(float(p[0]), float(p[1])) for p in trace["centerline_xy_mm"]]


def loop_ellipse_from_photos() -> LoopEllipse:
    """Bounding ellipse of the photo centerline (for locks / bbox checks)."""
    pts = photo_centerline_xy()
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    return LoopEllipse(
        a_mm=0.5 * (xmax - xmin),
        b_mm=0.5 * (ymax - ymin),
        cx_mm=0.5 * (xmax + xmin),
        cy_mm=0.5 * (ymax + ymin),
        rod_radius_mm=HARD_CORE_DIAMETER_MM / 2.0,
    )


def _ellipse_polyline(ell: LoopEllipse, n: int = 48) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(n):
        t = -math.pi / 2.0 + 2.0 * math.pi * i / n
        pts.append((ell.cx_mm + ell.a_mm * math.cos(t), ell.cy_mm + ell.b_mm * math.sin(t)))
    return pts


def _sweep_along_xy(pts: list[tuple[float, float]], radius_mm: float) -> cq.Workplane:
    x0, y0 = pts[0]
    local = [(x - x0, y - y0) for x, y in pts]
    path = cq.Workplane("XY").spline(local, periodic=True)
    return cq.Workplane("XZ").circle(radius_mm).sweep(path, isFrenet=True).translate((x0, y0, 0.0))


def build_loop_rod(ell: LoopEllipse | None = None) -> cq.Workplane:
    """One sweep along the photo-traced oval (bowed sides, not a stadium)."""
    del ell
    pts = photo_centerline_xy()
    rod = _sweep_along_xy(pts, HARD_CORE_DIAMETER_MM / 2.0)
    assert_valid_solid(rod, "photo_loop_rod")
    return rod


def build_hex_hub(ell: LoopEllipse | None = None) -> cq.Workplane:
    """Hex in the loop plane (XY), sitting on the left of the oval like the photo."""
    ell = ell or loop_ellipse_from_photos()
    lx, ly = ell.left_xy
    af = HUB_ACROSS_FLATS_MM
    vertex_d = 2.0 * af / math.sqrt(3.0)
    return (
        cq.Workplane("XY")
        .center(lx, ly)
        .polygon(6, vertex_d)
        .extrude(HUB_THICKNESS_MM / 2.0, both=True)
    )


def build_shaft_stub(ell: LoopEllipse | None = None) -> cq.Workplane:
    """ASSUMED square bar stub leaving the hex to the left."""
    ell = ell or loop_ellipse_from_photos()
    lx, ly = ell.left_xy
    s = SHAFT_SQUARE_MM
    stub = SHAFT_STUB_MM
    left_face = lx - HUB_ACROSS_FLATS_MM / 2.0
    return cq.Workplane("XY").box(stub + 4.0, s, s, centered=(False, True, True)).translate(
        (left_face - stub + 4.0, ly, 0.0)
    )


def build_printable_metal_handle() -> cq.Workplane:
    """Photo oval rod + XY hex + shaft, one solid."""
    ell = loop_ellipse_from_photos()
    fused = build_loop_rod(ell).union(build_hex_hub(ell)).union(build_shaft_stub(ell))
    solid = fused.combine().solids()
    assert_valid_solid(solid, "printable_metal_handle")
    return solid


def validate_full_handle(metal: cq.Workplane | None = None) -> dict:
    solid = metal or build_printable_metal_handle()
    vol = solid_volume(solid)
    ell = loop_ellipse_from_photos()
    return {
        "volumes_mm3": {"metal_loop": vol},
        "all_checks_pass": vol > 10000.0,
        "assembly": (
            "Metal D-loop is one solid (no click). The click/slider is only on the "
            "printed grip clamshell around the right leg."
        ),
        "ellipse": {"a_mm": ell.a_mm, "b_mm": ell.b_mm},
        "shape": "photo-traced oval (not stadium)",
    }


def exploded_full_handle(gap_z_mm: float | None = None) -> dict:
    del gap_z_mm
    metal = build_printable_metal_handle()
    return {
        "parts": metal,
        "workpieces": [
            (metal, "#718096", "D-lus kaal metaal (geen klik)", 1.0),
        ],
        "gap_z_mm": 0.0,
    }
