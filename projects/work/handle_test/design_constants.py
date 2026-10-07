"""Authoritative handle design constants (mm). Do not change without documented justification."""



from __future__ import annotations



# KNOWN — physical graph paper

GRID_SQUARE_MM = 10.0



# MEASURED — grid square counts × 10 mm (reference_measurements.json)

GRIP_LENGTH_MM = 130.0

GRIP_OUTER_DIAMETER_MM = 30.0

# INFERRED — mesh sleeve sits mid-span on right D-leg, not at loop bottom (plan photos).
# (plan_height 168.1 − grip 130) / 2
GRIP_ANCHOR_Y_MM = 19.0

HARD_CORE_DIAMETER_MM = 11.1



# ASSUMED — dual-print interface

HARD_SOFT_CLEARANCE_MM = 0.25



# CALCULATED — VariShore material wall (outer radius − inner void radius)

SOFT_INNER_RADIUS_MM = HARD_CORE_DIAMETER_MM / 2.0 + HARD_SOFT_CLEARANCE_MM  # 5.8 mm

SOFT_OUTER_RADIUS_MM = GRIP_OUTER_DIAMETER_MM / 2.0  # 15.0 mm

SOFT_WALL_NOMINAL_MM = SOFT_OUTER_RADIUS_MM - SOFT_INNER_RADIUS_MM  # 9.20 mm

# ASSUMED — clamshell: short bayonet sliders in notches (not a full-length groove)
CLAMSHELL_SPLIT = True
SLIDER_LENGTH_MM = 11.0
SLIDER_WIDTH_MM = 3.4
SLIDER_HEIGHT_MM = 4.2
SLIDER_CLICK_MM = 3.5
SLIDER_CLEARANCE_MM = 0.28
SLIDER_T_STATIONS = (0.30, 0.70)
# Legacy names kept so older imports do not break (unused by the notch slider).
RAIL_HEIGHT_MM = SLIDER_HEIGHT_MM
RAIL_NECK_MM = SLIDER_WIDTH_MM
RAIL_HEAD_MM = SLIDER_WIDTH_MM + 0.8
RAIL_CLEARANCE_MM = SLIDER_CLEARANCE_MM
RAIL_END_INSET_MM = 10.0
LATCH_LENGTH_MM = SLIDER_LENGTH_MM
LATCH_WIDTH_MM = SLIDER_WIDTH_MM
LATCH_HEIGHT_MM = SLIDER_HEIGHT_MM
LATCH_T_ALONG_RAIL = 0.70
ENDSTOP_THICKNESS_MM = 3.2
CLICK_SPHERE_RADIUS_MM = 0.85
CLICK_T_ALONG_RAIL = 0.70
EXPLODE_GAP_Z_MM = 32.0

# ASSUMED — one-way lock (no glue). Once clicked, only a reset pin releases it.
PAWL_LENGTH_MM = 8.0
PAWL_WIDTH_MM = 3.6
PAWL_HEIGHT_MM = 3.8
PAWL_CATCH_MM = 1.8
PAWL_CLEARANCE_MM = 0.30
RESET_PIN_DIAMETER_MM = 2.0

# INFERRED from bare-metal photo: hex is in the loop plane (6 sides visible in XY),
# ~2.2 grid squares across flats. Z-thickness is similar to the rod, slightly thicker.
HUB_ACROSS_FLATS_MM = 22.0
HUB_THICKNESS_MM = 14.0
# ASSUMED stub — shaft continues out of frame on the photo.
SHAFT_SQUARE_MM = 16.0
SHAFT_STUB_MM = 28.0

TOL_LENGTH_MM = 2.5

TOL_DIAMETER_MM = 1.0

TOL_WALL_MM = 0.35

TOL_CAP_NORMAL_DOT = 0.10



__all__ = [

    "GRID_SQUARE_MM",

    "GRIP_LENGTH_MM",

    "GRIP_ANCHOR_Y_MM",

    "GRIP_OUTER_DIAMETER_MM",

    "HARD_CORE_DIAMETER_MM",

    "HARD_SOFT_CLEARANCE_MM",

    "SOFT_INNER_RADIUS_MM",

    "SOFT_OUTER_RADIUS_MM",

    "SOFT_WALL_NOMINAL_MM",
    "CLAMSHELL_SPLIT",
    "SLIDER_LENGTH_MM",
    "SLIDER_WIDTH_MM",
    "SLIDER_HEIGHT_MM",
    "SLIDER_CLICK_MM",
    "SLIDER_CLEARANCE_MM",
    "SLIDER_T_STATIONS",
    "RAIL_HEIGHT_MM",
    "RAIL_NECK_MM",
    "RAIL_HEAD_MM",
    "RAIL_CLEARANCE_MM",
    "RAIL_END_INSET_MM",
    "LATCH_LENGTH_MM",
    "LATCH_WIDTH_MM",
    "LATCH_HEIGHT_MM",
    "LATCH_T_ALONG_RAIL",
    "ENDSTOP_THICKNESS_MM",
    "CLICK_SPHERE_RADIUS_MM",
    "CLICK_T_ALONG_RAIL",
    "EXPLODE_GAP_Z_MM",
    "PAWL_LENGTH_MM",
    "PAWL_WIDTH_MM",
    "PAWL_HEIGHT_MM",
    "PAWL_CATCH_MM",
    "PAWL_CLEARANCE_MM",
    "RESET_PIN_DIAMETER_MM",
    "HUB_ACROSS_FLATS_MM",
    "HUB_THICKNESS_MM",
    "SHAFT_SQUARE_MM",
    "SHAFT_STUB_MM",
    "TOL_LENGTH_MM",

    "TOL_DIAMETER_MM",

    "TOL_WALL_MM",

    "TOL_CAP_NORMAL_DOT",

]


