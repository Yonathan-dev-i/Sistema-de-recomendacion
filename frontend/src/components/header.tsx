"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { GraduationCap, History, LogOut, Menu, User, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuthStore } from "@/lib/auth-store";

const NAV_LINKS = [
  { href: "/#como-funciona", label: "Cómo funciona" },
  { href: "/#metodos", label: "Métodos" },
  { href: "/#carreras", label: "Carreras" },
  { href: "/#faq", label: "Preguntas frecuentes" },
];

export function Header() {
  const [menuAbierto, setMenuAbierto] = useState(false);
  const router = useRouter();
  const usuario = useAuthStore((s) => s.usuario);
  const cerrarSesion = useAuthStore((s) => s.cerrarSesion);

  function handleCerrarSesion() {
    cerrarSesion();
    setMenuAbierto(false);
    router.push("/");
  }

  return (
    <header className="sticky top-3 z-50 px-3 print:hidden sm:top-4 sm:px-4">
      <div className="glass-panel container flex h-16 items-center justify-between rounded-2xl !px-4 shadow-lg sm:!px-6">
        <Link
          href="/"
          className="flex items-center gap-2 font-display text-lg font-bold tracking-tight"
          onClick={() => setMenuAbierto(false)}
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-brand text-white shadow-glow">
            <GraduationCap className="h-5 w-5" />
          </span>
          <span className="hidden sm:inline">
            Orientación Vocacional <span className="texto-degradado">UNA Puno</span>
          </span>
          <span className="sm:hidden">UNA Puno</span>
        </Link>

        <nav
          className="hidden items-center gap-6 md:flex"
          aria-label="Navegación principal"
        >
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <ThemeToggle />
          {usuario ? (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/historial">
                  <History className="h-4 w-4" aria-hidden="true" />
                  Mis resultados
                </Link>
              </Button>
              <span className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
                <User className="h-4 w-4" aria-hidden="true" />
                {usuario.nombre_completo.split(" ")[0]}
              </span>
              <Button variant="ghost" size="sm" onClick={handleCerrarSesion}>
                <LogOut className="h-4 w-4" aria-hidden="true" />
                Salir
              </Button>
            </>
          ) : (
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Iniciar sesión</Link>
            </Button>
          )}
          <Button asChild size="sm" variant="gradient">
            <Link href="/test">Comenzar Test</Link>
          </Button>
        </div>

        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            aria-label={menuAbierto ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={menuAbierto}
            onClick={() => setMenuAbierto((v) => !v)}
          >
            {menuAbierto ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {menuAbierto && (
          <motion.nav
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="glass-panel mx-3 mt-2 overflow-hidden rounded-2xl md:hidden"
            aria-label="Navegación principal (móvil)"
          >
            <div className="flex flex-col gap-1 p-3">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMenuAbierto(false)}
                  className="rounded-lg px-3 py-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                >
                  {link.label}
                </Link>
              ))}
              {usuario ? (
                <div className="mt-2 flex flex-col gap-2 border-t border-border pt-3">
                  <Link
                    href="/historial"
                    onClick={() => setMenuAbierto(false)}
                    className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-primary"
                  >
                    <History className="h-4 w-4" aria-hidden="true" />
                    Mis resultados
                  </Link>
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
                      <User className="h-4 w-4" aria-hidden="true" />
                      {usuario.nombre_completo.split(" ")[0]}
                    </span>
                    <Button variant="ghost" size="sm" onClick={handleCerrarSesion}>
                      <LogOut className="h-4 w-4" aria-hidden="true" />
                      Salir
                    </Button>
                  </div>
                </div>
              ) : (
                <Button asChild variant="ghost" size="sm" className="mt-2">
                  <Link href="/login" onClick={() => setMenuAbierto(false)}>
                    Iniciar sesión
                  </Link>
                </Button>
              )}
              <Button asChild size="sm" variant="gradient">
                <Link href="/test" onClick={() => setMenuAbierto(false)}>
                  Comenzar Test
                </Link>
              </Button>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}