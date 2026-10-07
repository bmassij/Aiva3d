"""Pydantic models for Quote API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class MaterialProfile(BaseModel):
    id: str
    name: str
    density_g_cm3: float = Field(gt=0)
    price_per_kg: float = Field(ge=0)


class MachineProfile(BaseModel):
    id: str
    name: str
    machine_cost_per_hour: float = Field(ge=0)
    default_print_speed_mm_s: float = Field(gt=0)
    default_layer_height_mm: float = Field(gt=0)
    default_infill: float = Field(ge=0, le=1)
    notes: str = ""


class PricingProfile(BaseModel):
    id: str
    name: str
    labor_cost_per_hour: float = Field(ge=0)
    labor_minutes_per_job: float = Field(ge=0)
    post_processing_cost_fixed: float = Field(ge=0)
    packaging_cost_fixed: float = Field(ge=0)
    margin_percent: float = Field(ge=0)


class ObjectSummary(BaseModel):
    name: str
    volume_mm3: float
    weight_g: float
    filament_index: Optional[int] = None
    material_label: Optional[str] = None


class MaterialSummary(BaseModel):
    label: str
    weight_g: float
    filament_index: Optional[int] = None


class CostBreakdown(BaseModel):
    material_cost: float
    machine_cost: float
    labor_cost: float
    post_processing_cost: float
    packaging_cost: float
    cost_price: float


class QuoteAnalysis(BaseModel):
    ok: bool = True
    mode: Literal["estimate", "quote"] = "quote"
    filename: str
    quantity: int = 1
    object_count: int
    objects: list[ObjectSummary]
    materials: list[MaterialSummary]
    volume_mm3: float
    weight_g: float
    print_time_minutes: float
    print_time_note: str = "ESTIMATE — not slicer-exact"
    material_cost: float
    machine_cost: float
    labor_cost: float
    post_processing_cost: float
    packaging_cost: float
    cost_price: float
    margin_percent: float
    sale_price: float
    currency: str = "EUR"
    material_profile_id: str
    machine_profile_id: str
    pricing_profile_id: str
    profiles_note: str = "DEVELOPMENT DEFAULT profiles unless configured for production"


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
