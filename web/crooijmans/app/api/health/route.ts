import { NextResponse } from "next/server";

export async function GET() {
  const quoteApi = process.env.QUOTE_API_URL ?? process.env.NEXT_PUBLIC_QUOTE_API_URL ?? "";
  return NextResponse.json({
    ok: true,
    service: "crooijmans-print-calculator",
    version: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? "local",
    region: process.env.VERCEL_REGION ?? "local",
    quote_backend: quoteApi ? "connected" : "preview_only",
  });
}
