"""
Verification test model: parametric mounting plate with holes, boss, and pocket cut.

Run from project root:
  .venv\\Scripts\\python projects\\examples\\test_mounting_plate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cadquery as cq

from cad.primitives.common import mounting_holes, rounded_box
from cad.utilities.parameters import DataProvenance, Dimension, ParametricModelMeta
from cad.utilities.validation import assert_valid_solid, solid_volume
from exporters.pipeline import export_all
from preview.viewer import preview_matplotlib

# --- Parametric dimensions (mm) ---
BASE_LENGTH = 120.0
BASE_WIDTH = 80.0
BASE_THICKNESS = 8.0
CORNER_RADIUS = 4.0
HOLE_DIAMETER = 6.5  # clearance for M6
HOLE_EDGE_OFFSET = 12.0
BOSS_DIAMETER = 24.0
BOSS_HEIGHT = 15.0
POCKET_DIAMETER = 14.0
POCKET_DEPTH = 5.0

META = ParametricModelMeta(
    name="test_mounting_plate",
    description="Environment verification plate with fillets, holes, boss, and pocket.",
    dimensions={
        "base_length": Dimension("base_length", BASE_LENGTH, provenance=DataProvenance.ASSUMED),
        "base_width": Dimension("base_width", BASE_WIDTH, provenance=DataProvenance.ASSUMED),
        "base_thickness": Dimension("base_thickness", BASE_THICKNESS, provenance=DataProvenance.ASSUMED),
        "hole_diameter": Dimension("hole_diameter", HOLE_DIAMETER, provenance=DataProvenance.CALCULATED, notes="M6 clearance"),
        "hole_edge_offset": Dimension("hole_edge_offset", HOLE_EDGE_OFFSET, provenance=DataProvenance.ASSUMED),
    },
)


def build() -> cq.Workplane:
    plate = rounded_box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS, CORNER_RADIUS)

    hole_positions = [
        (BASE_LENGTH / 2 - HOLE_EDGE_OFFSET, BASE_WIDTH / 2 - HOLE_EDGE_OFFSET),
        (-BASE_LENGTH / 2 + HOLE_EDGE_OFFSET, BASE_WIDTH / 2 - HOLE_EDGE_OFFSET),
    ]
    plate = mounting_holes(plate, HOLE_DIAMETER, hole_positions)

    plate = (
        plate.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .center(0, 0)
        .circle(BOSS_DIAMETER / 2)
        .extrude(BOSS_HEIGHT)
    )

    plate = (
        plate.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .center(0, 0)
        .circle(POCKET_DIAMETER / 2)
        .cutBlind(-POCKET_DEPTH)
    )

    assert_valid_solid(plate, META.name)
    return plate


def main() -> None:
    model = build()
    vol = solid_volume(model)
    print(f"Model: {META.name}, volume = {vol:.2f} mm³")
    results = export_all(model, META.name, formats=("step", "stl", "3mf", "obj"))
    for r in results:
        print(f"  exported {r.format}: {r.path} ({r.bytes_written} bytes)")
    png = preview_matplotlib(model, title=META.name, show=False)
    print(f"  preview: {png}")


if __name__ == "__main__":
    main()
