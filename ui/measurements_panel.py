"""Display grid-calibrated reference measurements in Streamlit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from projects.work.handle_test.grid_measure import save_reference_measurements
from projects.work.handle_test.design_constants import (
    HARD_SOFT_CLEARANCE_MM,
    SOFT_INNER_RADIUS_MM,
    SOFT_OUTER_RADIUS_MM,
    SOFT_WALL_NOMINAL_MM,
)
from projects.work.handle_test.measurements_loader import (
    authoritative_grip,
    centerline_for_cad,
    centerline_metadata,
    load_measurements_doc,
)

PROJECT_DIR = Path(__file__).resolve().parents[1] / "projects" / "work" / "handle_test"


def rerun_measurements() -> dict[str, Any]:
    save_reference_measurements(PROJECT_DIR)
    return load_measurements_doc()


def render_measurements_panel() -> dict[str, Any]:
    st.subheader("REFERENCE SCALE")
    doc = load_measurements_doc()
    if not doc:
        st.warning("No reference_measurements.json — run calibration first.")
        if st.button("Calibrate from photos"):
            doc = rerun_measurements()
        return doc

    grid = doc.get("grid", {})
    st.markdown(
        f"**Grid:** {grid.get('square_width_mm', 10)} × {grid.get('square_height_mm', 10)} mm  \n"
        f"**Certainty:** {grid.get('certainty', 'known')} — {grid.get('source', '')}"
    )

    if st.button("Re-calibrate from photos"):
        doc = rerun_measurements()
        st.success("Updated reference_measurements.json and calibrated overlays.")

    verified = doc.get("photo_grid_counts_verified") or {}
    grip = authoritative_grip(doc)

    st.markdown("### Measured grip (authoritative for CAD)")
    st.write(
        {
            "Grip length": f"{grip.get('length_mm')} mm "
            f"({verified.get('grip_length_squares', '?')} squares × 10 mm)",
            "Grip outer diameter": f"{grip.get('outer_diameter_mm')} mm "
            f"({verified.get('grip_od_squares', '?')} squares × 10 mm)",
            "Hard core diameter": f"{grip.get('core_diameter_mm')} mm",
            "Soft inner radius (core + clearance)": f"{SOFT_INNER_RADIUS_MM:.2f} mm",
            "Soft outer radius (OD/2)": f"{SOFT_OUTER_RADIUS_MM:.2f} mm",
            "Soft wall thickness (material)": f"{SOFT_WALL_NOMINAL_MM:.2f} mm",
            "Hard/soft clearance": f"{HARD_SOFT_CLEARANCE_MM:.2f} mm",
            "Centerline (CAD)": centerline_for_cad(doc),
            "Centerline meta": centerline_metadata(doc),
            "Confidence": verified.get("confidence", "see per-measurement"),
            "Method": verified.get("method"),
        }
    )

    auto = doc.get("grip", {})
    if auto.get("length_mm_automated_cv") is not None:
        st.markdown("### Automated CV (comparison only)")
        st.caption(auto.get("notes") or verified.get("notes", ""))
        st.write(
            {
                "length_mm_automated_cv": auto.get("length_mm_automated_cv"),
                "outer_diameter_mm_automated_cv": auto.get("outer_diameter_mm_automated_cv"),
            }
        )

    with st.expander("Per-photo measurements & calibration"):
        st.json(doc.get("photos", []))

    overlays = []
    for photo in doc.get("photos", []):
        path = photo.get("overlay_path")
        if path and Path(path).exists():
            overlays.append(path)
    if overlays:
        st.markdown("### Calibrated overlays")
        for op in overlays:
            st.image(op, caption=Path(op).name, use_container_width=True)

    st.markdown("### Manual grid override (squares × 10 mm)")
    c1, c2, c3 = st.columns(3)
    with c1:
        sq_len = st.number_input("Grip length (squares)", value=float(verified.get("grip_length_squares", 11.0)), step=0.1)
    with c2:
        sq_od = st.number_input("Grip OD (squares)", value=float(verified.get("grip_od_squares", 3.0)), step=0.1)
    with c3:
        core_d = st.number_input("Core diameter (mm)", value=float(grip.get("core_diameter_mm", 11.0)), step=0.1)
    if st.button("Save manual grid counts to JSON"):
        doc["photo_grid_counts_verified"] = {
            **verified,
            "grip_length_squares": sq_len,
            "grip_od_squares": sq_od,
            "core_diameter_mm": core_d,
            "method": "manual_grid_square_count_ui",
            "confidence": "user_verified",
        }
        path = PROJECT_DIR / "reference_measurements.json"
        import json

        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        st.success(f"Saved {path}")

    return doc
