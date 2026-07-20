"use client";

import { memo, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Bot, History, ListChecks, LogIn } from "lucide-react";

import { Breadcrumb } from "@/components/breadcrumb";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { ApiError, IntentoResumen, obtenerMisIntentos } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

const FORMATO_FECHA: Intl.DateTimeFormatOptions = {
  year: "numeric",
  month: "long",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
};

const ETIQUETA_ESTADO: Record<IntentoResumen["estado"], string> = {
  completado: "Completado",
  en_progreso: "En progreso",
  abandonado: "Abandonado",
};

export default function HistorialPage() {
  const usuario = useAuthStore((s) => s.usuario);
  const accessToken = useAuthStore((s) => s.accessToken);
  const cargandoSesion = useAuthStore((s) => s.cargando);

  const [intentos, setIntentos] = useState<IntentoResumen[] | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const cargar = useCallback(() => {
    if (!accessToken) return;
    setErrorMsg(null);
    setIntentos(null);
    obtenerMisIntentos(accessToken)
      .then(setIntentos)
      .catch((err) => {
        setErrorMsg(err instanceof ApiError ? err.message : "Error de conexión con el backend.");
      });
  }, [accessToken]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  return (
    <main id="contenido" className="min-h-screen">
      <Breadcrumb items={[{ label: "Mis resultados anteriores" }]} />

      <div className="container max-w-3xl pb-20 pt-4">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <History className="h-5 w-5" />
          </span>
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Mis resultados anteriores
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Línea de tiempo de los tests que realizaste con tu cuenta.
            </p>
          </div>
        </div>

        <div className="mt-8">
          {!usuario ? (
            !cargandoSesion && <RequiereSesion />
          ) : errorMsg ? (
            <ErrorState
              message={`No se pudo cargar tu historial (${errorMsg}).`}
              onRetry={cargar}
            />
          ) : intentos === null ? (
            <div className="flex flex-col gap-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : intentos.length === 0 ? (
            <ListaVacia />
          ) : (
            <ol className="flex flex-col gap-4">
              {intentos.map((intento) => (
                <TarjetaIntento key={intento.id} intento={intento} />
              ))}
            </ol>
          )}
        </div>
      </div>
    </main>
  );
}

function RequiereSesion() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border bg-muted/30 px-6 py-12 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
        <LogIn className="h-6 w-6" />
      </span>
      <div>
        <p className="font-medium text-foreground">Necesitas una cuenta para ver tu historial</p>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          Los intentos realizados como invitado no se guardan a tu nombre. Inicia
          sesión (o crea una cuenta gratuita) antes de comenzar el test para que
          tus resultados queden aquí, ordenados por fecha.
        </p>
      </div>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/login">Iniciar sesión</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/registro">Crear cuenta</Link>
        </Button>
      </div>
    </div>
  );
}

function ListaVacia() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border bg-muted/30 px-6 py-12 text-center">
      <p className="font-medium text-foreground">Todavía no tienes intentos guardados</p>
      <p className="max-w-md text-sm text-muted-foreground">
        Cuando completes el test estando logueado, tu resultado aparecerá acá
        automáticamente.
      </p>
      <Button asChild>
        <Link href="/test">Realizar el test</Link>
      </Button>
    </div>
  );
}

// Fase 9f: `memo` — la línea de tiempo puede tener muchos intentos, y sin
// memoizar cada re-render de la página (ej. al reintentar tras un error)
// re-montaba las N tarjetas aunque sus datos no cambiaran.
const TarjetaIntento = memo(function TarjetaIntento({ intento }: { intento: IntentoResumen }) {
  const fecha = new Date(intento.completado_en ?? intento.iniciado_en).toLocaleDateString(
    "es-PE",
    FORMATO_FECHA,
  );
  const Icono = intento.metodo === "tradicional" ? ListChecks : Bot;

  const contenido = (
    <>
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
        <Icono className="h-5 w-5" />
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span>{fecha}</span>
          <span aria-hidden="true">·</span>
          <span>{intento.metodo === "tradicional" ? "Test tradicional" : "Chatbot"}</span>
          {intento.estado !== "completado" && (
            <span className="rounded-full bg-muted px-2 py-0.5 font-medium text-foreground">
              {ETIQUETA_ESTADO[intento.estado]}
            </span>
          )}
        </div>
        <p className="mt-1 truncate font-medium text-foreground">
          {intento.carrera_top1 ?? "Sin resultado calculado todavía"}
        </p>
      </div>

      {intento.estado === "completado" && intento.afinidad_top1_pct !== null && (
        <span className="shrink-0 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
          {intento.afinidad_top1_pct.toFixed(1)}%
        </span>
      )}
    </>
  );

  if (intento.carrera_top1_id !== null) {
    return (
      <li>
        <Link
          href={`/carrera/${intento.carrera_top1_id}`}
          className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4 transition-colors hover:border-primary/50 sm:p-5"
        >
          {contenido}
        </Link>
      </li>
    );
  }

  return (
    <li className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4 sm:p-5">
      {contenido}
    </li>
  );
});
