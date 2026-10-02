"""Aiva3D Streamlit CAD AI UI — reference upload, NL iteration, 3D preview, export."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exporters.pipeline import export_3mf, export_step, export_stl
from projects.work.handle_test import model as handle_model
from projects.work.handle_test.parameters import HandleParameters, default_parameters
from projects.work.handle_test.validation import validate_handle_pair
from ui.design_record import (
    HANDLE_CUSTOMER_TEXT,
    DesignRecord,
    design_record_from_handle_customer_text,
)
from ui.mesh_viewer import figure_from_workpieces, figure_side_by_side
from ui.model_session import BuiltModel, ModelSession
from ui.nl_adjust import apply_instruction
from ui.reference_images import list_reference_images, save_uploads_from_streamlit

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
    if "project_id" not in st.session_state:
        st.session_state.project_id = "handle_test"


def _build_handle(params: HandleParameters) -> BuiltModel:
    hard, soft = handle_model.build(params)
    stats = validate_handle_pair(hard, soft, params)
    return BuiltModel(
        hard_core=hard,
        soft_outer=soft,
        metadata={"validation": stats, "parameters": params.summary()},
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
    st.caption("Parametric CadQuery workspace with reference-driven reverse engineering.")

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

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Customer instruction (preserved)")
        st.info(HANDLE_CUSTOMER_TEXT)
    with col_right:
        st.subheader("Design record")
        with st.expander("Requirements & provenance"):
            st.json(record.to_dict())

    st.subheader("Parameters (mm)")
    c1, c2, c3 = st.columns(3)
    with c1:
        core = st.number_input("Core radius", min_value=1.0, max_value=40.0, value=float(params.core_radius_mm))
    with c2:
        wall = st.number_input(
            "Outer wall (VariShore)",
            min_value=0.5,
            max_value=15.0,
            value=float(params.outer_layer_thickness_mm),
        )
    with c3:
        clearance = st.number_input("Clearance", min_value=0.05, max_value=2.0, value=float(params.clearance_mm))

    params = HandleParameters(
        centerline_points_mm=list(params.centerline_points_mm),
        core_radius_mm=float(core),
        outer_layer_thickness_mm=float(wall),
        clearance_mm=float(clearance),
    )
    st.session_state.params = params

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
    if display is None and session.last_valid is None:
        st.info("No valid model yet. Click **Generate model**.")

    if display is not None:
        st.subheader("3D preview")
        if session.comparison is not None:
            left, right = figure_side_by_side(
                session.display_parts(session.comparison),
                session.display_parts(display),
                left_title="Saved comparison",
                right_title="Current model",
            )
            pc1, pc2 = st.columns(2)
            with pc1:
                st.plotly_chart(left, use_container_width=True)
            with pc2:
                st.plotly_chart(right, use_container_width=True)
        else:
            fig = figure_from_workpieces(session.display_parts(display), title="Current model")
            st.plotly_chart(fig, use_container_width=True)

        if export_clicked:
            paths = _export_pair(display, "handle_test")
            st.success("Exported hard + soft parts:")
            for line in paths:
                st.code(line, language=None)

    with st.expander("Session history"):
        st.write(session.history or ["No builds yet."])


if __name__ == "__main__":
    main()
