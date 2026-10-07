"""Streamlit FreeCAD connection panel."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from aiva3d.freecad.bridge import FreeCADConnection
from aiva3d.freecad.cmd_runner import detect_freecad_cmd
from aiva3d.freecad.object_sync import default_fcstd_path
from aiva3d.freecad.protocol import BridgeResponse
from projects.work.handle_test.parameters import HandleParameters

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = ROOT / "scripts" / "freecad" / "aiva3d_bridge_server.py"
EXPORT_DIR = ROOT / "projects" / "work" / "handle_test" / "exports"


def _get_connection() -> FreeCADConnection:
    if "freecad_connection" not in st.session_state:
        st.session_state.freecad_connection = FreeCADConnection()
    return st.session_state.freecad_connection



def _sync_to_freecad(conn: FreeCADConnection, params: HandleParameters) -> BridgeResponse:
    """Connect if needed, sync via HTTP bridge or FreeCADCmd fallback."""
    if not conn.is_connected:
        conn.connect()
    if not conn.is_connected:
        return BridgeResponse(
            success=False,
            command="SYNC",
            message="Not connected",
            error="Start bridge: scripts/restart_freecad_bridge.ps1",
        )
    result = conn.sync_model(params, default_fcstd_path(ROOT))
    if result.success:
        return result
    if conn.mode == "http" and detect_freecad_cmd():
        conn.mode = "cmd"
        fallback = conn.sync_model(params, default_fcstd_path(ROOT))
        if fallback.success:
            fallback.message += " (via FreeCADCmd — open handle_assembly.FCStd in FreeCAD)"
        return fallback
    return result


def render_freecad_panel(params: HandleParameters) -> None:
    st.subheader("FreeCAD connection")
    conn = _get_connection()

    connected = conn.is_connected
    status = "● Connected" if connected else "○ Disconnected"
    mode = f" ({conn.mode})" if connected else ""
    st.markdown(f"**Status:** {status}{mode}")
    if conn.last_message:
        st.caption(conn.last_message)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("Connect FreeCAD", use_container_width=True):
            resp = conn.connect()
            if resp.success:
                st.success(resp.message)
            else:
                st.warning(
                    f"{resp.message}. For live viewport updates, run the bridge in FreeCAD:\n\n"
                    f"`runpy.run_path(r'{BRIDGE_SCRIPT}')`"
                )
    with c2:
        if st.button("Create in FreeCAD", use_container_width=True):
            with st.spinner("Exporting STEP and syncing to FreeCAD…"):
                r = _sync_to_freecad(conn, params)
            if r.success:
                st.success(r.message)
                fc = default_fcstd_path(ROOT)
                if fc.exists():
                    st.caption(f"Saved: `{fc}` — open in FreeCAD if the 3D view is empty.")
            else:
                st.error(r.error or r.message)
    with c3:
        if st.button("Update FreeCAD", use_container_width=True):
            with st.spinner("Updating FreeCAD…"):
                r = _sync_to_freecad(conn, params)
            if r.success:
                st.success(r.message)
            else:
                st.error(r.error or r.message)
    with c4:
        if st.button("Save FreeCAD document", use_container_width=True):
            path = default_fcstd_path(ROOT)
            if conn.mode == "http" and conn.client:
                r = conn.client.save_document(str(path))
                st.success(r.message) if r.success else st.error(r.error or r.message)
            elif path.exists():
                st.info(f"Already saved: {path}")
            else:
                st.warning("Sync model first.")
    with c5:
        if st.button("Open export folder", use_container_width=True):
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            st.info(str(EXPORT_DIR.resolve()))

    with st.expander("Live FreeCAD bridge (optional)"):
        st.markdown(
            "**Eenvoudig (aanbevolen):** run eenmalig\n\n"
            "`powershell -File scripts/restart_freecad_bridge.ps1`\n\n"
            "Daarna in Streamlit alleen **Create in FreeCAD** (Connect is automatisch).\n\n"
            "**Met FreeCAD-venster:** Python-console →\n\n"
            f"```python\nimport runpy\nrunpy.run_path(r'{BRIDGE_SCRIPT}')\n```\n\n"
            "Open daarna `projects/work/handle_test/exports/handle_assembly.FCStd` als je geen live sync ziet.\n\n"
            "Niet `http://127.0.0.1:8765` in Chrome openen — dat is geen website."
        )
