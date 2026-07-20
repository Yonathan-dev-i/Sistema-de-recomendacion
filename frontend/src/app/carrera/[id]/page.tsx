"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, GraduationCap } from "lucide-react";

import { Area, ApiError, CarreraDetalle, obtenerAreas, obtenerCarreraDetalle } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { Breadcrumb } from "@/components/breadcrumb";
import { RadarChart } from "@/components/resultados/radar-chart";
import { leerUltimoResultado, type UltimoResultado } from "@/lib/ultimo-resultado";

type Estado = "cargando" | "error" | "listo";

export default function CarreraDetallePage() {
  const params = useParams<{ id: string }>();
  const carreraId = Number(params.id);

  const [estado, setEstado] = useState<Estado>("cargando");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [carrera, setCarrera] = useState<CarreraDetalle | null>(null);
  const [areas, setAreas] = useState<Area[]>([]);
  const [ultimoResultado, setUltimoResultado] = useState<UltimoResultado | null>(null);
  const [compararConMiPerfil, setCompararConMiPerfil] = useState(false);

  useEffect(() => {
    setUltimoResultado(leerUltimoResultado());
  }, []);

  const cargar = () => {
    setEstado("cargando");
    Promise.all([obtenerCarreraDetalle(carreraId), obtenerAreas()])
      .then(([carreraData, areasData]) => {
        setCarrera(carreraData);
        setAreas([...areasData].sort((a, b) => a.orden - b.orden));
        setEstado("listo");
      })
      .catch((err) => {
        setErrorMsg(
          err instanceof ApiError ? err.message : "Error de conexión con el backend.",
        );
        setEstado("error");
      });
  };

  useEffect(cargar, [carreraId]);

  return (
    <main id="contenido" className="min-h-screen">
      <Breadcrumb items={[{ label: "Carreras", href: "/#carreras" }, { label: carrera?.nombre ?? "Detalle" }]} />

      <div className="container max-w-3xl pb-20 pt-4">
        {estado === "cargando" && (
          <div className="space-y-6">
            <Skeleton className="h-10 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
            <div className="space-y-3">
              {Array.from({ length: 17 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          </div>
        )}

        {estado === "error" && (
          <ErrorState
            message={`No se pudo cargar el detalle de esta carrera (${errorMsg}).`}
            onRetry={cargar}
          />
        )}

        {estado === "listo" && carrera && (
          <>
            <div className="flex items-center gap-4">
              <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <GraduationCap className="h-7 w-7" />
              </span>
              <div>
                <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
                  {carrera.nombre}
                </h1>
                <p className="text-muted-foreground">
                  {carrera.facultad ?? "Facultad no especificada"}
                </p>
              </div>
            </div>

            <div className="mt-10">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="font-display text-lg font-semibold">Perfil de 17 áreas</h2>
                {ultimoResultado && (
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={compararConMiPerfil}
                      onChange={(e) => setCompararConMiPerfil(e.target.checked)}
                      className="h-4 w-4 rounded border-border"
                    />
                    Comparar con mi perfil
                  </label>
                )}
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                Puntaje de referencia de esta carrera en cada área evaluada por el test
                (escala 1–5), visualizado como el mismo gráfico radar usado en la
                pantalla de resultados.
              </p>

              <div className="mt-6">
                <RadarChart
                  areas={areas}
                  series={
                    compararConMiPerfil && ultimoResultado
                      ? [
                          { label: "Tu perfil", color: "#a5303f", valores: ultimoResultado.vectorUsuario },
                          { label: carrera.nombre, color: "#c9a227", valores: carrera.perfil_areas },
                        ]
                      : [{ label: carrera.nombre, color: "#a5303f", valores: carrera.perfil_areas }]
                  }
                />
              </div>
            </div>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link href="/test">Descubre tu afinidad con esta carrera</Link>
              </Button>
              <Button asChild size="lg" variant="ghost">
                <Link href="/#carreras">
                  <ArrowLeft className="h-4 w-4" />
                  Volver al catálogo
                </Link>
              </Button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
