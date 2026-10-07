"""
Cross-section sampling for handle grip symmetry / constancy checks (BREP, not mesh).

Uses world-Y cutting planes (as requested for UI-aligned checks) and optional
path-perpendicular planes at path ends where Y-planes are oblique to the sweep.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

import numpy as np

from projects.work.handle_test.model import _centerline_wire
from projects.work.handle_test.parameters import HandleParameters, default_parameters


@dataclass(frozen=True)
class SectionCircle:
    """Best-fit circle from a section edge polyline (mm)."""

    center_x: float
    center_z: float
    radius_mm: float
    radius_std_mm: float
    edge_points: int


@dataclass(frozen=True)
class StationReport:
    station_y_mm: float
    method: str
    circles: Tuple[SectionCircle, ...]


def _edge_to_circle(edge_shape) -> SectionCircle:
    edge = TopoDS.Edge_s(edge_shape)
    curve = BRepAdaptor_Curve(edge)
    u0, u1 = curve.FirstParameter(), curve.LastParameter()
    n = 48
    pts = []
    for i in range(n):
        u = u0 + (u1 - u0) * i / (n - 1)
        p = curve.Value(u)
        pts.append((p.X(), p.Y(), p.Z()))
    arr = np.array(pts, dtype=float)
    mean = arr.mean(axis=0)
    centered = arr - mean
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    u_axis, v_axis = vh[0], vh[1]
    xy = np.column_stack((centered @ u_axis, centered @ v_axis))
    x, y = xy[:, 0], xy[:, 1]
    a_mat = np.column_stack((x, y, np.ones(n)))
    b_vec = -(x * x + y * y)
    d, e, f = np.linalg.lstsq(a_mat, b_vec, rcond=None)[0]
    cx2, cy2 = -0.5 * d, -0.5 * e
    r_sq = cx2 * cx2 + cy2 * cy2 - f
    r_mean = float(math.sqrt(max(r_sq, 0.0)))
    center3 = mean + cx2 * u_axis + cy2 * v_axis
    radii = np.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
    r_std = float(np.sqrt(np.mean((radii - r_mean) ** 2)))
    return SectionCircle(float(center3[0]), float(center3[2]), r_mean, r_std, n)


def _section_circles_on_plane(shape, plane: gp_Pln) -> List[SectionCircle]:
    sec = BRepAlgoAPI_Section(shape, plane).Shape()
    exp = TopExp_Explorer(sec, TopAbs_EDGE)
    circles: List[SectionCircle] = []
    while exp.More():
        circles.append(_edge_to_circle(exp.Current()))
        exp.Next()
    circles.sort(key=lambda c: c.radius_mm)
    return circles


def section_at_y_mm(shape, y_mm: float) -> StationReport:
    plane = gp_Pln(gp_Pnt(0.0, y_mm, 0.0), gp_Dir(0.0, 1.0, 0.0))
    return StationReport(
        station_y_mm=y_mm,
        method="world_y_plane",
        circles=tuple(_section_circles_on_plane(shape, plane)),
    )


def _path_wire(params: HandleParameters):
    path = _centerline_wire(params.centerline_points_mm)
    exp = TopExp_Explorer(path.val().wrapped, TopAbs_EDGE)
    edge = TopoDS.Edge_s(exp.Current())
    return BRepAdaptor_Curve(edge)


def section_at_path_parameter(shape, params: HandleParameters, t: float) -> StationReport:
    curve = _path_wire(params)
    u0, u1 = curve.FirstParameter(), curve.LastParameter()
    u = u0 + t * (u1 - u0)
    pnt = curve.Value(u)
    tan = curve.DN(u, 1)
    tn = math.hypot(tan.X(), tan.Y(), tan.Z())
    plane = gp_Pln(
        gp_Pnt(pnt.X(), pnt.Y(), pnt.Z()),
        gp_Dir(tan.X() / tn, tan.Y() / tn, tan.Z() / tn),
    )
    return StationReport(
        station_y_mm=float(pnt.Y()),
        method="path_perpendicular",
        circles=tuple(_section_circles_on_plane(shape, plane)),
    )


def sample_grip_stations_for_solids(
    hard_shape,
    soft_shape,
    params: HandleParameters | None = None,
    y_values_mm: Sequence[float] = (0.0, 27.5, 55.0, 82.5, 110.0),
) -> dict[str, List[StationReport]]:
    params = params or default_parameters()
    length = max(p[1] for p in params.centerline_points_mm)
    hard_reports: List[StationReport] = []
    soft_reports: List[StationReport] = []
    for y in y_values_mm:
        if y <= 0.5:
            t_near_start = 0.04
            hard_reports.append(
                _nominal_station(section_at_path_parameter(hard_shape, params, t_near_start), y)
            )
            soft_reports.append(
                _nominal_station(section_at_path_parameter(soft_shape, params, t_near_start), y)
            )
        elif y >= length - 0.5:
            # End caps are oblique to world Y; sample just inside the cap (t≈0.96).
            t_near_end = 0.96
            hard_reports.append(
                _nominal_station(section_at_path_parameter(hard_shape, params, t_near_end), y)
            )
            soft_reports.append(
                _nominal_station(section_at_path_parameter(soft_shape, params, t_near_end), y)
            )
        else:
            hard_reports.append(section_at_y_mm(hard_shape, y))
            soft_reports.append(section_at_y_mm(soft_shape, y))
    return {"hard": hard_reports, "soft": soft_reports}


def pick_radius(
    circles: Sequence[SectionCircle],
    target: float,
    max_circularity_std: float = 0.15,
) -> SectionCircle | None:
    if not circles:
        return None
    well_formed = [c for c in circles if c.radius_std_mm <= max_circularity_std]
    pool = well_formed if well_formed else list(circles)
    return min(pool, key=lambda c: abs(c.radius_mm - target))


def pick_annulus(
    circles: Sequence[SectionCircle],
    max_circularity_std: float = 0.28,
) -> Tuple[SectionCircle | None, SectionCircle | None]:
    """Inner and outer rings from a soft-shell section (sorted by radius)."""
    if not circles:
        return None, None
    pool = [c for c in circles if c.radius_std_mm <= max_circularity_std]
    if len(pool) < 2:
        pool = sorted(circles, key=lambda c: c.radius_mm)
    else:
        pool = sorted(pool, key=lambda c: c.radius_mm)
    if len(pool) == 1:
        return pool[0], None
    return pool[0], pool[-1]


def _nominal_station(report: StationReport, nominal_y_mm: float) -> StationReport:
    return StationReport(
        station_y_mm=nominal_y_mm,
        method=report.method,
        circles=report.circles,
    )
