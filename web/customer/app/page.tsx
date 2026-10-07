"use client";

import { useCallback, useEffect, useState } from "react";

const CAD_API = process.env.NEXT_PUBLIC_CAD_API_URL ?? "";

export default function Home() {
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [hardColor, setHardColor] = useState("#4a90d9");
  const [softColor, setSoftColor] = useState("#7ed957");
  const [health, setHealth] = useState<string>("checking…");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setHealth(d.ok ? `OK — ${d.service} ${d.version}` : "degraded"))
      .catch(() => setHealth("offline"));
  }, []);

  const onLogo = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setLogoUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
  }, []);

  const onExport = () => {
    if (CAD_API) {
      window.open(CAD_API, "_blank", "noopener,noreferrer");
      return;
    }
    alert(
      "3MF-generatie draait op de CAD-server (Streamlit/API). Zet NEXT_PUBLIC_CAD_API_URL in Vercel naar je backend wanneer die live staat.",
    );
  };

  return (
    <main>
      <h1>Aiva3D · Klantportaal</h1>
      <p className="lead">
        <strong>PNG → 3MF</strong> (roadmap): upload logo/afbeelding, kies kleuren — preview hier; echte geometrie en
        3MF-export via de Python CAD-backend (CadQuery draait niet op Vercel).
      </p>

      <div className="card status warn" style={{ marginBottom: "1rem" }}>
        <strong>Review-build voor klant</strong> — laat weten wat je van de flow, teksten en preview vindt. 3MF-export
        volgt zodra de CAD-API online staat.
      </div>

      <div className="card">
        <label htmlFor="logo">Logo (PNG/SVG/JPG)</label>
        <input id="logo" type="file" accept="image/*" onChange={onLogo} />
        <button
          type="button"
          className="secondary"
          onClick={() => setLogoUrl("/demo-logo.jpg")}
          style={{ marginBottom: "0.75rem" }}
        >
          Demo logo laden
        </button>
        <div className="preview" style={{ borderColor: softColor }}>
          {logoUrl ? (
            <img src={logoUrl} alt="Logo preview" />
          ) : (
            <span style={{ color: "#6b7d94" }}>Geen logo</span>
          )}
        </div>
      </div>

      <div className="card row">
        <div>
          <label htmlFor="hard">Hard core kleur (preview)</label>
          <input
            id="hard"
            type="color"
            value={hardColor}
            onChange={(e) => setHardColor(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="soft">Soft grip kleur (preview)</label>
          <input
            id="soft"
            type="color"
            value={softColor}
            onChange={(e) => setSoftColor(e.target.value)}
          />
        </div>
      </div>

      <div
        className="card"
        style={{
          background: `linear-gradient(135deg, ${hardColor}33 0%, ${softColor}44 100%)`,
        }}
      >
        <p style={{ margin: 0 }}>
          <strong>Grip preview tint</strong> — echte geometrie komt uit Aiva3D CAD (110 mm × 30 mm productie).
        </p>
      </div>

      <button type="button" className="primary" onClick={onExport}>
        Open CAD / 3MF export
      </button>

      <div className={`status ${health.startsWith("OK") ? "ok" : "warn"}`}>
        Vercel deploy: {health}
        {CAD_API ? ` · API: ${CAD_API}` : " · NEXT_PUBLIC_CAD_API_URL niet gezet"}
      </div>

      <footer>
        Repo: GitHub bmassij/Aiva3d · Lokale CAD: Streamlit op poort 8501/8502
      </footer>
    </main>
  );
}
