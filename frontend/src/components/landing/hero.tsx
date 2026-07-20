"use client";

import { useMemo } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Brain, MessageCircle, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Partículas ambientales del fondo del hero (brief: "Agregar partículas
 * animadas"). Se generan posiciones/duraciones pseudo-aleatorias una sola
 * vez por montaje (useMemo) para que no cambien en cada render; son
 * puramente decorativas (aria-hidden) y respetan `prefers-reduced-motion`
 * vía la regla ya definida en globals.css sobre `.particula`.
 */
function useParticulas(cantidad: number) {
  return useMemo(
    () =>
      Array.from({ length: cantidad }, (_, i) => ({
        id: i,
        left: `${Math.round((i * 137.5) % 100)}%`, // distribución tipo "golden angle", evita agrupamientos
        size: 3 + ((i * 7) % 5),
        duration: 8 + ((i * 3) % 10),
        delay: (i * 0.7) % 8,
      })),
    [cantidad],
  );
}

export function Hero() {
  const particulas = useParticulas(18);

  return (
    <section className="fondo-hero relative flex min-h-[calc(100vh-4rem)] items-center overflow-hidden">
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        {particulas.map((p) => (
          <span
            key={p.id}
            className="particula"
            style={{
              left: p.left,
              bottom: "-10%",
              width: p.size,
              height: p.size,
              animationDuration: `${p.duration}s`,
              animationDelay: `${p.delay}s`,
            }}
          />
        ))}
      </div>

      <div className="container relative grid gap-12 py-20 lg:grid-cols-2 lg:items-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <span className="glass-panel inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium text-white/90">
            <Sparkles className="h-3.5 w-3.5" />
            Universidad Nacional del Altiplano — Puno
          </span>

          <h1 className="mt-5 font-display text-4xl font-bold leading-[1.08] tracking-tight text-white sm:text-5xl lg:text-[64px]">
            Descubre la carrera ideal para ti con{" "}
            <span className="texto-degradado">Inteligencia Artificial</span>
          </h1>

          <p className="mt-5 max-w-xl text-lg text-white/70">
            Analizamos tus intereses, habilidades y preferencias para
            recomendarte la carrera universitaria que mejor se adapta a tu
            perfil.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" variant="gradient">
              <Link href="/test">
                Comenzar Test
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="glass" className="text-white">
              <Link href="/test/chatbot">
                <MessageCircle className="h-4 w-4" />
                Hablar con IA
              </Link>
            </Button>
          </div>

          <p className="mt-5 text-sm text-white/50">
            37 carreras · 17 áreas evaluadas · Test 100% gratuito
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
          className="relative mx-auto aspect-square w-full max-w-md"
        >
          {/* Silueta central: estudiante frente a una pantalla, resuelta con
              formas simples (sin depender de un asset de ilustración externo)
              para mantener coherencia con el resto del look glass/gradiente. */}
          <div className="glass-panel absolute inset-6 flex items-center justify-center rounded-[2.5rem] shadow-glow">
            <Brain className="h-20 w-20 text-white/80" aria-hidden="true" />
          </div>

          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="glass-panel absolute left-2 top-4 flex w-48 flex-col gap-2 rounded-2xl p-4"
          >
            <p className="text-xs font-medium text-white/60">IA analizando…</p>
            <div className="h-2 w-28 rounded-full bg-white/20" />
            <div className="h-2 w-20 rounded-full bg-white/15" />
            <div className="mt-1 h-1.5 w-full rounded-full bg-white/15">
              <motion.div
                initial={{ width: "20%" }}
                animate={{ width: "85%" }}
                transition={{ duration: 2.2, ease: "easeOut", delay: 0.4 }}
                className="h-1.5 rounded-full bg-gradient-brand"
              />
            </div>
          </motion.div>

          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            className="glass-panel absolute bottom-16 right-0 flex w-44 items-center gap-3 rounded-2xl p-4"
          >
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-sm font-bold text-white">
              94%
            </span>
            <div className="flex flex-col gap-1">
              <p className="text-xs font-semibold text-white">Compatibilidad</p>
              <p className="text-[11px] text-white/60">Ingeniería de Sistemas</p>
            </div>
          </motion.div>

          <motion.div
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="glass-panel absolute bottom-0 left-6 rounded-2xl px-4 py-2"
          >
            <p className="text-xs font-medium text-white/80">Top 5 Carreras</p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}