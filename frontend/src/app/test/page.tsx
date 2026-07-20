"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Check, Clock, ListChecks, MessagesSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Breadcrumb } from "@/components/breadcrumb";

const METODOS = [
  {
    icono: ListChecks,
    titulo: "Test Tradicional",
    descripcion:
      "Responde un cuestionario con escala Likert, hasta 85 preguntas, una por una, con recorte inteligente por área.",
    beneficios: [
      "Ves tu progreso por área en todo momento",
      "Puedes volver atrás y corregir respuestas",
      "Ideal si prefieres avanzar a tu propio ritmo",
    ],
    tiempoEstimado: "10–15 min",
    boton: "Comenzar Test",
    href: "/test/tradicional",
    disponible: true,
  },
  {
    icono: MessagesSquare,
    titulo: "Test con Chatbot",
    descripcion:
      "Responde el mismo banco de preguntas conversando con un chatbot basado en reglas, que también recorta preguntas según tus intereses.",
    beneficios: [
      "Experiencia conversacional guiada, sin formularios",
      "Botones rápidos numerados del 1 al 5",
      "Retoma la conversación donde la dejaste",
    ],
    tiempoEstimado: "10–15 min",
    boton: "Iniciar Chat",
    href: "/test/chatbot",
    disponible: true,
  },
];

export default function SeleccionMetodoPage() {
  const [continuarInvitado, setContinuarInvitado] = useState(true);

  return (
    <main id="contenido" className="min-h-screen">
      <Breadcrumb items={[{ label: "Test" }]} />

      <div className="container pb-20 pt-4">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            ¿Cómo prefieres realizar el test?
          </h1>
          <p className="mt-3 text-muted-foreground">
            Ambos métodos usan el mismo banco de preguntas y el mismo motor de
            recomendación: llegarás al mismo resultado por el camino que
            prefieras.
          </p>
        </div>

        <div className="mx-auto mt-8 flex max-w-md items-start gap-3 rounded-xl border border-border bg-muted/40 p-4 text-left">
          <input
            id="continuar-invitado"
            type="checkbox"
            checked={continuarInvitado}
            onChange={(e) => setContinuarInvitado(e.target.checked)}
            className="mt-1 h-4 w-4 shrink-0 accent-primary"
          />
          <label htmlFor="continuar-invitado" className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">Continuar como invitado.</span>{" "}
            Podrás hacer el test sin crear una cuenta. Ten en cuenta que solo los
            intentos realizados con sesión iniciada quedan guardados en{" "}
            <Link href="/historial" className="underline underline-offset-2 hover:text-primary">
              Mis resultados anteriores
            </Link>
            ; como invitado, el resultado solo estará disponible en esta sesión del
            navegador.
          </label>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          {METODOS.map((metodo, i) => (
            <motion.div
              key={metodo.titulo}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: "easeOut", delay: i * 0.1 }}
              className="flex flex-col rounded-2xl border border-border bg-card p-8"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <metodo.icono className="h-6 w-6" />
                </span>
                <span className="flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" />
                  {metodo.tiempoEstimado}
                </span>
              </div>

              <h2 className="mt-5 font-display text-xl font-semibold">{metodo.titulo}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {metodo.descripcion}
              </p>

              <ul className="mt-5 flex flex-1 flex-col gap-2.5">
                {metodo.beneficios.map((beneficio) => (
                  <li key={beneficio} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                    <span className="text-foreground/90">{beneficio}</span>
                  </li>
                ))}
              </ul>

              <Button
                asChild
                size="lg"
                className="mt-7"
                variant={metodo.disponible ? "default" : "outline"}
              >
                <Link href={metodo.href}>
                  {metodo.boton}
                  {!metodo.disponible && (
                    <span className="ml-1 text-xs font-normal opacity-80">(próximamente)</span>
                  )}
                </Link>
              </Button>
            </motion.div>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Button asChild variant="ghost">
            <Link href="/">
              <ArrowLeft className="h-4 w-4" />
              Volver al inicio
            </Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
