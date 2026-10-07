"""Deterministic cost engine."""

from __future__ import annotations

from print_core import calculate_mass

from quote_api.engine.estimate import estimate_print_time_minutes
from quote_api.engine.margin import sale_price_from_cost
from quote_api.profiles.loader import get_machine, get_material, get_pricing
from quote_api.schemas import (
    CostBreakdown,
    MaterialProfile,
    MaterialSummary,
    ObjectSummary,
    QuoteAnalysis,
)
from print_core.models import PrintCoreAnalysis


def _pick_material_for_object(
    material_label: str | None,
    filament_index: int | None,
    default: MaterialProfile,
    catalog: list[MaterialProfile],
) -> MaterialProfile:
    if material_label:
        low = material_label.lower()
        if "varishore" in low or "foam" in low or "zacht" in low:
            for p in catalog:
                if "varishore" in p.id or "tpu" in p.id:
                    return p
        if "hard" in low or "pla" in low:
            for p in catalog:
                if "pla" in p.id:
                    return p
    if filament_index == 2:
        for p in catalog:
            if "varishore" in p.id or "tpu" in p.id:
                return p
    return default


def build_quote_analysis(
    *,
    core: PrintCoreAnalysis,
    mode: str,
    quantity: int,
    material_profile_id: str | None,
    machine_profile_id: str | None,
    pricing_profile_id: str | None,
    currency: str,
) -> QuoteAnalysis:
    from quote_api.profiles.loader import load_materials

    material_default = get_material(material_profile_id)
    machine = get_machine(machine_profile_id)
    pricing = get_pricing(pricing_profile_id)
    catalog = load_materials()

    objects: list[ObjectSummary] = []
    material_weights: dict[str, float] = {}
    total_weight = 0.0
    material_cost = 0.0

    for obj in core.objects:
        hint = obj.material_hints[0] if obj.material_hints else None
        label = hint.material_label if hint else None
        fidx = hint.filament_index if hint else None
        mat = _pick_material_for_object(label, fidx, material_default, catalog)
        w = calculate_mass(obj.volume_mm3, mat.density_g_cm3)
        total_weight += w
        material_cost += (w / 1000.0) * mat.price_per_kg
        key = mat.name
        material_weights[key] = material_weights.get(key, 0.0) + w
        objects.append(
            ObjectSummary(
                name=obj.name,
                volume_mm3=round(obj.volume_mm3, 2),
                weight_g=round(w, 2),
                filament_index=fidx,
                material_label=label,
            )
        )

    materials = [
        MaterialSummary(label=k, weight_g=round(v, 2)) for k, v in sorted(material_weights.items())
    ]

    print_min = estimate_print_time_minutes(
        volume_mm3=core.volume_mm3,
        object_count=core.object_count,
        machine=machine,
    )
    machine_cost = (print_min / 60.0) * machine.machine_cost_per_hour
    labor_cost = (pricing.labor_minutes_per_job / 60.0) * pricing.labor_cost_per_hour
    post = pricing.post_processing_cost_fixed
    pack = pricing.packaging_cost_fixed
    unit_cost = material_cost + machine_cost + labor_cost + post + pack
    cost_price = round(unit_cost * quantity, 2)
    sale = sale_price_from_cost(cost_price, pricing.margin_percent)

    return QuoteAnalysis(
        ok=True,
        mode="estimate" if mode == "estimate" else "quote",
        filename=core.filename,
        quantity=quantity,
        object_count=core.object_count,
        objects=objects,
        materials=materials,
        volume_mm3=round(core.volume_mm3, 2),
        weight_g=round(total_weight * quantity, 2),
        print_time_minutes=round(print_min * quantity, 1),
        material_cost=round(material_cost * quantity, 2),
        machine_cost=round(machine_cost * quantity, 2),
        labor_cost=round(labor_cost * quantity, 2),
        post_processing_cost=round(post * quantity, 2),
        packaging_cost=round(pack * quantity, 2),
        cost_price=cost_price,
        margin_percent=pricing.margin_percent,
        sale_price=sale,
        currency=currency,
        material_profile_id=material_default.id,
        machine_profile_id=machine.id,
        pricing_profile_id=pricing.id,
    )


def cost_breakdown_from_analysis(analysis: QuoteAnalysis) -> CostBreakdown:
    return CostBreakdown(
        material_cost=analysis.material_cost,
        machine_cost=analysis.machine_cost,
        labor_cost=analysis.labor_cost,
        post_processing_cost=analysis.post_processing_cost,
        packaging_cost=analysis.packaging_cost,
        cost_price=analysis.cost_price,
    )
