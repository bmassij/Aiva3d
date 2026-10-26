"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { bitmapToPreviewUrl, fileToImageData, imageDataToBitmap } from "@/lib/image-to-bitmap";
import { buildPrintModel, type PrintModel } from "@/lib/bitmap-to-mesh";
import { ModelViewer } from "@/components/ModelViewer";
import { downloadBytes } from "@/lib/download";
import { write3mf } from "@/lib/write-3mf";
import { writeBinaryStl } from "@/lib/write-stl";

const DEMO_LOGO = "/demo-logo.svg";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [imageData, setImageData] = useState<ImageData | null>(null);
  const [invert, setInvert] = useState(false);
  const [threshold, setThreshold] = useState<number | null>(null);
  const [sizeMm, setSizeMm] = useState(40);
  const [baseColor, setBaseColor] = useState("#f3f1eb");
  const [logoColor, setLogoColor] = useState("#0e3d3a");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [previewModel, setPreviewModel] = useState<PrintModel | null>(null);
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    return () => {
      if (logoUrl?.startsWith("blob:")) URL.revokeObjectURL(logoUrl);
    };
  }, [logoUrl]);

  const loadSource = useCallback(async (source: File | string) => {
    setError(null);
    setStatus(null);
    setThreshold(null);
    const data = await fileToImageData(source);
    setImageData(data);
    if (typeof source !== "string") {
      const url = URL.createObjectURL(source);
      setLogoUrl((prev) => {
        if (prev?.startsWith("blob:")) URL.revokeObjectURL(prev);
        return url;
      });
      setFile(source);
    } else {
      setFile(null);
      setLogoUrl(source);
    }
  }, []);

  const onLogo = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const next = e.target.files?.[0];
      if (!next) return;
      try {
        await loadSource(next);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload mislukt.");
      }
    },
    [loadSource],
  );

  const bitmap = useMemo(() => {
    if (!imageData) return null;
    return imageDataToBitmap(imageData, {
      invert,
      threshold: threshold ?? undefined,
    });
  }, [imageData, invert, threshold]);

  const maskUrl = useMemo(() => {
    if (!bitmap) return null;
    return bitmapToPreviewUrl(bitmap, logoColor, baseColor);
  }, [bitmap, logoColor, baseColor]);

  useEffect(() => {
    if (!bitmap) {
      setPreviewModel(null);
      setPreviewing(false);
      return;
    }
    let cancelled = false;
    setPreviewing(true);
    const timer = window.setTimeout(() => {
      try {
        const model = buildPrintModel(bitmap, { sizeMm, baseColor, logoColor });
        if (!cancelled) {
          setPreviewModel(model);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setPreviewModel(null);
          setError(err instanceof Error ? err.message : "3D-model kon niet worden gebouwd.");
        }
      } finally {
        if (!cancelled) setPreviewing(false);
      }
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [bitmap, sizeMm, baseColor, logoColor]);

  const generate = useCallback(
    async (format: "3mf" | "stl") => {
      if (!bitmap) {
        setError("Upload eerst het logo van het bedrijf of de persoon.");
        return;
      }
      setBusy(true);
      setError(null);
      setStatus(null);
      try {
        const model = buildPrintModel(bitmap, {
          sizeMm,
          baseColor,
          logoColor,
        });
        const stamp = new Date().toISOString().slice(0, 10);
        if (format === "3mf") {
          downloadBytes(`logo-hanger-${stamp}.3mf`, write3mf(model), "model/3mf");
        } else {
          downloadBytes(`logo-hanger-${stamp}.stl`, writeBinaryStl(model), "model/stl");
        }
        setStatus(
          `Printbestand klaar: ${model.widthMm}×${model.heightMm} mm, logo in reliëf, gat voor de ring. Open in Bambu, Orca of Prusa.`,
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Genereren mislukt.");
      } finally {
        setBusy(false);
      }
    },
    [bitmap, sizeMm, baseColor, logoColor],
  );

  return (
    <main>
      <h1>Print uw logo</h1>
      <p className="lead">
        Voor bedrijven en personen: upload het logo, kies de kleuren, en download een
        printbare hanger. Geen handvat, geen CAD-programma — het bestand is klaar voor de
        3D-printer.
      </p>

      <div className="card">
        <label htmlFor="logo">Logo (PNG, JPG, SVG of foto van het logo)</label>
        <input id="logo" type="file" accept="image/*" onChange={onLogo} />
        <button type="button" className="secondary" onClick={() => void loadSource(DEMO_LOGO)}>
          Voorbeeldlogo laden
        </button>
        <div className="row" style={{ marginTop: "1rem" }}>
          <div className="preview preview-light">
            {logoUrl ? <img src={logoUrl} alt="Geüpload logo" /> : <span>Nog geen logo</span>}
          </div>
          <div className="preview">
            {maskUrl ? <img src={maskUrl} alt="Zo wordt het logo geprint" /> : <span>Printvorm</span>}
          </div>
        </div>
        <p className="hint">Links het aangeleverde logo, rechts hoe het reliëf op de hanger komt.</p>
      </div>

      <div className="card">
        <label>3D-model</label>
        {previewModel ? (
          <ModelViewer model={previewModel} />
        ) : (
          <div className="viewer viewer-empty">
            {previewing
              ? "3D-model wordt opgebouwd…"
              : "Upload een logo om het 3D-model te zien."}
          </div>
        )}
        <p className="hint">Sleep om te draaien, scroll om te zoomen. Dit is het bestand dat je downloadt.</p>
      </div>

      <div className="card">
        <label htmlFor="size">Maat (mm, tot 40 × 40)</label>
        <input
          id="size"
          type="range"
          min={20}
          max={40}
          value={sizeMm}
          onChange={(e) => setSizeMm(Number(e.target.value))}
        />
        <p className="hint">{sizeMm} × {sizeMm} mm · plaat 2 mm · logo 1,2 mm hoog · ringgat</p>

        <label className="check">
          <input type="checkbox" checked={invert} onChange={(e) => setInvert(e.target.checked)} />
          Logo omdraaien (licht logo op donkere achtergrond)
        </label>

        <label htmlFor="threshold">Hoeveel van de foto wordt logo</label>
        <input
          id="threshold"
          type="range"
          min={20}
          max={230}
          value={threshold ?? bitmap?.threshold ?? 128}
          onChange={(e) => setThreshold(Number(e.target.value))}
        />
      </div>

      <div className="card row">
        <div>
          <label htmlFor="base">Kleur van de plaat</label>
          <input id="base" type="color" value={baseColor} onChange={(e) => setBaseColor(e.target.value)} />
        </div>
        <div>
          <label htmlFor="logoColor">Kleur van het logo</label>
          <input id="logoColor" type="color" value={logoColor} onChange={(e) => setLogoColor(e.target.value)} />
        </div>
      </div>

      <div className="actions">
        <button type="button" className="primary" disabled={!bitmap || busy} onClick={() => void generate("3mf")}>
          {busy ? "Bezig…" : "Download 3MF"}
        </button>
        <button type="button" className="secondary" disabled={!bitmap || busy} onClick={() => void generate("stl")}>
          Download STL
        </button>
      </div>

      {error ? <div className="status warn">{error}</div> : null}
      {status ? <div className="status ok">{status}</div> : null}

      <footer>
        Het 3D-model wordt in de browser gemaakt van het logo. Geschikt voor NFC-sleutelhangers en
        relatiegeschenken tot 40 × 40 mm.
      </footer>
    </main>
  );
}
