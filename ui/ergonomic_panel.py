"""Ergonomic design check panel for Streamlit."""

from __future__ import annotations

import streamlit as st

from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
    HARD_SOFT_CLEARANCE_MM,
    SOFT_WALL_NOMINAL_MM,
)
from projects.work.handle_test.ergonomics import assess_grip_od
from projects.work.handle_test.grip_ergonomic_design import (
    recommend_grip_design,
)


def render_ergonomic_panel() -> None:
    st.subheader("ERGONOMIC CHECK & GRIP DESIGN")
    assessment = assess_grip_od(GRIP_OUTER_DIAMETER_MM)
    rec = recommend_grip_design(
        photo_length_mm=GRIP_LENGTH_MM,
        photo_outer_diameter_mm=GRIP_OUTER_DIAMETER_MM,
        photo_core_diameter_mm=HARD_CORE_DIAMETER_MM,
        clearance_mm=HARD_SOFT_CLEARANCE_MM,
    )

    st.write(
        {
            "Foto/tuinslang OD (reconstructie)": f"{assessment.measured_od_mm:.1f} mm",
            "Ergonomische band (cilinder)": assessment.ergonomic_range_mm,
            "Aanbevolen print-OD (comfort)": f"{rec.recommended_nominal_od_mm:.1f} mm",
            "Aanbevolen zachte wand": f"{rec.recommended_soft_wall_mm:.2f} mm",
            "Lengte (boog)": f"{rec.recommended_length_mm:.0f} mm",
        }
    )

    with st.expander("Waarom deze dikte / minder pijn?", expanded=True):
        st.markdown(rec.markdown_nl())

    st.info(
        "**Tuinslang** = referentie voor vorm en grid-meting. **Print** = hard + zacht; "
        "nominaal **32 mm OD** is een ergonomisch comfortvoorstel boven de foto-**30 mm**, "
        "omdat VariShore onder druk zachter aanvoelt. Foto-reconstructie blijft 30 mm tot je "
        "hieronder comfort toepast."
    )

    if st.button("Pas ergonomisch comfort-OD toe op sliders", use_container_width=True):
        if "params" in st.session_state:
            p = st.session_state.params
            p.outer_radius_mm = rec.recommended_nominal_od_mm / 2.0
            st.session_state.params = p
            st.session_state.ergonomic_comfort_applied = True
            st.success(
                f"Outer radius → {p.outer_radius_mm:.2f} mm "
                f"(OD {rec.recommended_nominal_od_mm:.1f} mm). Genereer opnieuw."
            )
        else:
            st.warning("Parameters nog niet geladen.")

    st.caption(assessment.references_note)


from projects.work.handle_test.materials import legend_markdown_nl


def render_materials_panel() -> None:
    st.subheader("MATERIALS")
    st.markdown(legend_markdown_nl())
    st.write(
        {
            "Hard core (print)": "Structuur binnenin — Ø {:.1f} mm — niet-schuim".format(HARD_CORE_DIAMETER_MM),
            "Soft outer (print)": "VariShore schuim — nominale OD 30,0 mm",
            "Bestaande staaf (foto)": "Rond staal onder de mesh — Ø {:.1f} mm, niet printen".format(
                HARD_CORE_DIAMETER_MM
            ),
            "Nominal soft wall (radial)": f"{SOFT_WALL_NOMINAL_MM:.2f} mm",
            "Hard/soft clearance (CAD)": f"{HARD_SOFT_CLEARANCE_MM:.2f} mm",
        }
    )
    st.info(
        "Op de foto: **metaal + mesh-hoes**. In CAD exporteer je alleen **hard + soft**. "
        "De preview kan schakelen tussen **printweergave** (blauw+groen) en **fotoweergave** "
        "(grijze staaf + groen, zoals de mesh op het staal)."
    )
    st.caption(
        "VariShore voelt groter/zachter in gebruik dan de nominale CAD-diameter; compressie niet gemodelleerd."
    )
