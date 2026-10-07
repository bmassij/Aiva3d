"""Plotly 3D mesh viewer for CadQuery solids."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import cadquery as cq
import plotly.graph_objects as go
import trimesh

import config


def workpiece_to_trimesh(workpiece: cq.Workplane) -> trimesh.Trimesh:
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        cq.exporters.export(
            workpiece,
            str(tmp_path),
            tolerance=min(0.05, config.DEFAULT_MESH_TOLERANCE),
            angularTolerance=config.DEFAULT_MESH_ANGULAR_TOLERANCE,
        )
        mesh = trimesh.load_mesh(str(tmp_path), process=False)
        if not isinstance(mesh, trimesh.Trimesh):
            raise RuntimeError("Tessellation did not produce a Trimesh")
        return mesh
    finally:
        tmp_path.unlink(missing_ok=True)


def plotly_figure_for_meshes(
    meshes: List[Tuple[trimesh.Trimesh, str, str]],
    title: str = "CAD preview",
    opacities: List[float] | None = None,
) -> go.Figure:
    fig = go.Figure()
    all_x = []
    all_y = []
    all_z = []
    for idx, (mesh, color, name) in enumerate(meshes):
        if mesh is None or len(mesh.vertices) == 0:
            continue
        opacity = 0.92 if not opacities else float(opacities[idx])
        v = mesh.vertices
        all_x.append(v[:, 0])
        all_y.append(v[:, 1])
        all_z.append(v[:, 2])
        fig.add_trace(
            go.Mesh3d(
                x=v[:, 0],
                y=v[:, 1],
                z=v[:, 2],
                i=mesh.faces[:, 0],
                j=mesh.faces[:, 1],
                k=mesh.faces[:, 2],
                color=color,
                opacity=max(opacity, 0.85),
                name=name,
                flatshading=True,
                lighting=dict(ambient=0.72, diffuse=0.85, specular=0.15, roughness=0.6),
                lightposition=dict(x=80, y=200, z=120),
                showlegend=True,
            )
        )
    scene: dict = {
        "xaxis_title": "X (mm)",
        "yaxis_title": "Y (mm)",
        "zaxis_title": "Z (mm)",
        "aspectmode": "data",
        "bgcolor": "#f4f4f4",
        "camera": dict(eye=dict(x=1.6, y=-1.7, z=0.95)),
        "xaxis": dict(backgroundcolor="#f4f4f4", gridcolor="#ccc", zerolinecolor="#999"),
        "yaxis": dict(backgroundcolor="#f4f4f4", gridcolor="#ccc", zerolinecolor="#999"),
        "zaxis": dict(backgroundcolor="#f4f4f4", gridcolor="#ccc", zerolinecolor="#999"),
    }
    if all_x:
        import numpy as np

        xs = np.concatenate(all_x)
        ys = np.concatenate(all_y)
        zs = np.concatenate(all_z)
        pad = 12.0
        scene["xaxis"]["range"] = [float(xs.min()) - pad, float(xs.max()) + pad]
        scene["yaxis"]["range"] = [float(ys.min()) - pad, float(ys.max()) + pad]
        scene["zaxis"]["range"] = [float(zs.min()) - pad, float(zs.max()) + pad]
    fig.update_layout(
        title=title,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f4f4f4",
        scene=scene,
        margin=dict(l=0, r=0, t=48, b=0),
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(255,255,255,0.8)"),
    )
    return fig


def figure_from_workpieces(
    parts: List[Tuple],
    title: str = "CAD preview",
) -> go.Figure:
    meshes: List[Tuple[trimesh.Trimesh, str, str]] = []
    opacities: List[float] = []
    for item in parts:
        wp, color, name = item[0], item[1], item[2]
        opacity = float(item[3]) if len(item) > 3 else 0.92
        meshes.append((workpiece_to_trimesh(wp), color, name))
        opacities.append(opacity)
    return plotly_figure_for_meshes(meshes, title=title, opacities=opacities)


def figure_material_section(title: str = "Materialen — hard / VariShore / metaal") -> go.Figure:
    """Cutaway: metal rod + hard inner + half the foam shell, customer material colours."""
    from projects.work.handle_test.clamshell import _split_z
    from projects.work.handle_test.materials import HARD_PRINT, METAL_EXISTING, SOFT_PRINT
    from projects.work.handle_test.model import build
    from projects.work.handle_test.parameters import default_parameters
    from projects.work.handle_test.reference_geometry import build_metal_rod_context

    params = default_parameters()
    hard, soft = build(params)
    metal = build_metal_rod_context(params)
    soft_cut = _split_z(soft, True)
    fig = figure_from_workpieces(
        [
            (metal, METAL_EXISTING["color"], METAL_EXISTING["label"], 1.0),
            (hard, HARD_PRINT["color"], HARD_PRINT["label"], 1.0),
            (soft_cut, SOFT_PRINT["color"], SOFT_PRINT["label"] + " (halve doorsnede)", 0.5),
        ],
        title=title,
    )
    fig.update_layout(
        height=620,
        scene_camera=dict(eye=dict(x=1.6, y=-0.2, z=0.45)),
    )
    return fig


def figure_exploded_clamshell(title: str = "Clamshell — rails en klik") -> go.Figure:
    from projects.work.handle_test.clamshell import exploded_clamshell

    bundle = exploded_clamshell()
    fig = figure_from_workpieces(bundle["workpieces"], title=title)
    for i, path in enumerate(bundle["rail_paths"]):
        xs, ys, zs = zip(*path)
        fig.add_trace(
            go.Scatter3d(
                x=list(xs),
                y=list(ys),
                z=list(zs),
                mode="lines",
                line=dict(color="#c05621", width=8),
                name=f"Inkeping {i + 1}",
            )
        )
    if bundle["click_centers"]:
        xs, ys, zs = zip(*bundle["click_centers"])
        fig.add_trace(
            go.Scatter3d(
                x=list(xs),
                y=list(ys),
                z=list(zs),
                mode="markers+text",
                marker=dict(size=14, color="#e53e3e"),
                text=["haak"] * len(xs),
                textposition="top center",
                name="Haak (klik opzij)",
            )
        )
    fig.update_layout(
        height=640,
        scene_camera=dict(eye=dict(x=1.7, y=-0.35, z=0.55)),
    )
    return fig


def figure_full_handle(title: str = "Hele hendel — kaal metaal (geen tuinslang)") -> go.Figure:
    from projects.work.handle_test.full_handle import build_printable_metal_handle

    metal = build_printable_metal_handle()
    fig = figure_from_workpieces(
        [(metal, "#718096", "D-lus + hub (kaal metaal)", 1.0)],
        title=title,
    )
    fig.update_layout(height=680, scene_camera=dict(eye=dict(x=1.35, y=-1.55, z=0.9)))
    return fig


def figure_side_by_side(
    left_parts: List[Tuple[cq.Workplane, str, str]],
    right_parts: List[Tuple[cq.Workplane, str, str]],
    left_title: str = "Comparison A",
    right_title: str = "Comparison B",
) -> Tuple[go.Figure, go.Figure]:
    return (
        figure_from_workpieces(left_parts, title=left_title),
        figure_from_workpieces(right_parts, title=right_title),
    )
