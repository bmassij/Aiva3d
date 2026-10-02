"""Parametric dual-material handle: hard core + soft outer shell along a spline path."""

from __future__ import annotations

import cadquery as cq

from projects.work.handle_test.parameters import HandleParameters, default_parameters


def _centerline_wire(points: list[tuple[float, float]]) -> cq.Workplane:
    if len(points) < 2:
        raise ValueError("centerline requires at least two points")
    wp = cq.Workplane("XZ").moveTo(points[0][0], points[0][1])
    if len(points) == 2:
        wp = wp.lineTo(points[1][0], points[1][1])
    else:
        wp = wp.spline(points[1:])
    return wp


def _sweep_radius(path: cq.Workplane, radius: float) -> cq.Workplane:
    if radius <= 0:
        raise ValueError("radius must be positive")
    return cq.Workplane("YZ").circle(radius).sweep(path)


def build_hard_core(params: HandleParameters | None = None) -> cq.Workplane:
    params = params or default_parameters()
    path = _centerline_wire(params.centerline_points_mm)
    return _sweep_radius(path, params.core_radius_mm)


def build_soft_outer_shell(params: HandleParameters | None = None) -> cq.Workplane:
    """Foam/VariShore shell: outer sweep minus inner void (hard core + clearance)."""
    params = params or default_parameters()
    path = _centerline_wire(params.centerline_points_mm)
    outer = _sweep_radius(path, params.outer_radius_mm)
    inner_void = _sweep_radius(path, params.inner_cut_radius_mm)
    return outer.cut(inner_void)


def build(params: HandleParameters | None = None) -> tuple[cq.Workplane, cq.Workplane]:
    params = params or default_parameters()
    return build_hard_core(params), build_soft_outer_shell(params)
