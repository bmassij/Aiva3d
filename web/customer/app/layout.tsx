import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aiva3D — Customize your grip",
  description: "Upload a logo, pick colors, export a printable 3MF (customer preview)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
