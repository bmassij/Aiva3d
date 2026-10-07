"""

Parametric grip — millimeters.



Authoritative dimensions load from reference_measurements.json (grid: 10 mm / square).

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import List, Tuple



from projects.work.handle_test.design_constants import (

    GRIP_OUTER_DIAMETER_MM,

    HARD_SOFT_CLEARANCE_MM,

)

from projects.work.handle_test.measurements_loader import parameters_from_measurements





@dataclass

class HandleParameters:

    centerline_points_mm: List[Tuple[float, float]] = field(default_factory=list)

    core_radius_mm: float = 5.0

    outer_radius_mm: float = 15.0

    clearance_mm: float = 0.2



    @property

    def soft_inner_radius_mm(self) -> float:

        return self.core_radius_mm + self.clearance_mm



    @property

    def soft_wall_thickness_mm(self) -> float:

        return self.outer_radius_mm - self.soft_inner_radius_mm



    @property

    def inner_cut_radius_mm(self) -> float:

        return self.soft_inner_radius_mm



    def validate_relationships(self) -> None:

        inner = self.core_radius_mm + self.clearance_mm

        if abs(self.soft_inner_radius_mm - inner) > 1e-6:

            raise ValueError("soft_inner_radius must equal core_radius + clearance")

        wall = self.outer_radius_mm - self.soft_inner_radius_mm

        if abs(self.soft_wall_thickness_mm - wall) > 1e-6:

            raise ValueError("soft_wall_thickness must equal outer_radius - soft_inner_radius")



    def summary(self) -> dict:

        return {

            "centerline_points_mm": self.centerline_points_mm,

            "core_radius_mm": self.core_radius_mm,

            "clearance_mm": self.clearance_mm,

            "soft_inner_radius_mm": self.soft_inner_radius_mm,

            "outer_radius_mm": self.outer_radius_mm,

            "soft_wall_thickness_mm": self.soft_wall_thickness_mm,

        }





def parameters_from_sliders(

    centerline_points_mm: List[Tuple[float, float]],

    core_radius_mm: float,

    clearance_mm: float,

    outer_radius_mm: float | None = None,

) -> HandleParameters:

    """Build from UI: core + clearance + authoritative soft outer radius (30 mm OD)."""

    outer = float(outer_radius_mm if outer_radius_mm is not None else GRIP_OUTER_DIAMETER_MM / 2.0)

    params = HandleParameters(

        centerline_points_mm=list(centerline_points_mm),

        core_radius_mm=float(core_radius_mm),

        outer_radius_mm=outer,

        clearance_mm=float(clearance_mm),

    )

    params.validate_relationships()

    return params





def default_parameters() -> HandleParameters:

    data = parameters_from_measurements()

    params = HandleParameters(

        centerline_points_mm=list(data["centerline_points_mm"]),

        core_radius_mm=float(data["core_radius_mm"]),

        outer_radius_mm=float(data["outer_radius_mm"]),

        clearance_mm=HARD_SOFT_CLEARANCE_MM,

    )

    params.validate_relationships()

    return params


