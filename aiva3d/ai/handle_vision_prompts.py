"""Prompts for handle_test reference photo analysis (vision only)."""

from __future__ import annotations

HANDLE_VISION_SYSTEM = (
    "You are a mechanical CAD assistant analyzing reference photos of a metal D-loop "
    "handle on 10 mm graph paper. Be precise about what is existing metal versus what "
    "must be 3D-printed (hard inner sleeve + soft outer grip). Count grid squares where "
    "visible. State uncertainty clearly. Do not invent precise mm values if the grid is "
    "unclear — give square counts first, then mm (1 square = 10 mm)."
)

HANDLE_PAIR_USER_TEMPLATE = """We are reverse-engineering a customer grip for Aiva3D.

Context:
- Graph paper: each blue square is 10 mm × 10 mm.
- Existing product: metal D-loop handle (NOT printed).
- Customer print ONLY: hard inner sleeve + soft outer shell on the **outer/right leg** of the loop — a **short curved segment**, NOT the full oval height.
- Photo 1: bare metal — use this for **metal rod diameter** (~1 grid square thick).
- Photo 2: translucent mesh hose (tuinslang) on part of the outer arc — measure **only the mesh sleeve**, not the whole D-loop, not fingers, not empty paper.

CRITICAL:
- Do NOT report the full oval height (~15–17 squares) as grip print length.
- The printable grip follows the **mesh sleeve** on photo 2: count vertical grid squares along the sleeve outer span (often ~13 squares including partial end cells; ~11 fully filled).
- Sleeve width is about **2–3 grid squares**, not the width of the entire loop interior.

Answer in Dutch (Nederlands), structured with these headings:

## Wat is metaal (bestaand)
## Wat moet geprint worden (hard + zacht)
## Tuinslang / mesh op foto 2 (alleen dit stuk meten)
## Grid-metingen (vakjes, daarna mm) — sleeve apart van hele loop
## Vorm (boog op buitenste been, centerlijn)
## Onzekerheden
## Ergonomie handvat (dikte, pijn, vorm — algemene richtlijnen)
## Aanbeveling voor CAD (kort)

Under **Ergonomie handvat**, discuss in Dutch:
- Is the sleeve OD appropriate for a **power grip** (typical cylindrical handle band ~30–45 mm)?
- Would **slightly larger nominal OD** or **thicker soft foam** reduce pressure pain (VariShore compresses)?
- **Shape**: curved segment following outer leg; rounded ends; not sharp edges.
- Separate **photo truth** from **comfort recommendation** — do not replace grid counts with guesses.

Images attached in order:
1. {photo1_name} — bare metal
2. {photo2_name} — mesh sleeve
"""

METAL_LOOP_SILHOUETTE_SYSTEM = (
    "You reverse-engineer a photographed steel D-loop on 10 mm graph paper. "
    "Describe the true silhouette. Do not simplify to a running-track/stadium "
    "(straight rails + semicircle ends) unless the photo actually shows that."
)

METAL_LOOP_SILHOUETTE_TEMPLATE = """This is the BARE METAL D-loop only (no garden-hose sleeve).

Graph paper: 1 square = 10 mm.

Task: map the REAL shape so CAD can copy the photo — not invent a simpler primitive.

Answer in Dutch with these headings:

## Silhouet (ovaal vs renbaan)
Is the inner opening a true oval/ellipse (bowed long sides), or a stadium (parallel straight legs + round ends)? Say which, with evidence from the grid.

## Linkerbeen en zeskant
How do the top-left and bottom-left legs meet the hexagonal hub? Do they pinch/weld INTO the hex, or is there a full left rail with a separate block stuck on the outside?

## Zeskant en as
- Hex outline in this plan photo (XY): count squares across flats.
- Is the hex a hexagon in the same plane as the loop (we see 6 sides), not a side-view box?
- Square shaft: direction and approx squares.

## Grid (vakjes → mm)
- Outer loop height (top outer to bottom outer)
- Outer loop width (left outer rod to right outer rod), excluding shaft if possible
- Hub face to right outer
- Rod thickness (one square ~10 mm?)

## CAD-regels (kort)
Bullet list of constraints the solid MUST follow to match THIS photo. No stadium unless you measured straights.

File: {photo_name}
"""


HANDLE_SINGLE_USER_TEMPLATE = """Analyze this handle reference photo on 10 mm grid paper.

Context: metal D-loop; printable part is hard+soft grip on the rod, not the whole metal loop.

Answer in Dutch with headings:
## Metaal vs print
## Grid-metingen (vakjes → mm)
## Vorm
## Onzekerheden
## CAD-aanbeveling

File: {photo_name}
"""
