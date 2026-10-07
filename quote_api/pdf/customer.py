"""Customer-facing quote PDF (no internal cost or margin)."""

from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from quote_api.schemas import QuoteAnalysis


def render_customer_pdf(
    analysis: QuoteAnalysis,
    *,
    quote_number: str,
    notes: str = "",
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(25 * mm, y, "Crooijmans — Offerte (indicatie)")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, f"Offertenr.: {quote_number}")
    y -= 5 * mm
    c.drawString(25 * mm, y, f"Datum: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "Product")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    lines = [
        f"Bestand: {analysis.filename}",
        f"Aantal: {analysis.quantity}",
        f"Objecten: {analysis.object_count}",
        f"Gewicht (totaal): {analysis.weight_g} g",
        f"Geschatte printtijd: {analysis.print_time_minutes} min ({analysis.print_time_note})",
    ]
    if analysis.materials:
        mat_txt = ", ".join(f"{m.label} ({m.weight_g} g)" for m in analysis.materials)
        lines.append(f"Materialen: {mat_txt}")
    for line in lines:
        c.drawString(25 * mm, y, line)
        y -= 5 * mm

    y -= 5 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "Prijs")
    y -= 6 * mm
    c.setFont("Helvetica", 11)
    c.drawString(25 * mm, y, f"Totaal: {analysis.currency} {analysis.sale_price:.2f}")
    y -= 8 * mm

    c.setFont("Helvetica", 8)
    c.drawString(
        25 * mm,
        y,
        "Indicatieve offerte. Definitieve prijs kan afwijken na productiecontrole.",
    )
    if notes:
        y -= 5 * mm
        c.drawString(25 * mm, y, f"Opmerkingen: {notes[:200]}")

    c.showPage()
    c.save()
    return buf.getvalue()
