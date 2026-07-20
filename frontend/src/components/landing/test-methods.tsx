"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Check, ListChecks, MessagesSquare } from "lucide-react";

import { Button } from "@/components/ui/button";

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
    boton: "Iniciar Chat",
    href: "/test/chatbot",
    disponible: false,
  },
];

export function TestMethods() {
  return (
    <section id="metodos" className="scroll-mt-20 py-16 sm:py-24">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-[42px]">
            Métodos del Test
          </h2>
          <p className="mt-3 text-muted-foreground">
            Elige la forma de responder que más se ajuste a ti. Ambos métodos
            usan el mismo banco de preguntas y el mismo motor de
            recomendación.
          </p>
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          {METODOS.map((metodo, i) => (
            <motion.div
              key={metodo.titulo}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.45, ease: "easeOut", delay: i * 0.1 }}
              whileHover={{ y: -4 }}
              className="glass-panel flex flex-col rounded-2xl p-8"
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-brand text-white">
                <metodo.icono className="h-6 w-6" />
              </span>
              <h3 className="mt-5 font-display text-xl font-semibold">{metodo.titulo}</h3>
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

              <Button asChild size="lg" className="mt-7" variant={metodo.disponible ? "gradient" : "outline"}>
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
      </div>
    </section>
  );
}