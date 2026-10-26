import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Print uw logo — Aiva3D",
  description: "Bedrijven en personen uploaden een logo en downloaden een printbare 3MF of STL, tot 40×40 mm.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
