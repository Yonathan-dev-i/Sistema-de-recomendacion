"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import type { ResultadoCarrera } from "@/lib/api";

/**
 * Barras horizontales del Top 5, ordenadas de mayor a menor `afinidad_pct`
 * (el backend ya las entrega ordenadas así — no se reordena aquí para no
 * duplicar la regla de negocio, solo se renderiza el orden recibido).
 * Animación de "llenado" al entrar en el viewport (`whileInView`), respeta
 * `prefers-reduced-motion` mediante la regla global ya definida en
 * `globals.css` (Fase 5), que Framer Motion honra automáticamente.
 *
 * Fase 9f: `memo` para no recalcular ni re-animar cuando el padre
 * (`PantallaResultados`) re-renderiza por el estado del comparador, que no
 * afecta a este componente.
 */
function BarrasTop5Base({ resultados }: { resultados: ResultadoCarrera[] }) {
  const max = Math.max(...resultados.map((r) => r.afinidad_pct), 1);

  return (
    <div className="space-y-3" role="img" aria-label="Gráfico de barras del Top 5 por afinidad">
      {resultados.map((r, i) => (
        <div key={r.carrera_id}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium">
              #{i + 1} {r.nombre}
            </span>
            <span className="font-semibold text-primary">{r.afinidad_pct.toFixed(1)}%</span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
            <motion.div
              className="h-3 rounded-full bg-primary"
              initial={{ width: 0 }}
              whileInView={{ width: `${(r.afinidad_pct / max) * 100}%` }}
              viewport={{ once: true, amount: 0.6 }}
              transition={{ duration: 0.7, ease: "easeOut", delay: i * 0.05 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export const BarrasTop5 = memo(BarrasTop5Base);
