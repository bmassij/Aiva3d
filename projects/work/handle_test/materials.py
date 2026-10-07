"""Print/reference materials as specified by the customer (hard + VariShore foam)."""

from __future__ import annotations

from typing import Dict

# Customer: "hard en zacht geprint ... Met varioshore. Schuim en neet schuim"
HARD_PRINT = {
    "id": "hard_print",
    "label": "Hard print (niet-schuim, binnen)",
    "color": "#2b6cb0",
    "role": "Structural inner sleeve around the metal rod. Printed rigid (not foam).",
}
SOFT_PRINT = {
    "id": "varishore_foam",
    "label": "Zacht VariShore (schuim, buiten)",
    "color": "#38a169",
    "role": "Foam-like outer grip. Printed VariShore; carries hand contact.",
}
METAL_EXISTING = {
    "id": "existing_metal",
    "label": "Bestaand metaal (niet printen)",
    "color": "#718096",
    "role": "Round steel rod of the D-loop. Context only; not a printed part.",
}
CLICK_HARD = {
    "id": "click_hard",
    "label": "Klik/geleider (hard, niet-schuim)",
    "color": "#c05621",
    "role": "Short slider in a notch; click sideways into the L-pocket to lock.",
}

MATERIALS: Dict[str, dict] = {
    HARD_PRINT["id"]: HARD_PRINT,
    SOFT_PRINT["id"]: SOFT_PRINT,
    METAL_EXISTING["id"]: METAL_EXISTING,
    CLICK_HARD["id"]: CLICK_HARD,
}


def hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.strip().lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


def legend_markdown_nl() -> str:
    return (
        "**Materialen (zoals opgegeven: hard + zacht VariShore)**\n\n"
        f"- **{HARD_PRINT['label']}** — kleur in 3D: blauw. {HARD_PRINT['role']}\n"
        f"- **{SOFT_PRINT['label']}** — kleur in 3D: groen. {SOFT_PRINT['role']}\n"
        f"- **{METAL_EXISTING['label']}** — kleur in 3D: grijs. {METAL_EXISTING['role']}\n"
        f"- **{CLICK_HARD['label']}** — kleur in 3D: oranje. {CLICK_HARD['role']}\n"
    )
