"""Orthographic + isometric drawings of the production grip (mm)."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from preview.viewer import _tessellate
from projects.work.handle_test.design_constants import (
    GRIP_LENGTH_MM,
    GRIP_OUTER_DIAMETER_MM,
    HARD_CORE_DIAMETER_MM,
)
from projects.work.handle_test.model import build, build_assembly_compound
from projects.work.handle_test.parameters import default_parameters
from projects.work.handle_test.validation import bounding_box_mm, validate_handle_pair

OUT = ROOT / "projects" / "work" / "handle_test" / "exports" / "drawings"


def _equal_aspect(ax, xs, ys) -> None:
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.6)
    pad = 8.0
    ax.set_xlim(float(np.min(xs)) - pad, float(np.max(xs)) + pad)
    ax.set_ylim(float(np.min(ys)) - pad, float(np.max(ys)) + pad)


def _dim_h(ax, x0: float, x1: float, y: float, text: str) -> None:
    ax.annotate(
        "",
        xy=(x1, y),
        xytext=(x0, y),
        arrowprops=dict(arrowstyle="<->", color="#222", lw=1.1),
    )
    ax.text((x0 + x1) / 2.0, y + 1.6, text, ha="center", va="bottom", fontsize=8, color="#111")


def _dim_v(ax, y0: float, y1: float, x: float, text: str) -> None:
    ax.annotate(
        "",
        xy=(x, y1),
        xytext=(x, y0),
        arrowprops=dict(arrowstyle="<->", color="#222", lw=1.1),
    )
    ax.text(x + 2.0, (y0 + y1) / 2.0, text, ha="left", va="center", fontsize=8, color="#111")


def _scatter_view(ax, verts: np.ndarray, i: int, j: int, color: str, alpha: float = 0.35, s: float = 0.4) -> None:
    ax.scatter(verts[:, i], verts[:, j], s=s, c=color, alpha=alpha, linewidths=0, rasterized=True)


def render_drawings() -> dict[str, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    params = default_parameters()
    hard, soft = build(params)
    stats = validate_handle_pair(hard, soft, params)
    hard_m = _tessellate(hard)
    soft_m = _tessellate(soft)
    hv, sv = hard_m.vertices, soft_m.vertices
    bb = bounding_box_mm(soft)

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 6.2))
    fig.suptitle(
        f"Handle grip — print pair  |  L={GRIP_LENGTH_MM:.0f} mm  OD={GRIP_OUTER_DIAMETER_MM:.0f} mm  "
        f"core Ø={HARD_CORE_DIAMETER_MM:.1f} mm",
        fontsize=12,
    )

    ax = axes[0]
    _scatter_view(ax, sv, 0, 1, "#7aa6c2", 0.28)
    _scatter_view(ax, hv, 0, 1, "#c45c26", 0.55)
    cl = np.array(params.centerline_points_mm)
    ax.plot(cl[:, 0], cl[:, 1], color="#1a1a1a", lw=1.2, label="centerline")
    _equal_aspect(ax, np.concatenate([sv[:, 0], hv[:, 0]]), np.concatenate([sv[:, 1], hv[:, 1]]))
    ax.set_xlabel("X (mm)  — outward")
    ax.set_ylabel("Y (mm)  — along D-leg")
    ax.set_title("Plan (XY) — matches photo")
    _dim_v(ax, bb["ymin"], bb["ymax"], bb["xmax"] + 6.0, f"{bb['size_y']:.0f}")
    ax.legend(loc="lower right", fontsize=7, frameon=False)

    ax = axes[1]
    _scatter_view(ax, sv, 2, 1, "#7aa6c2", 0.28)
    _scatter_view(ax, hv, 2, 1, "#c45c26", 0.55)
    _equal_aspect(ax, np.concatenate([sv[:, 2], hv[:, 2]]), np.concatenate([sv[:, 1], hv[:, 1]]))
    ax.set_xlabel("Z (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title("Side (ZY)")
    _dim_h(ax, bb["zmin"], bb["zmax"], bb["ymin"] - 6.0, f"OD {bb['size_z']:.0f}")

    ax = axes[2]
    iso = np.column_stack(
        (
            sv[:, 0] * 0.86 + sv[:, 2] * 0.50,
            sv[:, 1] * 0.92 - sv[:, 0] * 0.18 + sv[:, 2] * 0.22,
        )
    )
    iso_h = np.column_stack(
        (
            hv[:, 0] * 0.86 + hv[:, 2] * 0.50,
            hv[:, 1] * 0.92 - hv[:, 0] * 0.18 + hv[:, 2] * 0.22,
        )
    )
    ax.scatter(iso[:, 0], iso[:, 1], s=0.35, c="#7aa6c2", alpha=0.28, linewidths=0, rasterized=True)
    ax.scatter(iso_h[:, 0], iso_h[:, 1], s=0.4, c="#c45c26", alpha=0.55, linewidths=0, rasterized=True)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title("Isometric")
    ax.set_xlabel("mm")
    ax.set_ylabel("mm")
    ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.5)

    fig.tight_layout()
    sheet = OUT / "handle_drawing_sheet.png"
    fig.savefig(sheet, dpi=160)
    plt.close(fig)

    fig = plt.figure(figsize=(7.2, 9.0))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_trisurf(
        soft_m.vertices[:, 0],
        soft_m.vertices[:, 1],
        soft_m.vertices[:, 2],
        triangles=soft_m.faces,
        color=(0.48, 0.66, 0.78, 0.55),
        linewidth=0.02,
        shade=True,
    )
    ax.plot_trisurf(
        hard_m.vertices[:, 0],
        hard_m.vertices[:, 1],
        hard_m.vertices[:, 2],
        triangles=hard_m.faces,
        color=(0.78, 0.38, 0.16, 0.92),
        linewidth=0.02,
        shade=True,
    )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Soft shell (blue) + hard core (orange)")
    try:
        ax.set_box_aspect((bb["size_x"], bb["size_y"], bb["size_z"]))
    except Exception:
        pass
    iso_path = OUT / "handle_isometric.png"
    fig.savefig(iso_path, dpi=150)
    plt.close(fig)

    assembly = build_assembly_compound(params)
    from preview.viewer import preview_matplotlib

    preview_matplotlib(assembly, title="handle_assembly", save_path=OUT / "handle_assembly_preview.png", show=False)

    from projects.work.handle_test.clamshell import exploded_clamshell, build_clamshell
    from ui.mesh_viewer import figure_exploded_clamshell

    bundle = exploded_clamshell()
    fig3 = plt.figure(figsize=(9.5, 8.0))
    ax3 = fig3.add_subplot(111, projection="3d")
    colors = {}
    for wp, hexcol, name, op in bundle["workpieces"]:
        mesh = _tessellate(wp)
        from matplotlib.colors import to_rgba

        ax3.plot_trisurf(
            mesh.vertices[:, 0],
            mesh.vertices[:, 1],
            mesh.vertices[:, 2],
            triangles=mesh.faces,
            color=to_rgba(hexcol, alpha=max(op, 0.35)),
            linewidth=0.0,
            shade=True,
        )
    for path in bundle["rail_paths"]:
        arr = np.array(path)
        ax3.plot(arr[:, 0], arr[:, 1], arr[:, 2], color="#ffdd33", lw=2.4, label="inkeping")
    clicks = np.array(bundle["click_centers"])
    if len(clicks):
        ax3.scatter(clicks[:, 0], clicks[:, 1], clicks[:, 2], c="#ff2d8a", s=90, depthshade=True, label="haak")
        for i, (x, y, z) in enumerate(clicks):
            ax3.text(x, y, z + 4.0, f"haak {i + 1}", color="#ff2d8a", fontsize=8)
    ax3.set_xlabel("X (mm)")
    ax3.set_ylabel("Y (mm)")
    ax3.set_zlabel("Z (mm)")
    ax3.set_title("Materialen: blauw=hard, groen=VariShore, oranje=slider, rood=haak")
    ax3.view_init(elev=18, azim=-70)
    handles, labels = ax3.get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    ax3.legend(uniq.values(), uniq.keys(), loc="upper left", fontsize=8)
    fig3.tight_layout()
    exploded_png = OUT / "handle_clamshell_exploded.png"
    fig3.savefig(exploded_png, dpi=160)
    plt.close(fig3)

    html_path = OUT / "handle_clamshell_3d.html"
    figure_exploded_clamshell().write_html(str(html_path), include_plotlyjs=True)

    from ui.mesh_viewer import figure_material_section

    mat_html = OUT / "handle_materials_3d.html"
    figure_material_section().write_html(str(mat_html), include_plotlyjs=True)

    shells = build_clamshell(params)
    print_parts = [
        (shells.hard_plus, "#2b6cb0", "1  Hard +Z", "Niet-schuim / hard filament"),
        (shells.hard_minus, "#2b6cb0", "2  Hard −Z", "Niet-schuim / hard filament"),
        (shells.soft_plus, "#38a169", "3  Soft +Z", "VariShore — L-inkepingen"),
        (shells.soft_minus, "#38a169", "4  Soft −Z", "VariShore — kleine sliders + haak"),
    ]
    figp, axes_p = plt.subplots(2, 2, figsize=(11.0, 12.0))
    figp.suptitle(
        "Printtekening — 4 helften (niet de complete staaf printen)\n"
        f"L={GRIP_LENGTH_MM:.0f} mm  OD={GRIP_OUTER_DIAMETER_MM:.0f} mm  |  "
        "Schuif +Z op −Z langs de greep; bestaande metalen D-lus niet printen",
        fontsize=11,
    )
    for axp, (wp, color, title, material) in zip(axes_p.ravel(), print_parts):
        mesh = _tessellate(wp)
        v = mesh.vertices
        _scatter_view(axp, v, 0, 1, color, 0.45, 0.5)
        _equal_aspect(axp, v[:, 0], v[:, 1])
        axp.set_title(f"{title}\n{material}", fontsize=10)
        axp.set_xlabel("X (mm)")
        axp.set_ylabel("Y (mm)")
    figp.tight_layout()
    print_sheet = OUT / "handle_print_sheet.png"
    figp.savefig(print_sheet, dpi=160)
    plt.close(figp)

    print_readme = OUT.parent / "print" / "PRINT.md"
    print_readme.parent.mkdir(parents=True, exist_ok=True)
    print_readme.write_text(
        "\n".join(
            [
                "# Print — clamshell greep",
                "",
                "Niet printen: `handle_complete.*` (dat is de gesloten montage, inclusief overlap).",
                "Niet printen: de bestaande metalen D-lus.",
                "",
                "| Bestand | Materiaal | Opmerking |",
                "|---|---|---|",
                "| `01_hard_plus.stl` | hard / niet-schuim | +Z helft kern |",
                "| `02_hard_minus.stl` | hard / niet-schuim | −Z helft kern |",
                "| `03_soft_plus_varishore.stl` | VariShore schuim | +Z mantel, L-inkepingen |",
                "| `04_soft_minus_varishore_rails.stl` | VariShore schuim | −Z mantel, sliders + haak |",
                "",
                "Montage: −Z om de staaf leggen, +Z erop schuiven tot de klik. Eenheden: mm.",
                "",
                "Tekening: `exports/drawings/handle_print_sheet.png`",
                "Uit elkaar in 3D: `exports/drawings/handle_clamshell_3d.html`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    summary = {
        "drawing_sheet": str(sheet),
        "isometric": str(iso_path),
        "clamshell_exploded_png": str(exploded_png),
        "clamshell_exploded_html": str(html_path),
        "materials_html": str(mat_html),
        "print_sheet": str(print_sheet),
        "centerline_mm": params.centerline_points_mm,
        "validation_pass": stats.get("all_checks_pass"),
        "soft_bbox": bb,
        "hard_bbox": bounding_box_mm(hard),
    }
    (OUT / "drawing_summary.json").write_text(
        __import__("json").dumps(summary, indent=2),
        encoding="utf-8",
    )
    from projects.work.handle_test.full_handle import build_printable_metal_handle, photo_centerline_xy

    metal = build_printable_metal_handle()
    mv = _tessellate(metal).vertices
    cl = np.array(photo_centerline_xy())
    figm, axm = plt.subplots(figsize=(5.2, 9.0))
    axm.scatter(mv[:, 0], mv[:, 1], s=0.35, c="#444", alpha=0.35, linewidths=0, rasterized=True)
    axm.plot(cl[:, 0], cl[:, 1], color="#e85d04", lw=1.4, label="foto-centerlijn")
    axm.set_title("Kaal metaal — ovaal van de foto (geen renbaan)")
    axm.set_xlabel("X (mm)")
    axm.set_ylabel("Y (mm)")
    axm.legend(loc="upper right", fontsize=8)
    _equal_aspect(axm, mv[:, 0], mv[:, 1])
    figm.tight_layout()
    bare_png = OUT / "handle_bare_metal.png"
    figm.savefig(bare_png, dpi=160)
    plt.close(figm)
    summary["bare_metal"] = str(bare_png)

    print(__import__("json").dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    render_drawings()
