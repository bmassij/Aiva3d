"""Plotly 3D mesh viewer for CadQuery solids."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

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
            tolerance=config.DEFAULT_MESH_TOLERANCE,
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
) -> go.Figure:
    fig = go.Figure()
    for mesh, color, name in meshes:
        fig.add_trace(
            go.Mesh3d(
                x=mesh.vertices[:, 0],
                y=mesh.vertices[:, 1],
                z=mesh.vertices[:, 2],
                i=mesh.faces[:, 0],
                j=mesh.faces[:, 1],
                k=mesh.faces[:, 2],
                color=color,
                opacity=0.85,
                name=name,
                flatshading=True,
            )
        )
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
    )
    return fig


def figure_from_workpieces(
    parts: List[Tuple[cq.Workplane, str, str]],
    title: str = "CAD preview",
) -> go.Figure:
    meshes = [(workpiece_to_trimesh(wp), color, name) for wp, color, name in parts]
    return plotly_figure_for_meshes(meshes, title=title)


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
