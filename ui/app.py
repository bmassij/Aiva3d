"""Aiva3D Streamlit CAD AI UI — reference upload, NL iteration, 3D preview, export."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_UI = Path(__file__).resolve().parent
if str(_UI) not in sys.path:
    sys.path.insert(0, str(_UI))

import importlib

import projects.work.handle_test.design_constants as _design_constants
import projects.work.handle_test.measurements_loader as _measurements_loader
import projects.work.handle_test.parameters as _handle_parameters

importlib.reload(_design_constants)
importlib.reload(_measurements_loader)
importlib.reload(_handle_parameters)

from exporters.pipeline import export_3mf, export_step, export_stl
import projects.work.handle_test.model as handle_model

importlib.reload(handle_model)

import projects.work.handle_test.validation as _handle_validation

importlib.reload(_handle_validation)

from projects.work.handle_test.parameters import (
    HandleParameters,
    default_parameters,
    parameters_from_sliders,
)
from projects.work.handle_test.validation import (
    validate_grip_position_on_reference_handle,
    validate_handle_pair,
)
from cad.utilities.validation import assert_valid_solid
from ui.design_record import (
    HANDLE_CUSTOMER_TEXT,
    DesignRecord,
    design_record_from_handle_customer_text,
)
try:
    from ui.mesh_viewer import (
        figure_exploded_clamshell,
        figure_from_workpieces,
        figure_full_handle,
        figure_material_section,
        figure_side_by_side,
    )
except ImportError:
    from mesh_viewer import (  # type: ignore[no-redef]
        figure_exploded_clamshell,
        figure_from_workpieces,
        figure_full_handle,
        figure_material_section,
        figure_side_by_side,
    )
from ui.model_session import BuiltModel, ModelSession
from ui.nl_adjust import apply_instruction
from ui.ergonomic_panel import render_ergonomic_panel, render_materials_panel
from ui.measurements_panel import render_measurements_panel
from ui.freecad_panel import render_freecad_panel
from ui.cadquery_llm_panel import render_cadquery_llm_panel
from ui.reference_images import list_reference_images, save_uploads_from_streamlit
import projects.work.handle_test.reference_geometry as _reference_geometry

importlib.reload(_reference_geometry)

from projects.work.handle_test.reference_geometry import build_metal_rod_context

PROJECTS = {
    "handle_test": {
        "label": "Handle test (dual-material grip)",
        "description": "Hard core + VariShore shell along spline centerline.",
    },
}


def _init_state() -> None:
    if "session" not in st.session_state:
        st.session_state.session = ModelSession()
    if "design_record" not in st.session_state:
        st.session_state.design_record = design_record_from_handle_customer_text()
    if "params" not in st.session_state:
        st.session_state.params = default_parameters()
    if "measurements_applied" not in st.session_state:
        from projects.work.handle_test.measurements_loader import load_measurements_doc

        st.session_state.measurements_applied = bool(load_measurements_doc())
    if "show_reference_metal" not in st.session_state:
        st.session_state.show_reference_metal = False
    if "project_id" not in st.session_state:
        st.session_state.project_id = "handle_test"


def _build_handle(params: HandleParameters) -> BuiltModel:
    hard, soft = handle_model.build(params)
    metal_rod = build_metal_rod_context(params)
    stats = validate_handle_pair(hard, soft, params)
    assert_valid_solid(metal_rod, "metal_rod_context")
    grip_pos = validate_grip_position_on_reference_handle(hard, params, metal_rod)
    return BuiltModel(
        hard_core=hard,
        soft_outer=soft,
        reference_metal=metal_rod,
        metadata={
            "validation": stats,
            "metal_rod_context": {"role": "existing_rod_under_mesh", "diameter_mm": 11.1},
            "grip_position": grip_pos,
            "parameters": params.summary(),
        },
    )


def _run_build(params: HandleParameters, note: str) -> None:
    session: ModelSession = st.session_state.session
    try:
        built = _build_handle(params)
        session.apply_build(built, note=note)
        st.success("Model generated and validated.")
    except Exception as exc:  # noqa: BLE001 — surface CAD errors in UI
        session.apply_failure(str(exc))
        st.error(f"Build failed: {exc}")
        if session.last_valid is not None:
            st.warning("Showing last valid model (previous build preserved).")


def _export_pair(built: BuiltModel, basename: str) -> list[str]:
    messages: list[str] = []
    for suffix, workpiece in (("hard", built.hard_core), ("soft", built.soft_outer)):
        name = f"{basename}_{suffix}"
        step = export_step(workpiece, name)
        stl = export_stl(workpiece, name)
        mf3 = export_3mf(workpiece, name)
        messages.extend(
            [
                f"STEP: {step.path}",
                f"STL: {stl.path}",
                f"3MF: {mf3.path}",
            ]
        )
    return messages


def main() -> None:
    st.set_page_config(page_title="Aiva3D", layout="wide")
    _init_state()

    session: ModelSession = st.session_state.session
    record: DesignRecord = st.session_state.design_record
    params: HandleParameters = st.session_state.params

    st.title("Aiva3D — CAD AI")
    st.caption("Parametric CadQuery workspace — 3D preview, FreeCAD-export, print-helften.")

    params = st.session_state.params
    if session.last_valid is None:
        _run_build(params, note="auto-preview")

    st.subheader("3D weergave")
    from projects.work.handle_test.materials import legend_markdown_nl

    st.markdown(legend_markdown_nl())
    view_mode = st.radio(
        "Weergave",
        options=("hendel", "helften", "materialen", "foto"),
        format_func=lambda k: {
            "hendel": "Kaal metaal (D-lus, geen klik)",
            "materialen": "Materialen (doorsnede: metaal / hard / schuim)",
            "helften": "Handvat / tuinslang (slider + klik)",
            "foto": "Foto-modus (staaf + hoes)",
        }[k],
        horizontal=True,
        key="preview_view_mode",
    )
    try:
        if view_mode == "hendel":
            st.caption(
                "Kale metalen D-lus van de foto: één vast stuk. Geen klik, geen tuinslang."
            )
            from pathlib import Path as _P

            _png = _P(__file__).resolve().parents[1] / "projects/work/handle_test/exports/drawings/handle_bare_metal.png"
            if _png.exists():
                st.image(str(_png), caption="Plan-aanzicht (zelfde kant als de foto)")
            st.plotly_chart(figure_full_handle(), use_container_width=True)
        elif view_mode == "materialen":
            st.caption("Grijs = bestaande staaf, blauw = hard, groen = VariShore (halve buitenlaag).")
            st.plotly_chart(figure_material_section(), use_container_width=True)
        elif view_mode == "helften":
            st.caption(
                "Alleen het handvat dat om de staaf gaat (vervangt de tuinslang). "
                "Oranje = slider, rood = klikhaak. Het metaal zelf klikt niet."
            )
            st.plotly_chart(figure_exploded_clamshell("Helften — slider in inkeping + haak"), use_container_width=True)
        elif session.last_valid is not None:
            fig = figure_from_workpieces(
                session.display_parts(session.last_valid, show_reference_metal=True),
                title="Foto-modus",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Model nog niet gebouwd.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"3D preview mislukt: {exc}")

    st.divider()

    with st.sidebar:
        st.header("Project")
        project_id = st.selectbox(
            "Active project",
            options=list(PROJECTS.keys()),
            format_func=lambda k: PROJECTS[k]["label"],
            key="project_select",
        )
        st.session_state.project_id = project_id
        st.markdown(PROJECTS[project_id]["description"])

        st.divider()
        st.subheader("Reference images")
        uploads = st.file_uploader(
            "Upload photos (graph paper grid)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        if st.button("Save uploads", use_container_width=True) and uploads:
            paths = save_uploads_from_streamlit(project_id, uploads)
            record.reference_data.append(f"Uploaded {len(paths)} image(s) via UI.")
            record.touch()
            st.success(f"Saved {len(paths)} file(s) to project reference/.")

        refs = list_reference_images(project_id)
        if refs:
            st.write("On disk:")
            for path in refs[:8]:
                st.text(path.name)
            if len(refs) > 8:
                st.caption(f"+ {len(refs) - 8} more")

    render_measurements_panel()
    render_ergonomic_panel()
    render_materials_panel()
    render_freecad_panel(params)

    st.divider()
    render_cadquery_llm_panel(params)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Customer instruction (preserved)")
        st.info(HANDLE_CUSTOMER_TEXT)
    with col_right:
        st.subheader("Design record")
        with st.expander("Requirements & provenance"):
            st.json(record.to_dict())

    st.subheader("CAD parameters (from reference_measurements.json)")
    c1, c2, c3 = st.columns(3)
    with c1:
        core = st.number_input(
            "Hard core radius (mm)",
            min_value=1.0,
            max_value=40.0,
            value=float(params.core_radius_mm),
        )
    with c2:
        clearance = st.number_input("Clearance (mm)", min_value=0.05, max_value=2.0, value=float(params.clearance_mm))
    with c3:
        outer_r = st.number_input(
            "Soft shell outer radius (mm)",
            min_value=5.0,
            max_value=40.0,
            value=float(params.outer_radius_mm),
            help="Authoritative grip OD is 30 mm → 15.00 mm radius.",
        )
    inner_r = float(core) + float(clearance)
    wall_t = float(outer_r) - inner_r
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Soft shell inner radius", f"{inner_r:.2f} mm")
    m2.metric("Soft wall thickness", f"{wall_t:.2f} mm")
    m3.metric("Soft shell outer radius", f"{float(outer_r):.2f} mm")
    m4.metric("Grip OD", f"{float(outer_r) * 2:.1f} mm")

    if st.button("Apply photo measurements to parameters", use_container_width=True):
        st.session_state.params = default_parameters()
        st.session_state.measurements_applied = True
        st.success("Parameters loaded from reference_measurements.json.")

    params = st.session_state.params
    base_centerline = (
        list(default_parameters().centerline_points_mm)
        if st.session_state.measurements_applied
        else list(params.centerline_points_mm)
    )
    params = parameters_from_sliders(
        base_centerline,
        float(core),
        float(clearance),
        outer_radius_mm=float(outer_r),
    )
    st.session_state.params = params
    if not st.session_state.measurements_applied:
        st.warning("Apply photo measurements before generating CAD (grid-calibrated values).")

    st.subheader("Natural-language instruction")
    instruction = st.text_area(
        "Describe changes (e.g. thicker grip, core radius 12 mm, wall 4 mm)",
        value=record.original_instruction if record.original_instruction != HANDLE_CUSTOMER_TEXT else "",
        height=100,
        placeholder="Adjust grip thickness, shell wall, or paste measured values…",
    )

    btn_gen, btn_compare, btn_export = st.columns(3)
    with btn_gen:
        if st.button("Generate model", type="primary", use_container_width=True):
            merged, notes = apply_instruction(instruction, params)
            st.session_state.params = merged
            for note in notes:
                record.change_log.append(note)
            if instruction.strip():
                record.original_instruction = instruction.strip()
            record.touch()
            _run_build(merged, note="generate")

    with btn_compare:
        if st.button("Save snapshot for comparison", use_container_width=True):
            session.save_comparison_snapshot()
            st.toast("Comparison snapshot saved.")

    with btn_export:
        export_clicked = st.button("Export STEP / STL / 3MF", use_container_width=True)

    if session.last_error:
        st.error(f"Last error: {session.last_error}")

    display = session.last_valid
    if display is None:
        st.info("No valid model yet. Click **Generate model**.")

    if export_clicked and display is not None:
        paths = _export_pair(display, "handle_test")
        st.success("Exported hard + soft parts:")
        for line in paths:
            st.code(line, language=None)

    with st.expander("Session history"):
        st.write(session.history or ["No builds yet."])


if __name__ == "__main__":
    main()
