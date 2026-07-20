"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Download, RotateCcw } from "lucide-react";

import {
  Area,
  ApiError,
  CarreraDetalle,
  ResultadoCarrera,
  obtenerAreas,
  obtenerCarreraDetalle,
} from "@/lib/api";
import { guardarUltimoResultado } from "@/lib/ultimo-resultado";
import { TarjetaCarrera } from "./tarjeta-carrera";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";

/**
 * Fase 9f (performance): el radar (SVG con hasta 3 series × 17 puntos y sus
 * áreas táctiles), las barras del Top 5 (con animación de Framer Motion) y
 * el comparador (que puede montar un segundo radar) son el trabajo más
 * pesado de esta pantalla. Se cargan con `next/dynamic` para que su JS
 * entre en un chunk aparte que no bloquea el render inicial (encabezado +
 * tarjetas), mostrando un `Skeleton` del tamaño real mientras se cargan.
 * `ssr: false` porque dependen de interacción del cliente (hover/tap) y no
 * aportan al primer HTML servido.
 */
const RadarChart = dynamic(() => import("./radar-chart").then((m) => m.RadarChart), {
  ssr: false,
  loading: () => <Skeleton className="mx-auto h-[420px] w-full max-w-[420px]" />,
});
const BarrasTop5 = dynamic(() => import("./barras-top5").then((m) => m.BarrasTop5), {
  ssr: false,
  loading: () => <Skeleton className="h-40 w-full" />,
});
const ComparadorCarreras = dynamic(
  () => import("./comparador-carreras").then((m) => m.ComparadorCarreras),
  {
    ssr: false,
    loading: () => <Skeleton className="h-32 w-full" />,
  },
);

export function PantallaResultados({
  testId,
  vectorUsuario,
  resultados,
  metodo,
}: {
  testId: number;
  vectorUsuario: Record<string, number>;
  resultados: ResultadoCarrera[];
  metodo: "tradicional" | "chatbot";
}) {
  const [areas, setAreas] = useState<Area[] | null>(null);
  const [top1Detalle, setTop1Detalle] = useState<CarreraDetalle | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [seleccionComparador, setSeleccionComparador] = useState<number[]>([]);

  const top1 = resultados[0];

  const cargar = () => {
    setErrorMsg(null);
    setAreas(null);
    Promise.all([obtenerAreas(), top1 ? obtenerCarreraDetalle(top1.carrera_id) : null])
      .then(([areasData, detalle]) => {
        setAreas([...areasData].sort((a, b) => a.orden - b.orden));
        setTop1Detalle(detalle);
      })
      .catch((err) => {
        setErrorMsg(err instanceof ApiError ? err.message : "Error de conexión con el backend.");
      });
  };

  useEffect(() => {
    cargar();
    guardarUltimoResultado({ testId, vectorUsuario, resultados });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [testId]);

  const toggleComparador = (carreraId: number) => {
    setSeleccionComparador((prev) => {
      if (prev.includes(carreraId)) return prev.filter((id) => id !== carreraId);
      if (prev.length >= 3) return prev; // máximo 3, según el criterio de la Fase 8
      return [...prev, carreraId];
    });
  };

  const fechaGeneracion = useMemo(
    () => new Date().toLocaleDateString("es-PE", { year: "numeric", month: "long", day: "numeric" }),
    [],
  );

  if (errorMsg) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <ErrorState message={`No se pudo cargar el detalle de resultados (${errorMsg}).`} onRetry={cargar} />
      </div>
    );
  }

  return (
    <div id="resultado-imprimible" className="mx-auto flex max-w-4xl flex-col gap-8 px-4 py-10">
      <div className="text-center">
        <p className="text-sm text-muted-foreground">
          Intento #{testId} · Método: {metodo === "tradicional" ? "Test tradicional" : "Chatbot"} ·{" "}
          {fechaGeneracion}
        </p>
        <h1 className="mt-1 font-display text-2xl font-bold sm:text-3xl">
          Tu Top 5 de carreras recomendadas
        </h1>
        {top1 && (
          <div className="mt-3 flex flex-col items-center gap-1">
            <span className="rounded-full bg-primary px-4 py-1 text-sm font-semibold text-primary-foreground">
              {top1.afinidad_pct.toFixed(1)}% de afinidad
            </span>
            <p className="text-lg font-semibold text-primary">{top1.nombre}</p>
            {top1Detalle?.facultad && (
              <p className="text-sm text-muted-foreground">{top1Detalle.facultad}</p>
            )}
          </div>
        )}
      </div>

      {/* Gráfico radar: usuario vs. carrera recomendada — datos reales del backend */}
      <section>
        <h2 className="mb-1 text-center font-display text-lg font-semibold">
          Tu perfil vs. {top1?.nombre ?? "la carrera recomendada"}
        </h2>
        <p className="mb-3 text-center text-sm text-muted-foreground">
          Cada punta del gráfico es un área evaluada: mientras más lejos del centro,
          más fuerte es esa competencia en ti (guinda) y en la carrera (dorado).
        </p>
        {areas && top1Detalle ? (
          <RadarChart
            areas={areas}
            series={[
              { label: "Tu perfil", color: "#6E8FFF", valores: vectorUsuario },
              { label: top1Detalle.nombre, color: "#8B5CF6", valores: top1Detalle.perfil_areas },
            ]}
          />
        ) : (
          <Skeleton className="mx-auto h-[420px] w-full max-w-[420px]" />
        )}
      </section>

      {/* Gráfico de barras del Top 5 */}
      <section>
        <h2 className="mb-3 font-display text-lg font-semibold">Afinidad del Top 5</h2>
        <BarrasTop5 resultados={resultados} />
      </section>

      {/* Tarjetas completas */}
      <section>
        <h2 className="mb-3 font-display text-lg font-semibold">Detalle de cada carrera</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resultados.map((r, i) => (
            <TarjetaCarrera
              key={r.carrera_id}
              resultado={r}
              posicion={i + 1}
              seleccionable
              seleccionada={seleccionComparador.includes(r.carrera_id)}
              onToggleSeleccion={() => toggleComparador(r.carrera_id)}
            />
          ))}
        </div>
      </section>

      {/* Comparador de carreras (hasta 3, mejora sugerida) */}
      <section className="print:hidden" id="comparador">
        <h2 className="mb-3 font-display text-lg font-semibold">Comparador de carreras</h2>
        {areas && (
          <ComparadorCarreras resultados={resultados} seleccionadas={seleccionComparador} areas={areas} />
        )}
      </section>

      {/* Acciones — ocultas al imprimir/exportar a PDF */}
      <div className="flex flex-wrap justify-center gap-3 pt-2 print:hidden">
        {top1 && (
          <Link
            href={`/carrera/${top1.carrera_id}`}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:border-primary/50"
          >
            Ver perfil profesional
          </Link>
        )}
        <a
          href="#comparador"
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:border-primary/50"
        >
          Comparar carreras
        </a>
        <button
          onClick={() => window.print()}
          className="flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:border-primary/50"
        >
          <Download className="h-4 w-4" />
          Descargar PDF
        </button>
        <Link
          href={metodo === "tradicional" ? "/test/tradicional" : "/test/chatbot"}
          onClick={() => {
            if (metodo === "chatbot" && typeof window !== "undefined") {
              window.localStorage.removeItem("vocacional_chatbot_sesion_id");
            }
          }}
          className="flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm font-medium hover:border-primary/50"
        >
          <RotateCcw className="h-4 w-4" />
          Realizar nuevamente el test
        </Link>
        <Link
          href="/"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}