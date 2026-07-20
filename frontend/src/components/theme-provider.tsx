"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import { MotionConfig } from "framer-motion";
import type { ReactNode } from "react";

/**
 * `MotionConfig reducedMotion="user"` (Fase 9d) hace que **toda** animación
 * de Framer Motion en la app respete `prefers-reduced-motion: reduce` del
 * sistema operativo del usuario, reduciéndolas automáticamente a un
 * cross-fade instantáneo. La regla CSS global en `globals.css`
 * (`animation-duration: 0.01ms !important`) ya cubre las transiciones CSS
 * puras, pero Framer Motion anima vía JS/transform y no obedece esa regla
 * por sí sola — de ahí la necesidad de este wrapper a nivel de aplicación,
 * en vez de repetir el chequeo en cada componente que usa `motion.*`
 * (header, landing, chatbot, resultados/barras-top5, /test).
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <MotionConfig reducedMotion="user">{children}</MotionConfig>
    </NextThemesProvider>
  );
}