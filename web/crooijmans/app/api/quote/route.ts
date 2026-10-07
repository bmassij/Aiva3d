import { NextRequest, NextResponse } from "next/server";

const QUOTE_API = process.env.QUOTE_API_URL ?? process.env.NEXT_PUBLIC_QUOTE_API_URL ?? "";

/**
 * Pilot 3: proxy naar Python quote-engine wanneer QUOTE_API_URL gezet is.
 * Zonder backend: metadata-only response (geen echte prijs nog).
 */
export async function POST(req: NextRequest) {
  const form = await req.formData();
  const file = form.get("file");
  if (!file || !(file instanceof File)) {
    return NextResponse.json({ ok: false, error: "Geen 3MF-bestand ontvangen." }, { status: 400 });
  }
  const name = file.name.toLowerCase();
  if (!name.endsWith(".3mf") && !name.endsWith(".stl")) {
    return NextResponse.json(
      { ok: false, error: "Alleen .3mf of .stl (tijdelijk) voor de pilot." },
      { status: 400 },
    );
  }

  const quantity = form.get("quantity");
  const materialProfile = form.get("material_profile");
  const machineProfile = form.get("machine_profile");
  const pricingProfile = form.get("pricing_profile");

  if (QUOTE_API) {
    const upstream = new FormData();
    upstream.append("file", file);
    if (quantity != null) upstream.append("quantity", String(quantity));
    if (materialProfile != null) upstream.append("material_profile", String(materialProfile));
    if (machineProfile != null) upstream.append("machine_profile", String(machineProfile));
    if (pricingProfile != null) upstream.append("pricing_profile", String(pricingProfile));
    try {
      const res = await fetch(`${QUOTE_API.replace(/\/$/, "")}/quote`, {
        method: "POST",
        body: upstream,
      });
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    } catch {
      return NextResponse.json(
        { ok: false, error: "Quote-backend niet bereikbaar (QUOTE_API_URL)." },
        { status: 502 },
      );
    }
  }

  const bytes = file.size;
  return NextResponse.json({
    ok: true,
    mode: "preview_only",
    message:
      "Calculator-UI op Vercel. Gewicht/tijd/kosten/PDF komen uit de Python quote-engine (nog koppelen via QUOTE_API_URL).",
    file: { name: file.name, bytes, kb: Math.round(bytes / 1024) },
    quote: {
      weight_g: null,
      materials: [],
      print_time_min: null,
      cost_eur: null,
      margin_eur: null,
      total_eur: null,
      pdf_url: null,
    },
    next_steps: [
      "Deploy quote API (FastAPI) naast Aiva3D",
      "Parse 3MF meshes → volume per filament",
      "Tarief + marge → PDF",
    ],
  });
}
