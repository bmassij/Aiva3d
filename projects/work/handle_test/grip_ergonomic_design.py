"""
Grip print design: photo/tuinslang envelope + algemene handvat-ergonomie.

Foto-metingen blijven leidend voor reconstructie; dit module geeft aanbevelingen
voor comfort (dikte, zachte laag, vorm) zonder stille overschrijving van CAD.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
    HARD_SOFT_CLEARANCE_MM,
    SOFT_WALL_NOMINAL_MM,
)


# Algemene richtlijnen cilindrisch / power-grip (literatuurband, geen norm)
ERGONOMIC_OD_MIN_MM = 30.0
ERGONOMIC_OD_COMFORT_MM = 32.0
ERGONOMIC_OD_SWEET_MM = 35.0
ERGONOMIC_OD_MAX_MM = 45.0
ERGONOMIC_LENGTH_MIN_PALM_MM = 100.0
SOFT_WALL_MIN_COMFORT_MM = 8.0
SOFT_WALL_IDEAL_VARISHORE_MM = 9.0


@dataclass
class GripDesignRecommendation:
    """Foto-envelope vs ergonomisch printvoorstel."""

    photo_length_mm: float
    photo_outer_diameter_mm: float
    photo_core_diameter_mm: float
    photo_soft_wall_mm: float

    ergonomic_od_band_mm: str
    recommended_nominal_od_mm: float
    recommended_soft_wall_mm: float
    recommended_length_mm: float

    od_rationale: str
    length_rationale: str
    shape_and_comfort: List[str]
    pain_reduction: List[str]
    hard_soft_notes: str
    apply_to_cad_note: str
    provenance: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "photo_envelope": {
                "length_mm": self.photo_length_mm,
                "outer_diameter_mm": self.photo_outer_diameter_mm,
                "core_diameter_mm": self.photo_core_diameter_mm,
                "soft_wall_mm": self.photo_soft_wall_mm,
            },
            "ergonomic_recommendation": {
                "nominal_od_mm": self.recommended_nominal_od_mm,
                "soft_wall_mm": self.recommended_soft_wall_mm,
                "length_mm": self.recommended_length_mm,
                "od_band": self.ergonomic_od_band_mm,
            },
            "od_rationale": self.od_rationale,
            "length_rationale": self.length_rationale,
            "shape_and_comfort": self.shape_and_comfort,
            "pain_reduction": self.pain_reduction,
            "hard_soft_notes": self.hard_soft_notes,
            "apply_to_cad_note": self.apply_to_cad_note,
            "provenance": self.provenance,
        }

    def markdown_nl(self) -> str:
        lines = [
            "## Handvat — foto (tuinslang) vs ergonomisch printvoorstel",
            "",
            "### Envelope van de referentie (tuinslang / mesh)",
            f"- Lengte langs boog: **{self.photo_length_mm:.0f} mm**",
            f"- Buiten-diameter (nominaal): **{self.photo_outer_diameter_mm:.1f} mm**",
            f"- Harde kern (staaf): **{self.photo_core_diameter_mm:.1f} mm**",
            f"- Zachte wand (nominaal): **{self.photo_soft_wall_mm:.2f} mm**",
            "",
            "### Ergonomische richtlijn (algemeen handvat)",
            f"- Gangbare OD-band cilindrisch/power-grip: **{self.ergonomic_od_band_mm}**",
            f"- **Aanbevolen print-OD:** **{self.recommended_nominal_od_mm:.1f} mm** — {self.od_rationale}",
            f"- **Aanbevolen lengte:** **{self.recommended_length_mm:.0f} mm** — {self.length_rationale}",
            f"- **Zachte VariShore-wand (radiaal):** **{self.recommended_soft_wall_mm:.2f} mm**",
            "",
            "### Vorm & grip",
        ]
        lines.extend(f"- {s}" for s in self.shape_and_comfort)
        lines.append("")
        lines.append("### Minder druk / pijn")
        lines.extend(f"- {s}" for s in self.pain_reduction)
        lines.append("")
        lines.append(f"**Hard + zacht:** {self.hard_soft_notes}")
        lines.append("")
        lines.append(f"**CAD:** {self.apply_to_cad_note}")
        return "\n".join(lines)


def recommend_grip_design(
    *,
    photo_length_mm: float = GRIP_LENGTH_MM,
    photo_outer_diameter_mm: float = GRIP_OUTER_DIAMETER_MM,
    photo_core_diameter_mm: float = HARD_CORE_DIAMETER_MM,
    clearance_mm: float = HARD_SOFT_CLEARANCE_MM,
    prefer_comfort_od: bool = True,
) -> GripDesignRecommendation:
    """
    Combine tuinslang/reference envelope with general handle ergonomics.

    ``prefer_comfort_od``: if True and foto-OD zit op onderkant comfortband,
    stel iets hogere nominale OD voor (zachtere laag blijft dik genoeg).
    """
    inner_r = photo_core_diameter_mm / 2.0 + clearance_mm
    photo_wall = photo_outer_diameter_mm / 2.0 - inner_r

    # Lengte: foto leidend, wel minimum palm-contact
    rec_length = photo_length_mm
    if rec_length < ERGONOMIC_LENGTH_MIN_PALM_MM:
        length_rationale = (
            f"Foto {photo_length_mm:.0f} mm onder palm-minimum ~{ERGONOMIC_LENGTH_MIN_PALM_MM:.0f} mm; "
            f"ergonomisch minstens {ERGONOMIC_LENGTH_MIN_PALM_MM:.0f} mm overwegen."
        )
        rec_length = max(rec_length, ERGONOMIC_LENGTH_MIN_PALM_MM)
    else:
        length_rationale = (
            f"Foto/tuinslang ~{photo_length_mm:.0f} mm voldoet voor palmcontact langs de boog; "
            "lengte behouden."
        )

    # OD: ondergrens ergonomisch, niet smaller than photo if photo already OK
    floor_od = max(photo_outer_diameter_mm, ERGONOMIC_OD_MIN_MM)
    rec_od = floor_od
    if prefer_comfort_od and floor_od <= ERGONOMIC_OD_COMFORT_MM + 0.5:
        rec_od = ERGONOMIC_OD_COMFORT_MM
        od_rationale = (
            f"Tuinslang ~{photo_outer_diameter_mm:.1f} mm; voor algemeen handvatcomfort "
            f"ligt **{ERGONOMIC_OD_COMFORT_MM:.0f}–{ERGONOMIC_OD_SWEET_MM:.0f} mm** gangbaar. "
            f"Voorstel: nominale print-OD **{rec_od:.1f} mm** (zachte laag compenseert druk)."
        )
    elif floor_od > ERGONOMIC_OD_MAX_MM:
        rec_od = ERGONOMIC_OD_SWEET_MM
        od_rationale = (
            f"Foto-OD {photo_outer_diameter_mm:.1f} mm boven typische bovengrens; "
            f"overweeg print **{rec_od:.1f} mm** tenzij grote handen/maximumkracht vereist is."
        )
    else:
        od_rationale = (
            f"Foto-OD {photo_outer_diameter_mm:.1f} mm binnen band "
            f"{ERGONOMIC_OD_MIN_MM:.0f}–{ERGONOMIC_OD_MAX_MM:.0f} mm; nominale print-OD **{rec_od:.1f} mm**."
        )

    rec_inner_r = photo_core_diameter_mm / 2.0 + clearance_mm
    rec_wall = rec_od / 2.0 - rec_inner_r
    if rec_wall < SOFT_WALL_MIN_COMFORT_MM:
        rec_wall = SOFT_WALL_MIN_COMFORT_MM
        rec_od = (rec_inner_r + rec_wall) * 2.0
        od_rationale += (
            f" Zachte wand opgehoogd tot min. **{SOFT_WALL_MIN_COMFORT_MM:.0f} mm** "
            f"→ OD **{rec_od:.1f} mm**."
        )

    shape = [
        "Volg de **boog-centerlijn** van het buitenste been (niet rechte extrusie van hele D-loop).",
        "Doorsnede: **rond** is baseline; licht **ovaal** (1–2 mm extra in duimrichting) kan slip verminderen — optionele latere variant.",
        "Afsluiting aan uiteinden: **afgeronde kap** (geen scherpe rand) voor minder hotspots op palm.",
        "Hard kern volgt **metalen staaf** (~{:.1f} mm); zachte buitenlaag draagt de **contactdruk**.".format(
            photo_core_diameter_mm
        ),
    ]
    pain = [
        "Compressible VariShore **verlaagt piekdruk** — voelt groter/zachter dan nominale CAD-OD.",
        f"Nominale zachte wand ≥ **{SOFT_WALL_MIN_COMFORT_MM:.0f} mm** helpt druk te spreiden (doel ~{SOFT_WALL_IDEAL_VARISHORE_MM:.0f} mm).",
        "Te smalle OD (< 30 mm) verhoogt contactdruk; te brede OD (> 45 mm) belast kleine handen.",
        "Grip-lengte voldoende voor **verdeling over palm** — niet alleen vingertoppen.",
    ]
    hard_soft = (
        "Twee-delig print: **hard** binnenhuls op staaf (± clearance {:.2f} mm), "
        "**zacht** schuimachtig om hard heen — mesh/tuinslang is **geen** printmateriaal."
        .format(clearance_mm)
    )
    apply = (
        "Standaard CAD blijft foto-gestuurd (30 mm OD). "
        "Schakel in UI **‘Ergonomisch comfort-OD’** om outer_radius naar aanbeveling te zetten."
    )

    return GripDesignRecommendation(
        photo_length_mm=photo_length_mm,
        photo_outer_diameter_mm=photo_outer_diameter_mm,
        photo_core_diameter_mm=photo_core_diameter_mm,
        photo_soft_wall_mm=round(photo_wall, 2),
        ergonomic_od_band_mm=f"{ERGONOMIC_OD_MIN_MM:.0f}–{ERGONOMIC_OD_MAX_MM:.0f} mm",
        recommended_nominal_od_mm=round(rec_od, 1),
        recommended_soft_wall_mm=round(rec_wall, 2),
        recommended_length_mm=round(rec_length, 1),
        od_rationale=od_rationale,
        length_rationale=length_rationale,
        shape_and_comfort=shape,
        pain_reduction=pain,
        hard_soft_notes=hard_soft,
        apply_to_cad_note=apply,
        provenance={
            "photo_length": "measured / grid",
            "photo_od": "measured / grid",
            "recommended_od": "calculated / ergonomic_guidance",
            "recommended_wall": "calculated",
        },
    )


def parameters_comfort_overrides(recommendation: GripDesignRecommendation) -> Dict[str, float]:
    """Slider/CAD overrides when user enables ergonomic comfort mode."""
    return {
        "outer_radius_mm": recommendation.recommended_nominal_od_mm / 2.0,
        "core_radius_mm": recommendation.photo_core_diameter_mm / 2.0,
    }
