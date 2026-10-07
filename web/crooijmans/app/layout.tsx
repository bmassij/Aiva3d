import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Crooijmans — 3D print offerte",
  description: "Upload 3MF, bereken gewicht, materiaal, tijd en offerte (Pilot 3)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
