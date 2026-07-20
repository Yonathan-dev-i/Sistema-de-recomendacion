import { Inter, Lexend } from "next/font/google";

/**
 * Rediseño "Superhuman-inspired": el prompt de diseño pide explícitamente
 * "Inter Variable" como tipografía única de la interfaz. El proyecto ya
 * referenciaba `--font-sans: "Inter"` y `--font-display: "Lexend"` en
 * `globals.css`, pero en ningún lugar se cargaban realmente esas fuentes
 * (ni `next/font`, ni un `<link>` a Google Fonts) — el navegador caía
 * silenciosamente a la fuente del sistema. Este archivo corrige eso.
 *
 * `variable` reasigna directamente esas mismas custom properties, así que
 * el resto de la app (que ya usa `font-sans` / `font-display` de Tailwind)
 * no necesita ningún otro cambio.
 */
export const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const lexend = Lexend({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});