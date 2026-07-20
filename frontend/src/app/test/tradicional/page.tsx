"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ApiError,
  Area,
  Pregunta,
  ResultadoCarrera,
  enviarTestTradicional,
  obtenerAreas,
  obtenerPreguntas,
} from "@/lib/api";
import { progresoEstimadoPct, siguientePreguntaIndiceEnArea } from "@/lib/adaptiveFlow";
import { iconoDeArea } from "@/lib/area-icons";
import { PantallaResultados } from "@/components/resultados/pantalla-resultados";
import { useAuthStore } from "@/lib/auth-store";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";

type Paso = { areaIndex: number; pregunta: Pregunta };
type Fase = "cargando_datos" | "error_carga" | "formulario" | "enviando" | "resultados";

const ESCALA_LIKERT: { valor: number; label: string; emoji: string; tinte: number }[] = [
  { valor: 1, label: "No me gusta nada", emoji: "😕", tinte: 0.03 },
  { valor: 2, label: "Me gusta poco", emoji: "🙁", tinte: 0.06 },
  { valor: 3, label: "Me gusta moderadamente", emoji: "🙂", tinte: 0.1 },
  { valor: 4, label: "Me gusta bastante", emoji: "😃", tinte: 0.16 },
  { valor: 5, label: "Me gusta mucho", emoji: "🤩", tinte: 0.24 },
];

/** Frase corta de ánimo al cruzar ciertos hitos de áreas completadas (puramente
 * cosmético: no afecta el cálculo, solo hace el recorrido de 17 áreas menos monótono). */
function fraseDeHito(numeroAreaActual: number, totalAreas: number): string | null {
  const restantes = totalAreas - numeroAreaActual + 1;
  if (numeroAreaActual === 1) return null;
  if (restantes === 1) return "¡Última área, ya casi terminas!";
  if (numeroAreaActual === Math.ceil(totalAreas / 2)) return "Vas por la mitad del camino. ¡Sigue así!";
  if (restantes === 5) return "Ya quedan pocas áreas. ¡Vas muy bien!";
  return null;
}

