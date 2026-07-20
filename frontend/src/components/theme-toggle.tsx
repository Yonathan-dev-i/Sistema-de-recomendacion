"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Toggle claro/oscuro. `next-themes` persiste la preferencia en
 * `localStorage` y respeta `prefers-color-scheme` la primera vez
 * (configurado en ThemeProvider con `defaultTheme="system"`).
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  // Evita mismatch de hidratación: el tema real solo se conoce en cliente.
  const [montado, setMontado] = useState(false);
  useEffect(() => setMontado(true), []);

  const esOscuro = montado && resolvedTheme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={esOscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      onClick={() => setTheme(esOscuro ? "light" : "dark")}
    >
      {montado ? (
        esOscuro ? (
          <Sun className="h-5 w-5" />
        ) : (
          <Moon className="h-5 w-5" />
        )
      ) : (
        <span className="h-5 w-5" />
      )}
    </Button>
  );
}
