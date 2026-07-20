"use client";

import { memo } from "react";
import Link from "next/link";
import type { ResultadoCarrera } from "@/lib/api";

/**
 * Tarjeta completa del Top 5 (criterio de la Fase 8: "Tarjetas completas con
 * fortalezas, áreas por mejorar y explicación por reglas"). Reemplaza la
 * versión reducida usada provisionalmente por la Fase 4, agregando el
 * indicador circular de afinidad y el botón "Ver detalle" hacia
 * `/carrera/{id}` (ya existente desde la Fase 5).
 *
 * Fase 9f: envuelta en `memo` porque se renderiza hasta 5 veces en la
 * grilla de resultados; sin memo, cada `toggleComparador` en la tarjeta A
 * volvía a renderizar las otras 4 tarjetas cuyas props no cambiaron.
 */
function TarjetaCarreraBase({
  resultado,
  posicion,
  seleccionable,
  seleccionada,
  onToggleSeleccion,
}: {
  resultado: ResultadoCarrera;
  posicion: number;
  seleccionable?: boolean;
  seleccionada?: boolean;
  onToggleSeleccion?: () => void;
}) {
  const r = resultado;
  const esDestacada = posicion === 1;
  const circunferencia = 2 * Math.PI * 26;
  const relleno = (r.afinidad_pct / 100) * circunferencia;

  return (
    <div
      className={`tarjeta-interactiva relative flex flex-col gap-3 rounded-2xl border p-5 ${
        esDestacada
          ? "border-accent/50 bg-accent/5 shadow-md sm:col-span-2 lg:col-span-1"
          : "border-border bg-muted/40"
      }`}
    >
      {esDestacada && (
        <span className="absolute -top-3 left-5 rounded-full bg-accent px-3 py-0.5 text-xs font-semibold text-accent-foreground shadow-sm">
          ★ Tu mejor afinidad
        </span>
      )}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground">#{posicion}</span>
        <div className="relative h-16 w-16 shrink-0">
          <svg viewBox="0 0 60 60" className="h-16 w-16 -rotate-90">
            <circle cx="30" cy="30" r="26" fill="none" strokeWidth="6" className="stroke-muted" />
            <circle
              cx="30"
              cy="30"
              r="26"
              fill="none"
              strokeWidth="6"
              strokeLinecap="round"
              className={esDestacada ? "stroke-accent" : "stroke-primary"}
              strokeDasharray={`${relleno} ${circunferencia}`}
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold">
            {r.afinidad_pct.toFixed(0)}%
          </span>
        </div>
      </div>

      <h3 className="text-lg font-semibold leading-tight">{r.nombre}</h3>

      {/* Callout "por qué te la recomendamos": siempre visible en la #1 para
          que la razón principal no quede escondida bajo un <details>; en el
          resto del Top 5 se mantiene colapsable para no saturar la grilla. */}
      {esDestacada ? (
        <div className="rounded-xl border border-accent/30 bg-accent/10 p-3 text-sm">
          <p className="mb-1 flex items-center gap-1.5 font-medium text-foreground">
            <span aria-hidden="true">💡</span> Por qué te la recomendamos
          </p>
          <p className="text-muted-foreground">{r.explicacion}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Distancia de Mahalanobis: {r.distancia_mahalanobis.toFixed(4)}
          </p>
        </div>
      ) : (
        <details className="text-sm text-muted-foreground">
          <summary className="cursor-pointer font-medium text-foreground">
            💡 Por qué te la recomendamos
          </summary>
          <p className="mt-1">{r.explicacion}</p>
          <p className="mt-1 text-xs">
            Distancia de Mahalanobis: {r.distancia_mahalanobis.toFixed(4)}
          </p>
        </details>
      )}

      {r.fortalezas.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold text-muted-foreground">Fortalezas</p>
          <div className="flex flex-wrap gap-1">
            {r.fortalezas.map((f) => (
              <span
                key={f}
                className="rounded-full bg-success/15 px-2 py-0.5 text-xs text-success-700 dark:text-green-300"
              >
                {f.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}
      {r.areas_por_mejorar.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold text-muted-foreground">Áreas por mejorar</p>
          <div className="flex flex-wrap gap-1">
            {r.areas_por_mejorar.map((a) => (
              <span
                key={a}
                className="rounded-full bg-warning/15 px-2 py-0.5 text-xs text-warning-700 dark:text-amber-300"
              >
                {a.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-1 flex items-center gap-2">
        <Link
          href={`/carrera/${r.carrera_id}`}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:border-primary/50"
        >
          Ver detalle
        </Link>
        {seleccionable && (
          <button
            type="button"
            onClick={onToggleSeleccion}
            aria-pressed={seleccionada}
            aria-label={
              seleccionada
                ? `Quitar ${r.nombre} del comparador`
                : `Agregar ${r.nombre} al comparador`
            }
            className={`min-h-[36px] rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              seleccionada
                ? "bg-primary text-primary-foreground"
                : "border border-border hover:border-primary/50"
            }`}
          >
            {seleccionada ? "✓ En comparador" : "Comparar"}
          </button>
        )}
      </div>
    </div>
  );
}

export const TarjetaCarrera = memo(TarjetaCarreraBase);