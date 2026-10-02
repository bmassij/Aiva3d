"""Lightweight geometry preview (matplotlib wireframe; optional CadQuery VTK show)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import cadquery as cq
import matplotlib.pyplot as plt
import trimesh

import config


def _tessellate(workpiece: cq.Workplane) -> trimesh.Trimesh:
    config.PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    tmp = config.PREVIEW_DIR / "_preview_tmp.stl"
    cq.exporters.export(
        workpiece,
        str(tmp),
        tolerance=config.DEFAULT_MESH_TOLERANCE,
        angularTolerance=config.DEFAULT_MESH_ANGULAR_TOLERANCE,
    )
    mesh = trimesh.load_mesh(str(tmp), process=False)
    tmp.unlink(missing_ok=True)
    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("Preview tessellation failed")
    return mesh


def preview_matplotlib(
    workpiece: cq.Workplane,
    title: str = "CAD preview",
    save_path: Optional[Path] = None,
    show: bool = True,
) -> Path:
    """
    Render a quick 3D triangle mesh view using matplotlib.
    Saves PNG to preview/output when save_path is omitted.
    """
    mesh = _tessellate(workpiece)
    config.PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    if save_path is None:
        save_path = config.PREVIEW_DIR / f"{title.replace(' ', '_').lower()}.png"

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_trisurf(
        mesh.vertices[:, 0],
        mesh.vertices[:, 1],
        mesh.vertices[:, 2],
        triangles=mesh.faces,
        linewidth=0.1,
        alpha=0.9,
    )
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path, dpi=120)
    if show:
        plt.show()
    else:
        plt.close(fig)
    return save_path


def preview_vtk_show(workpiece: cq.Workplane) -> None:
    """Interactive VTK viewer via CadQuery (requires display; may block)."""
    from cadquery import show

    show(workpiece)