export default function TestTradicionalPage() {
  const [fase, setFase] = useState<Fase>("cargando_datos");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const accessToken = useAuthStore((s) => s.accessToken);

  const [areas, setAreas] = useState<Area[]>([]);
  const [preguntasPorArea, setPreguntasPorArea] = useState<Record<string, Pregunta[]>>({});

  const [pasos, setPasos] = useState<Paso[]>([]);
  const [cursor, setCursor] = useState(0);
  const [respuestas, setRespuestas] = useState<Record<number, number>>({});

  const [resultado, setResultado] = useState<{
    testId: number;
    vectorUsuario: Record<string, number>;
    resultados: ResultadoCarrera[];
  } | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // Carga inicial: áreas + banco de preguntas. Se expone como función
  // reutilizable (no solo un efecto de una sola vez) para que el botón
  // "Reintentar" del estado de error pueda repetir exactamente la misma
  // carga sin recurrir a un `window.location.reload()` de página completa.
  const cargarDatosIniciales = useCallback(() => {
    setFase("cargando_datos");
    setErrorMsg(null);
    Promise.all([obtenerAreas(), obtenerPreguntas()])
      .then(([areasData, preguntasData]) => {
        const ordenadas = [...areasData].sort((a, b) => a.orden - b.orden);
        const agrupadas: Record<string, Pregunta[]> = {};
        for (const area of ordenadas) agrupadas[area.key] = [];
        for (const p of preguntasData) {
          if (agrupadas[p.area]) agrupadas[p.area].push(p);
        }
        for (const key of Object.keys(agrupadas)) {
          agrupadas[key].sort((a, b) => a.id - b.id);
        }
        setAreas(ordenadas);
        setPreguntasPorArea(agrupadas);
        setFase("formulario");
      })
      .catch((err) => {
        setErrorMsg(err instanceof ApiError ? err.message : "Error de conexión con el backend.");
        setFase("error_carga");
      });
  }, []);

  useEffect(() => {
    cargarDatosIniciales();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const finalizarTest = useCallback(
    async (pasosFinales: Paso[], respuestasFinales: Record<number, number>) => {
      setFase("enviando");
      try {
        const payload = pasosFinales.map((p) => ({
          pregunta_id: p.pregunta.id,
          respuesta: respuestasFinales[p.pregunta.id],
        }));
        const data = await enviarTestTradicional(payload, accessToken);
        setResultado({
          testId: data.test_id,
          vectorUsuario: data.vector_usuario,
          resultados: data.resultados,
        });
        setFase("resultados");
      } catch (err) {
        setErrorMsg(err instanceof ApiError ? err.message : String(err));
        setFase("error_carga");
      }
    },
    [accessToken],
  );

  // Motor de avance: dado el estado actual, calcula la siguiente pregunta a
  // formular (o `null` si el test terminó) aplicando la Lógica Adaptativa.
  const calcularSiguientePaso = useCallback(
    (pasosActuales: Paso[], respuestasActuales: Record<number, number>): Paso | null => {
      if (areas.length === 0) return null;

      if (pasosActuales.length === 0) {
        const primeraPregunta = preguntasPorArea[areas[0]?.key]?.[0];
        return primeraPregunta ? { areaIndex: 0, pregunta: primeraPregunta } : null;
      }

      const areaIndexActual = pasosActuales[pasosActuales.length - 1].areaIndex;
      const grupoAreaActual = pasosActuales.filter((p) => p.areaIndex === areaIndexActual);
      const preguntasArea = preguntasPorArea[areas[areaIndexActual]?.key] ?? [];
      const respuestasArea = grupoAreaActual.map((p) => respuestasActuales[p.pregunta.id]);

      const siguienteIdxEnArea = siguientePreguntaIndiceEnArea(
        respuestasArea,
        preguntasArea.length,
      );
      if (siguienteIdxEnArea !== null) {
        return { areaIndex: areaIndexActual, pregunta: preguntasArea[siguienteIdxEnArea] };
      }

      const siguienteAreaIndex = areaIndexActual + 1;
      if (siguienteAreaIndex >= areas.length) return null; // 17 áreas completadas

      const primeraPreguntaSiguienteArea = preguntasPorArea[areas[siguienteAreaIndex]?.key]?.[0];
      return primeraPreguntaSiguienteArea
        ? { areaIndex: siguienteAreaIndex, pregunta: primeraPreguntaSiguienteArea }
        : null;
    },
    [areas, preguntasPorArea],
  );

  // Cuando el cursor apunta a un paso que todavía no existe, se calcula (o
  // se finaliza el test si ya no queda ninguna pregunta por formular).
  useEffect(() => {
    if (fase !== "formulario") return;
    if (areas.length === 0) return;
    if (cursor < pasos.length) return; // ya existe ese paso, nada que calcular

    const siguiente = calcularSiguientePaso(pasos, respuestas);
    if (siguiente === null) {
      finalizarTest(pasos, respuestas);
      return;
    }
    setPasos((prev) => [...prev, siguiente]);
  }, [cursor, pasos, areas, respuestas, fase, calcularSiguientePaso, finalizarTest]);

  const pasoActual = cursor < pasos.length ? pasos[cursor] : null;
  const respuestaActual = pasoActual ? respuestas[pasoActual.pregunta.id] : undefined;

  const onSeleccionar = (valor: number) => {
    if (!pasoActual) return;
    const respuestaPrevia = respuestas[pasoActual.pregunta.id];
    setRespuestas((prev) => ({ ...prev, [pasoActual.pregunta.id]: valor }));
    if (respuestaPrevia !== undefined && respuestaPrevia !== valor && cursor < pasos.length - 1) {
      // Edición retroactiva: se descartan los pasos posteriores para que el
      // motor recalcule cuántas preguntas corresponden desde aquí.
      setPasos((prev) => prev.slice(0, cursor + 1));
      setToast(
        "Como cambiaste tu respuesta, el número de preguntas de esta área (y las siguientes) se recalculó.",
      );
    }
  };

  const onSiguiente = () => {
    if (respuestaActual === undefined) return;
    setCursor((c) => c + 1);
  };

  const onAnterior = () => {
    if (cursor > 0) setCursor((c) => c - 1);
  };

  const totalAreas = areas.length || 17;
  const areaLabelActual = pasoActual ? areas[pasoActual.areaIndex]?.label : "";
  const numeroAreaActual = pasoActual ? pasoActual.areaIndex + 1 : 1;
  const progresoPct = pasoActual ? progresoEstimadoPct(pasoActual.areaIndex, totalAreas) : 0;
  const preguntasAreaActual = pasoActual
    ? preguntasPorArea[areas[pasoActual.areaIndex]?.key] ?? []
    : [];
  const numeroPreguntaEnArea =
    pasoActual !== null
      ? pasos.filter((p) => p.areaIndex === pasoActual.areaIndex).indexOf(pasoActual) + 1
      : 1;

  if (fase === "cargando_datos") {
    return <SkeletonFormulario />;
  }

  if (fase === "error_carga") {
    return (
      <main
        id="contenido"
        className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-4 py-8"
      >
        <ErrorState
          message={`No se pudo completar el test: ${errorMsg}`}
          onRetry={cargarDatosIniciales}
        />
      </main>
    );
  }

  if (fase === "enviando") {
    return <SkeletonEnviando />;
  }

  if (fase === "resultados" && resultado) {
    return (
      <PantallaResultados
        testId={resultado.testId}
        vectorUsuario={resultado.vectorUsuario}
        resultados={resultado.resultados}
        metodo="tradicional"
      />
    );
  }

  if (!pasoActual) {
    return <SkeletonFormulario />;
  }

  return (
    <main id="contenido" className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-4 py-8">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <Link href="/" className="hover:underline">
          ← Salir
        </Link>
        <span>Test Tradicional</span>
      </div>

      {/* Progreso: por área + barra continua estimada */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm font-medium">
          <span>
            Área {numeroAreaActual} de {totalAreas}
          </span>
          <span className="text-muted-foreground">{progresoPct}% estimado</span>
        </div>
        <div className="flex gap-1">
          {areas.map((a, i) => (
            <div
              key={a.key}
              className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${
                i < numeroAreaActual - 1
                  ? "bg-primary"
                  : i === numeroAreaActual - 1
                    ? "bg-primary/60"
                    : "bg-muted"
              }`}
            />
          ))}
        </div>
        {fraseDeHito(numeroAreaActual, totalAreas) && (
          <p className="text-center text-xs font-medium text-accent-700 dark:text-accent-300">
            {fraseDeHito(numeroAreaActual, totalAreas)}
          </p>
        )}
      </div>

      {toast && (
        <div
          role="status"
          aria-live="polite"
          className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200"
        >
          {toast}
        </div>
      )}

      {/* Tarjeta de pregunta */}
      <div
        key={pasoActual.pregunta.id}
        className="animar-entrada rounded-2xl border border-border bg-muted/40 p-6 shadow-sm"
      >
        <p className="mb-1 flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wide text-primary">
          <span className="text-base" aria-hidden="true">
            {iconoDeArea(areas[pasoActual.areaIndex]?.key ?? "")}
          </span>
          {areaLabelActual} · Pregunta {numeroPreguntaEnArea} de máx.{" "}
          {preguntasAreaActual.length}
        </p>
        <h2 className="mb-6 text-xl font-semibold leading-snug">
          {pasoActual.pregunta.texto}
        </h2>

        <div
          role="radiogroup"
          aria-label={`Respuesta para: ${pasoActual.pregunta.texto}`}
          onKeyDown={(e) => {
            // Atajo de teclado: los números 1-5 seleccionan directamente
            // (requisito explícito del prompt maestro para el selector Likert).
            const num = Number(e.key);
            if (num >= 1 && num <= 5) {
              e.preventDefault();
              onSeleccionar(num);
              return;
            }
            // Navegación por flechas entre las 5 opciones + Enter/Espacio
            // para confirmar la opción con foco (semántica de radiogroup).
            const idxActual = ESCALA_LIKERT.findIndex((o) => o.valor === respuestaActual);
            if (e.key === "ArrowRight" || e.key === "ArrowDown") {
              e.preventDefault();
              const siguiente = ESCALA_LIKERT[Math.min(idxActual + 1, 4)] ?? ESCALA_LIKERT[0];
              onSeleccionar(siguiente.valor);
              document.getElementById(`likert-${siguiente.valor}`)?.focus();
            } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
              e.preventDefault();
              const anterior = ESCALA_LIKERT[Math.max(idxActual - 1, 0)] ?? ESCALA_LIKERT[0];
              onSeleccionar(anterior.valor);
              document.getElementById(`likert-${anterior.valor}`)?.focus();
            }
          }}
          className="grid grid-cols-1 gap-2 sm:grid-cols-5"
        >
          {ESCALA_LIKERT.map((opcion) => (
            <button
              key={opcion.valor}
              id={`likert-${opcion.valor}`}
              type="button"
              role="radio"
              aria-checked={respuestaActual === opcion.valor}
              tabIndex={
                respuestaActual === opcion.valor || (respuestaActual === undefined && opcion.valor === 1)
                  ? 0
                  : -1
              }
              onClick={() => onSeleccionar(opcion.valor)}
              style={
                respuestaActual === opcion.valor
                  ? undefined
                  : { backgroundColor: `hsl(var(--accent) / ${opcion.tinte})` }
              }
              className={`flex min-h-[72px] flex-col items-center justify-center gap-1 rounded-xl border-2 px-2 py-3 text-center text-xs font-medium transition-colors ${
                respuestaActual === opcion.valor
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <span className="text-lg" aria-hidden="true">
                {opcion.emoji}
              </span>
              <span>{opcion.valor}</span>
              <span className="leading-tight">{opcion.label}</span>
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Puedes usar las flechas del teclado o pulsar directamente el número 1–5.
        </p>
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={onAnterior}
          disabled={cursor === 0}
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          ← Anterior
        </button>
        <span className="text-xs text-muted-foreground">Guardado automáticamente</span>
        <button
          onClick={onSiguiente}
          disabled={respuestaActual === undefined}
          className="rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground disabled:opacity-40"
        >
          Siguiente →
        </button>
      </div>
    </main>
  );
}

/**
 * Skeleton que imita la estructura real de la pantalla del formulario
 * (barra de progreso + tarjeta de pregunta + botones de navegación), en vez
 * de un spinner genérico de pantalla completa. Se usa tanto durante la
 * carga inicial de áreas/preguntas como en el instante de transición entre
 * pasos, para que el usuario nunca vea una pantalla en blanco.
 */
function SkeletonFormulario() {
  return (
    <main
      id="contenido"
      role="status"
      aria-live="polite"
      className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-4 py-8"
    >
      <span className="sr-only">Cargando el banco de preguntas…</span>
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="flex gap-1">
          {Array.from({ length: 17 }).map((_, i) => (
            <Skeleton key={i} className="h-1.5 flex-1 rounded-full" />
          ))}
        </div>
      </div>
      <div className="rounded-2xl border border-border bg-muted/40 p-6 shadow-sm">
        <Skeleton className="mb-3 h-3 w-40" />
        <Skeleton className="mb-6 h-6 w-full" />
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-[72px] w-full rounded-xl" />
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <Skeleton className="h-9 w-24 rounded-lg" />
        <Skeleton className="h-9 w-28 rounded-lg" />
      </div>
    </main>
  );
}

/**
 * Skeleton mostrado mientras se envía el test y se calcula la
 * recomendación: imita la estructura de la pantalla de resultados que está
 * a punto de aparecer (radar + tarjetas), en vez de un spinner genérico.
 */
function SkeletonEnviando() {
  return (
    <main
      id="contenido"
      role="status"
      aria-live="polite"
      className="mx-auto flex max-w-4xl flex-col gap-8 px-4 py-10"
    >
      <span className="sr-only">Calculando tu recomendación con Mahalanobis…</span>
      <div className="flex flex-col items-center gap-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-7 w-72" />
      </div>
      <Skeleton className="mx-auto h-[320px] w-full max-w-[420px] rounded-2xl" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-40 w-full rounded-2xl" />
        ))}
      </div>
    </main>
  );
}