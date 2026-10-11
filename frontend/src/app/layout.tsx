import type { Metadata } from "next";
import { DM_Serif_Display, Manrope, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const dmSerif = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  weight: ["400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "chaai. — AI Market Research & Quantitative Cockpit",
  description:
    "Editorial-grade financial research, technical indicators, risk analysis, and disciplined paper trading execution. Clarity over constant activity.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${dmSerif.variable} ${manrope.variable} ${ibmPlexMono.variable}`}
    >
      <body className="bg-bone text-ink font-sans min-h-screen antialiased selection:bg-stone selection:text-ink">
        {children}
      </body>
    </html>
  );
}
