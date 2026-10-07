"""Estimated print time (not slicer-exact)."""

from __future__ import annotations

import math

from quote_api.schemas import MachineProfile


def estimate_print_time_minutes(
    *,
    volume_mm3: float,
    object_count: int,
    machine: MachineProfile,
    layer_height_mm: float | None = None,
    infill: float | None = None,
) -> float:
    """
    Heuristic ESTIMATE from bounding volume, infill, and nominal speed.

    Phase 2 may replace this with Orca/Bambu slicer output.
    """
    if volume_mm3 <= 0:
        return 0.0
    lh = layer_height_mm if layer_height_mm is not None else machine.default_layer_height_mm
    inf = infill if infill is not None else machine.default_infill
    inf = max(0.05, min(inf, 1.0))
    # Effective material factor: shell + infill fraction
    effective_factor = 0.35 + 0.65 * inf
    effective_volume_mm3 = volume_mm3 * effective_factor
    # Approximate equivalent length of extrusion at 0.4 mm line
    line_area_mm2 = 0.4 * lh
    extrusion_length_mm = effective_volume_mm3 / max(line_area_mm2, 0.01)
    speed = max(machine.default_print_speed_mm_s, 1.0)
    travel_overhead = 1.0 + 0.08 * max(object_count - 1, 0)
    seconds = (extrusion_length_mm / speed) * travel_overhead
    # Layer change overhead
    layer_penalty = math.sqrt(volume_mm3) / max(lh, 0.05) * 0.15
    seconds += layer_penalty
    return max(seconds / 60.0, 1.0)
