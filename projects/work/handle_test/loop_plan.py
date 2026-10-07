"""Photo-supported D-loop plan parameters (reference metal only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from projects.work.handle_test.measurements_loader import load_measurements_doc


@dataclass(frozen=True)
class LoopPlan:
    """Plan-view rod centerline frame for OriginalMetalHandle (mm, Y up along right leg)."""

    plan_height_mm: float
    top_bar_left_x_mm: float
    left_leg_bottom_x_mm: float
    left_leg_arc_split_y_mm: float
    bottom_arc_mid_x_mm: float
    bottom_arc_mid_y_mm: float
    hub_to_right_outer_mm: float | None = None

    def bottom_arc_control_local(self) -> tuple[float, float]:
        """Control point in arc-local coords (start at left_leg_bottom, end at origin)."""
        ex = -self.left_leg_bottom_x_mm
        ey = -self.left_leg_arc_split_y_mm
        return (self.bottom_arc_mid_x_mm - self.left_leg_bottom_x_mm, self.bottom_arc_mid_y_mm - self.left_leg_arc_split_y_mm)


def _float(doc: dict[str, Any], key: str, default: float) -> float:
    raw = doc.get(key)
    if raw is None:
        return default
    return float(raw)


def load_loop_plan(doc: dict[str, Any] | None = None) -> LoopPlan:
    doc = doc or load_measurements_doc()
    loop = doc.get("metal_loop") or {}
    items = {m["name"]: m for m in doc.get("all_measurements") or []}
    height = _float(loop, "plan_height_mm", 0.0)
    items = {m["name"]: m for m in doc.get("all_measurements") or []}
    rope_h = float(items.get("metal_loop_rope_plan_height_mm", {}).get("value_mm") or 0.0)
    if rope_h > 0:
        height = rope_h
    elif height <= 0:
        height = float(items.get("metal_loop_bbox_height_mm", {}).get("value_mm") or 215.5)

    top_x = _float(loop, "top_bar_left_x_mm", -48.0)
    bot_x = _float(loop, "left_leg_bottom_x_mm", -54.0)
    split_y = _float(loop, "left_leg_arc_split_y_mm", height * 0.335)
    mid_x = _float(loop, "bottom_arc_mid_x_mm", bot_x * 0.42)
    mid_y = _float(loop, "bottom_arc_mid_y_mm", split_y * 0.48)
    hub_span = loop.get("hub_to_right_outer_mm")
    hub_span_f = float(hub_span) if hub_span is not None else None

    return LoopPlan(
        plan_height_mm=height,
        top_bar_left_x_mm=top_x,
        left_leg_bottom_x_mm=bot_x,
        left_leg_arc_split_y_mm=split_y,
        bottom_arc_mid_x_mm=mid_x,
        bottom_arc_mid_y_mm=mid_y,
        hub_to_right_outer_mm=hub_span_f,
    )
