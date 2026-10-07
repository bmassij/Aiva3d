"""
Grip reconstruction: hard inner core + VariShore-style soft shell.

Centerline follows the photographed mesh sleeve on the right vertical segment of the
D-shaped metal loop (not a generic straight handle).

Path: XY plane — Y along sleeve axis, X outward bow.
Profile: circular sweep in XZ (CadQuery pipe along wire).
Production grips trim end caps perpendicular to the path tangent at start/end.
"""

from __future__ import annotations

import math

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakeHalfSpace
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

from projects.work.handle_test.parameters import HandleParameters, default_parameters


def _centerline_wire(points: list[tuple[float, float]]) -> cq.Workplane:
    if len(points) < 2:
        raise ValueError("centerline requires at least two points")
    if len(points) == 3:
        return cq.Workplane("XY").moveTo(points[0][0], points[0][1]).threePointArc(
            (points[1][0], points[1][1]),
            (points[2][0], points[2][1]),
        )
    if len(points) == 2:
        return cq.Workplane("XY").moveTo(points[0][0], points[0][1]).lineTo(points[1][0], points[1][1])
    return cq.Workplane("XY").polyline(points)


def _path_end_frames(points: list[tuple[float, float]]) -> tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]:
    path = _centerline_wire(points)
    exp = TopExp_Explorer(path.val().wrapped, TopAbs_EDGE)
    edge = TopoDS.Edge_s(exp.Current())
    curve = BRepAdaptor_Curve(edge)
    u0, u1 = curve.FirstParameter(), curve.LastParameter()

    def frame(u: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        pnt = curve.Value(u)
        tan = curve.DN(u, 1)
        tn = math.hypot(tan.X(), tan.Y(), tan.Z())
        if tn <= 0:
            raise ValueError("zero-length path tangent")
        return (
            (float(pnt.X()), float(pnt.Y()), float(pnt.Z())),
            (float(tan.X() / tn), float(tan.Y() / tn), float(tan.Z() / tn)),
        )

    return frame(u0), frame(u1)


def _halfspace_common(
    shape,
    origin: tuple[float, float, float],
    normal: tuple[float, float, float],
    inside_point: tuple[float, float, float],
):
    ox, oy, oz = origin
    nx, ny, nz = normal
    pln = gp_Pln(gp_Pnt(ox, oy, oz), gp_Dir(nx, ny, nz))
    face = BRepBuilderAPI_MakeFace(pln, -500.0, 500.0, -500.0, 500.0).Face()
    ix, iy, iz = inside_point
    half = BRepPrimAPI_MakeHalfSpace(face, gp_Pnt(ix, iy, iz)).Solid()
    return BRepAlgoAPI_Common(shape, half).Shape()


def _trim_caps_perpendicular_to_path(workpiece: cq.Workplane, centerline_points_mm: list[tuple[float, float]]) -> cq.Workplane:
    """Bound solid between planes ⊥ to path tangent at start and end."""
    (p0, t0), (p1, t1) = _path_end_frames(centerline_points_mm)
    shape = workpiece.val().wrapped
    shape = _halfspace_common(
        shape,
        p0,
        t0,
        (p0[0] + t0[0], p0[1] + t0[1], p0[2] + t0[2]),
    )
    shape = _halfspace_common(
        shape,
        p1,
        (-t1[0], -t1[1], -t1[2]),
        (p1[0] - t1[0], p1[1] - t1[1], p1[2] - t1[2]),
    )
    return cq.Workplane().newObject([cq.Shape.cast(shape)])


def _sweep_circular(
    path: cq.Workplane,
    radius: float,
    centerline_points_mm: list[tuple[float, float]] | None = None,
) -> cq.Workplane:
    if radius <= 0:
        raise ValueError("radius must be positive")
    if centerline_points_mm:
        x0, y0 = centerline_points_mm[0]
        local = [(x - x0, y - y0) for x, y in centerline_points_mm]
        path = _centerline_wire(local)
        swept = cq.Workplane("XZ").circle(radius).sweep(path)
        swept = swept.translate((x0, y0, 0))
        return _trim_caps_perpendicular_to_path(swept, centerline_points_mm)
    swept = cq.Workplane("XZ").circle(radius).sweep(path)
    return swept


def build_hard_core(params: HandleParameters | None = None) -> cq.Workplane:
    params = params or default_parameters()
    path = _centerline_wire(params.centerline_points_mm)
    return _sweep_circular(path, params.core_radius_mm, params.centerline_points_mm)


def build_soft_outer_shell(params: HandleParameters | None = None) -> cq.Workplane:
    """Soft shell: outer sleeve OD minus inner void (hard core + clearance)."""
    params = params or default_parameters()
    path = _centerline_wire(params.centerline_points_mm)
    pts = params.centerline_points_mm
    outer = _sweep_circular(path, params.outer_radius_mm, pts)
    inner_void = _sweep_circular(path, params.inner_cut_radius_mm, pts)
    return outer.cut(inner_void)


def build_assembly_compound(params: HandleParameters | None = None) -> cq.Workplane:
    hard = build_hard_core(params)
    soft = build_soft_outer_shell(params)
    compound = cq.Compound.makeCompound([hard.val(), soft.val()])
    return cq.Workplane().newObject([compound])


def build(params: HandleParameters | None = None) -> tuple[cq.Workplane, cq.Workplane]:
    params = params or default_parameters()
    return build_hard_core(params), build_soft_outer_shell(params)


def path_end_tangents_for_validation(centerline_points_mm: list[tuple[float, float]]) -> dict[str, list[float]]:
    (p0, t0), (p1, t1) = _path_end_frames(centerline_points_mm)
    return {"start": list(t0), "end": list(t1), "start_point": list(p0), "end_point": list(p1)}


def sample_path_frame(
    centerline_points_mm: list[tuple[float, float]],
    t: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Frame at normalised path parameter t in [0, 1]."""
    path = _centerline_wire(centerline_points_mm)
    exp = TopExp_Explorer(path.val().wrapped, TopAbs_EDGE)
    edge = TopoDS.Edge_s(exp.Current())
    curve = BRepAdaptor_Curve(edge)
    u0, u1 = curve.FirstParameter(), curve.LastParameter()
    u = u0 + float(t) * (u1 - u0)
    pnt = curve.Value(u)
    tan = curve.DN(u, 1)
    tn = math.hypot(tan.X(), tan.Y(), tan.Z())
    if tn <= 0:
        raise ValueError("zero-length path tangent")
    return (
        (float(pnt.X()), float(pnt.Y()), float(pnt.Z())),
        (float(tan.X() / tn), float(tan.Y() / tn), float(tan.Z() / tn)),
    )
