"use client";

import { useCallback, useEffect, useState } from "react";
import type { Area, CarreraDetalle, ResultadoCarrera } from "@/lib/api";
import { ApiError, obtenerCarreraDetalle } from "@/lib/api";
import { RadarChart } from "./radar-chart";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";

const COLORES = ["#a5303f", "#c9a227", "#2563eb"];

/**
 * Comparador de carreras (mejora sugerida del prompt maestro, Fase 8):
 * el usuario elige 2-3 carreras de su propio Top 5 y las ve lado a lado
 * (afinidad %, fortalezas, áreas por mejorar) junto con un mini-radar
 * superpuesto por carrera.
 */
export function ComparadorCarreras({
  resultados,
  seleccionadas,
  areas,
}: {
  resultados: ResultadoCarrera[];
  seleccionadas: number[]; // carrera_id[]
  areas: Area[];
}) {
  const [detalles, setDetalles] = useState<Record<number, CarreraDetalle>>({});
  const [cargando, setCargando] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const carrerasElegidas = resultados.filter((r) => seleccionadas.includes(r.carrera_id));

  const cargarFaltantes = useCallback(() => {
    setErrorMsg(null);
    setDetalles((prevDetalles) => {
      const faltantes = seleccionadas.filter((id) => !prevDetalles[id]);
      if (faltantes.length === 0) return prevDetalles;
      setCargando(true);
      Promise.all(faltantes.map((id) => obtenerCarreraDetalle(id)))
        .then((datos) => {
          setDetalles((prev) => {
            const copia = { ...prev };
            for (const d of datos) copia[d.id] = d;
            return copia;
          });
        })
        .catch((err) => {
          setErrorMsg(
            err instanceof ApiError ? err.message : "Error de conexión con el backend.",
          );
        })
        .finally(() => setCargando(false));
      return prevDetalles;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seleccionadas.join(",")]);

  useEffect(() => {
    cargarFaltantes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seleccionadas.join(",")]);

  if (seleccionadas.length < 2) {
    return (
      <p className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Selecciona al menos 2 carreras del Top 5 (botón &quot;Comparar&quot; en cada tarjeta) para
        verlas lado a lado aquí.
      </p>
    );
  }

  if (cargando && Object.keys(detalles).length < seleccionadas.length) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {seleccionadas.map((id) => (
          <Skeleton key={id} className="h-64 w-full" />
        ))}
      </div>
    );
  }

  if (errorMsg) {
    return (
      <ErrorState
        message={`No se pudo cargar la comparación (${errorMsg}).`}
        onRetry={cargarFaltantes}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {carrerasElegidas.map((r, i) => {
          const detalle = detalles[r.carrera_id];
          return (
            <div key={r.carrera_id} className="rounded-2xl border border-border bg-muted/40 p-4">
              <div className="mb-2 flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: COLORES[i % COLORES.length] }}
                  aria-hidden
                />
                <h4 className="text-sm font-semibold leading-tight">{r.nombre}</h4>
              </div>
              <p className="text-xs text-muted-foreground">
                {detalle?.facultad ?? "Facultad no especificada"}
              </p>
              <p className="mt-2 text-2xl font-bold text-primary">{r.afinidad_pct.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground">afinidad</p>

              <div className="mt-3">
                <p className="mb-1 text-xs font-semibold text-muted-foreground">Fortalezas</p>
                <div className="flex flex-wrap gap-1">
                  {r.fortalezas.slice(0, 4).map((f) => (
                    <span
                      key={f}
                      className="rounded-full bg-success/15 px-2 py-0.5 text-[11px] text-success-700 dark:text-green-300"
                    >
                      {f.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
              <div className="mt-2">
                <p className="mb-1 text-xs font-semibold text-muted-foreground">
                  Áreas por mejorar
                </p>
                <div className="flex flex-wrap gap-1">
                  {r.areas_por_mejorar.slice(0, 4).map((a) => (
                    <span
                      key={a}
                      className="rounded-full bg-warning/15 px-2 py-0.5 text-[11px] text-warning-700 dark:text-amber-300"
                    >
                      {a.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {Object.keys(detalles).length >= carrerasElegidas.length && carrerasElegidas.length >= 2 && (
        <div>
          <h4 className="mb-2 text-center text-sm font-semibold">
            Perfil de 17 áreas superpuesto
          </h4>
          <RadarChart
            areas={areas}
            series={carrerasElegidas.map((r, i) => ({
              label: r.nombre,
              color: COLORES[i % COLORES.length],
              valores: detalles[r.carrera_id]?.perfil_areas ?? {},
            }))}
          />
        </div>
      )}
    </div>
  );
}
