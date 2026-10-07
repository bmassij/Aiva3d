"use client";



import { useCallback, useEffect, useState } from "react";



type QuoteResponse = {

  ok: boolean;

  mode?: string;

  message?: string;

  filename?: string;

  file?: { name: string; bytes: number; kb: number };

  object_count?: number;

  objects?: { name: string; weight_g: number; material_label?: string | null }[];

  materials?: { label: string; weight_g: number }[];

  weight_g?: number;

  print_time_minutes?: number;

  print_time_note?: string;

  cost_price?: number;

  margin_percent?: number;

  sale_price?: number;

  currency?: string;

  profiles_note?: string;

  quote?: {

    weight_g: number | null;

    print_time_min: number | null;

    cost_eur: number | null;

    margin_eur: number | null;

    total_eur: number | null;

    pdf_url: string | null;

  };

  error?: string;

};



export default function Home() {

  const [file, setFile] = useState<File | null>(null);

  const [health, setHealth] = useState("checking…");
  const [quoteBackend, setQuoteBackend] = useState<"connected" | "preview_only" | "unknown">(
    "unknown",
  );

  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState<QuoteResponse | null>(null);



  useEffect(() => {

    fetch("/api/health")

      .then((r) => r.json())

      .then((d) => {
        setHealth(d.ok ? `OK — ${d.service}` : "degraded");
        if (d.quote_backend === "connected" || d.quote_backend === "preview_only") {
          setQuoteBackend(d.quote_backend);
        }
      })

      .catch(() => setHealth("offline"));

  }, []);



  const onFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {

    const f = e.target.files?.[0];

    setFile(f ?? null);

    setResult(null);

  }, []);



  const onQuote = async () => {

    if (!file) return;

    setLoading(true);

    setResult(null);

    try {

      const body = new FormData();

      body.append("file", file);

      const res = await fetch("/api/quote", { method: "POST", body });

      const data = (await res.json()) as QuoteResponse;

      setResult(data);

    } catch {

      setResult({ ok: false, error: "Netwerkfout bij offerte-aanvraag." });

    } finally {

      setLoading(false);

    }

  };



  const weight =

    result?.weight_g ?? result?.quote?.weight_g ?? null;

  const printMin =

    result?.print_time_minutes ?? result?.quote?.print_time_min ?? null;

  const total =

    result?.sale_price ?? result?.quote?.total_eur ?? null;

  const cost = result?.cost_price ?? result?.quote?.cost_eur ?? null;



  return (

    <main>

      <h1>Crooijmans · 3D-print calculator</h1>

      <p className="lead">
        Pilot 3: upload <strong>3MF</strong> → gewicht, materiaal, printtijd, kosten, marge → offerte-PDF.
        Deze pagina draait op <strong>Vercel</strong>; zware berekening komt uit de <strong>Python quote-API</strong>.
      </p>

      <div className="card status warn" style={{ marginBottom: "1rem" }}>
        <strong>Review-build</strong> — feedback op layout en flow is welkom. Geen productieprijzen; tarieven zijn
        development-default tot Crooijmans ze invult.
        {quoteBackend === "preview_only" && (
          <>
            {" "}
            <em>
              Nu: alleen UI-demo op Vercel (geen QUOTE_API_URL). Echte €/gewicht: lokaal of tijdelijk tunnel naar je
              PC.
            </em>
          </>
        )}
        {quoteBackend === "connected" && (
          <> <em>Quote-backend is gekoppeld — uploads geven echte berekeningen.</em></>
        )}
      </div>



      <div className="card">

        <label htmlFor="threemf">Printbestand (.3mf)</label>

        <input id="threemf" type="file" accept=".3mf,.stl" onChange={onFile} />

        {file && (

          <p style={{ margin: "0 0 1rem", color: "var(--muted)", fontSize: "0.9rem" }}>

            {file.name} · {(file.size / 1024).toFixed(0)} KB

          </p>

        )}

        <button type="button" className="primary" disabled={!file || loading} onClick={onQuote}>

          {loading ? "Bezig…" : "Offerte berekenen"}

        </button>

      </div>



      {result && (

        <div className={`card status ${result.ok ? "ok" : "warn"}`}>

          {!result.ok && <p>{result.error}</p>}

          {result.ok && (

            <>

              <p style={{ marginTop: 0 }}>

                {result.message ??

                  `Modus: ${result.mode ?? "quote"} · ${result.profiles_note ?? ""}`}

              </p>

              <table className="quote-table">

                <tbody>

                  <tr>

                    <th>Bestand</th>

                    <td>{result.filename ?? result.file?.name ?? "—"}</td>

                  </tr>

                  <tr>

                    <th>Objecten</th>

                    <td>{result.object_count ?? "—"}</td>

                  </tr>

                  <tr>

                    <th>Gewicht</th>

                    <td>{weight != null ? `${weight} g` : "— (API)"}</td>

                  </tr>

                  <tr>

                    <th>Materialen</th>

                    <td>

                      {result.materials?.length

                        ? result.materials.map((m) => `${m.label}: ${m.weight_g} g`).join("; ")

                        : "—"}

                    </td>

                  </tr>

                  <tr>

                    <th>Printtijd</th>

                    <td>

                      {printMin != null ? `${printMin} min` : "— (API)"}

                      {result.print_time_note ? ` · ${result.print_time_note}` : ""}

                    </td>

                  </tr>

                  <tr>

                    <th>Kostprijs (intern)</th>

                    <td>

                      {cost != null && result.currency

                        ? `${result.currency} ${cost}`

                        : result.quote?.cost_eur != null

                          ? `€ ${result.quote.cost_eur}`

                          : "— (API)"}

                    </td>

                  </tr>

                  <tr>

                    <th>Marge</th>

                    <td>

                      {result.margin_percent != null ? `${result.margin_percent} %` : "—"}

                    </td>

                  </tr>

                  <tr>

                    <th>Verkoopprijs</th>

                    <td>

                      {total != null && result.currency

                        ? `${result.currency} ${total}`

                        : total != null

                          ? `€ ${total}`

                          : "— (API)"}

                    </td>

                  </tr>

                </tbody>

              </table>

              {result.objects && result.objects.length > 0 && (

                <details style={{ marginTop: "1rem" }}>

                  <summary>Objecten</summary>

                  <ul>

                    {result.objects.map((o) => (

                      <li key={o.name}>

                        {o.name}: {o.weight_g} g

                        {o.material_label ? ` (${o.material_label})` : ""}

                      </li>

                    ))}

                  </ul>

                </details>

              )}

            </>

          )}

        </div>

      )}



      <div className={`status ${health.startsWith("OK") ? "ok" : "warn"}`}>Deploy: {health}</div>



      <footer>

        Intern · Crooijmans Pilot 3 · Backend: QUOTE_API_URL · Klant PNG→3MF: aparte Vercel-app{" "}

        <code>web/customer</code>

      </footer>

    </main>

  );

}


