"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { GraduationCap } from "lucide-react";

import { ApiError, CarreraResumen, obtenerCarreras } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";

type Estado = "cargando" | "error" | "listo";

export function CareersExplorer() {
  const [estado, setEstado] = useState<Estado>("cargando");
  const [carreras, setCarreras] = useState<CarreraResumen[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [facultadActiva, setFacultadActiva] = useState<string>("todas");

  const cargar = () => {
    setEstado("cargando");
    obtenerCarreras()
      .then((data) => {
        setCarreras(data);
        setEstado("listo");
      })
      .catch((err) => {
        setErrorMsg(err instanceof ApiError ? err.message : "Error de conexión con el backend.");
        setEstado("error");
      });
  };

  useEffect(cargar, []);

  const facultades = useMemo(() => {
    const set = new Set(carreras.map((c) => c.facultad ?? "Sin facultad"));
    return ["todas", ...Array.from(set).sort()];
  }, [carreras]);

  const carrerasFiltradas = useMemo(() => {
    if (facultadActiva === "todas") return carreras;
    return carreras.filter((c) => (c.facultad ?? "Sin facultad") === facultadActiva);
  }, [carreras, facultadActiva]);

  return (
    <section id="carreras" className="container scroll-mt-20 py-16 sm:py-24">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
          Explora las 37 carreras
        </h2>
        <p className="mt-3 text-muted-foreground">
          Este es el catálogo real de carreras de la UNA Puno contra el que se
          compara tu perfil vocacional.
        </p>
      </div>

      {estado === "listo" && facultades.length > 2 && (
        <div className="mt-8 flex flex-wrap justify-center gap-2">
          {facultades.map((f) => (
            <button
              key={f}
              onClick={() => setFacultadActiva(f)}
              className={`rounded-full border px-4 py-1.5 text-xs font-medium transition-colors ${
                facultadActiva === f
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-transparent text-muted-foreground hover:border-primary/40 hover:text-primary"
              }`}
            >
              {f === "todas" ? "Todas" : f}
            </button>
          ))}
        </div>
      )}

      <div className="mt-8">
        {estado === "cargando" && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 9 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-2xl" />
            ))}
          </div>
        )}

        {estado === "error" && (
          <ErrorState
            message={`No se pudo cargar el catálogo de carreras (${errorMsg}).`}
            onRetry={cargar}
            className="mx-auto max-w-md"
          />
        )}

        {estado === "listo" && carrerasFiltradas.length === 0 && (
          <p className="text-center text-sm text-muted-foreground">
            No hay carreras para esta facultad.
          </p>
        )}

        {estado === "listo" && carrerasFiltradas.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, amount: 0.15 }}
            transition={{ duration: 0.4 }}
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {carrerasFiltradas.map((carrera) => (
              <Link
                key={carrera.id}
                href={`/carrera/${carrera.id}`}
                className="group flex items-center gap-3 rounded-2xl border border-border bg-card p-4 transition-colors hover:border-primary/40 hover:bg-primary/5"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground">
                  <GraduationCap className="h-5 w-5" />
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-medium leading-snug">
                    {carrera.nombre}
                  </span>
                  <span className="block truncate text-xs text-muted-foreground">
                    {carrera.facultad ?? "Facultad no especificada"}
                  </span>
                </span>
              </Link>
            ))}
          </motion.div>
        )}
      </div>

      {estado === "listo" && (
        <div className="mt-10 text-center">
          <Button asChild variant="outline">
            <Link href="/test">Descubre cuál es la tuya</Link>
          </Button>
        </div>
      )}
    </section>
  );
}
