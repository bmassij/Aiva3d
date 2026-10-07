"""LM Studio CadQuery model — experimental code generation + STEP for FreeCAD."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from aiva3d.ai.cadquery_provider import CadQueryProvider
from aiva3d.ai.handle_cad_spec import handle_params_to_cad_spec
from aiva3d.ai.lmstudio_client import LMStudioError
from aiva3d.ai.pipeline import run_cadquery_pipeline
from aiva3d.ai.sandbox_runner import export_validated_cadquery
from aiva3d.ai.settings import load_settings
from projects.work.handle_test.parameters import HandleParameters

ROOT = Path(__file__).resolve().parents[1]
LLM_EXPORT_DIR = ROOT / "projects" / "work" / "handle_test" / "exports" / "llm_cadquery"


def render_cadquery_llm_panel(params: HandleParameters) -> None:
    settings = load_settings()
    st.subheader("CadQuery LLM (LM Studio)")
    st.caption(
        f"Model: `{settings.cadquery_model}` · Vision blijft `{settings.vision_model}` — "
        "geen foto's naar dit model."
    )

    with st.expander("Werkt CadQuery in FreeCAD?", expanded=False):
        st.markdown(
            """
**CadQuery draait in Python (Aiva3D), niet inside het FreeCAD-venster.**

- **FreeCAD** = eigen Part-workbench + Python-API (`Part.makeCylinder`, …).
- **CadQuery** = Python-library op **dezelfde OpenCascade-kernel**, maar andere code.

**Wel compatible:** CadQuery → **STEP/STL export** → FreeCAD **File → Import** of onze bridge
(`hard_core.step` / `soft_grip.step` komen ook uit CadQuery).

**Waarom niet alles via het LLM?** Het handle-project gebruikt geteste parametrische code
(`model.py`: boog, hard+soft, validatie). Het LLM is **experiment** — handig voor ideeën,
niet de enige bron van waarheid voor jullie grip.

**NC-licentie:** fine-tune is non-commercial (CC-BY-NC-SA-4.0).
            """
        )

    if not st.session_state.get("measurements_applied"):
        st.warning("Eerst **Apply photo measurements to parameters**.")
        return

    if st.button("Genereer CadQuery via LM Studio", use_container_width=True):
        spec = handle_params_to_cad_spec(params)
        provider = CadQueryProvider.from_env()
        with st.spinner(f"LM Studio ({provider.model_id})…"):
            try:
                result = run_cadquery_pipeline(spec, provider=provider)
            except LMStudioError as exc:
                st.error(str(exc))
                return

        if not result.success or not result.code:
            st.error("Generatie mislukt: " + "; ".join(result.errors[:5]))
            return

        LLM_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        step_path = LLM_EXPORT_DIR / "llm_grip_result.step"
        stl_path = LLM_EXPORT_DIR / "llm_grip_result.stl"
        geom = export_validated_cadquery(result.code, step_path=step_path, stl_path=stl_path)
        if not geom.valid:
            st.error("Export mislukt: " + "; ".join(geom.errors))
            return

        st.session_state.llm_cadquery = {
            "code": result.code,
            "step": str(step_path),
            "stl": str(stl_path),
            "bbox": geom.bbox,
            "volume": geom.volume,
            "repair_attempts": result.repair_attempts,
        }
        st.success(
            f"OK — solid_count={geom.solid_count}, repair_pogingen={result.repair_attempts}. "
            f"STEP voor FreeCAD: `{step_path.name}`"
        )

    llm = st.session_state.get("llm_cadquery")
    if llm:
        st.code(llm["code"][:4000] + ("…" if len(llm["code"]) > 4000 else ""), language="python")
        st.write(
            {
                "STEP (FreeCAD import)": llm["step"],
                "STL": llm["stl"],
                "bbox_mm": llm.get("bbox"),
                "volume_mm3": llm.get("volume"),
            }
        )
        st.info(
            "In **FreeCAD**: File → Import → "
            f"`projects/work/handle_test/exports/llm_cadquery/llm_grip_result.step`. "
            "Of kopieer naar je assembly naast hard/soft STEP."
        )
