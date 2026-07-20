import type { Metadata } from "next";
import "./globals.css";
import { inter, lexend } from "@/lib/fonts";
import { ThemeProvider } from "@/components/theme-provider";
import { Header } from "@/components/header";
import { SessionInit } from "@/components/auth/session-init";

export const metadata: Metadata = {
  title: "Orientación Vocacional | UNA Puno",
  description:
    "Sistema Inteligente de Orientación Vocacional de la Universidad Nacional del Altiplano - Puno",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning className={`${inter.variable} ${lexend.variable}`}>
      <body className="font-sans">
        <ThemeProvider>
          <SessionInit />
          <a href="#contenido" className="skip-link">
            Saltar al contenido principal
          </a>
          <Header />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}