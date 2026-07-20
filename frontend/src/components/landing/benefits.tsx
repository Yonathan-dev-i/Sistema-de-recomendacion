"use client";

import { motion } from "framer-motion";
import { BarChart3, Compass, FileText, Scale, Sparkles, Users } from "lucide-react";

const BENEFICIOS = [
  { icono: Sparkles, texto: "Resultados personalizados" },
  { icono: Compass, texto: "Basado en tus propios intereses" },
  { icono: Scale, texto: "Recomendación objetiva y estadísticamente fundamentada" },
  { icono: Users, texto: "Comparación con 37 carreras reales de la UNA Puno" },
  { icono: FileText, texto: "Explicación detallada de fortalezas y áreas por mejorar" },
  { icono: BarChart3, texto: "Basado en Distancia de Mahalanobis, no solo similitud simple" },
];

export function Benefits() {
  return (
    <section className="container py-16 sm:py-24">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Beneficios</h2>
        <p className="mt-3 text-muted-foreground">
          Un modelo estadístico multivariado, no una simple lista de
          coincidencias.
        </p>
      </div>

      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {BENEFICIOS.map((b, i) => (
          <motion.div
            key={b.texto}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.4, ease: "easeOut", delay: i * 0.06 }}
            className="flex items-start gap-3 rounded-xl border border-border bg-card p-5"
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/15 text-accent-700 dark:text-accent-300">
              <b.icono className="h-5 w-5" />
            </span>
            <p className="text-sm font-medium leading-snug text-foreground/90">{b.texto}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
