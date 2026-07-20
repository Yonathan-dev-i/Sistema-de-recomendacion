"use client";

import { motion } from "framer-motion";
import { BrainCircuit, ClipboardList, ScanSearch, Trophy } from "lucide-react";

/**
 * El brief pide 4 pasos (Responder Test / Analizar Respuestas / IA Procesa /
 * Obtener Recomendaciones). El backend real solo tiene dos etapas técnicas
 * separadas (recorte adaptativo de preguntas → motor de Mahalanobis), así
 * que "Analizar respuestas" y "La IA procesa" se explican aquí como dos
 * momentos distintos de ESE mismo cálculo (normalización del perfil vs.
 * comparación contra las 37 carreras) para no inventar un paso que no
 * existe en el sistema real.
 */
const PASOS = [
  {
    numero: "01",
    icono: ClipboardList,
    titulo: "Responde el test",
    descripcion:
      "Hasta 85 preguntas en 17 áreas. El sistema recorta preguntas automáticamente según tus propias respuestas.",
  },
  {
    numero: "02",
    icono: ScanSearch,
    titulo: "Analizamos tus respuestas",
    descripcion:
      "Construimos tu perfil vocacional: un puntaje normalizado por cada una de las 17 áreas evaluadas.",
  },
  {
    numero: "03",
    icono: BrainCircuit,
    titulo: "La IA procesa tu perfil",
    descripcion:
      "Comparamos tu perfil contra el de 37 carreras con la Distancia de Mahalanobis, un modelo estadístico multivariado.",
  },
  {
    numero: "04",
    icono: Trophy,
    titulo: "Obtén tus recomendaciones",
    descripcion:
      "Recibe un Top 5 de carreras con el porcentaje de afinidad y una explicación clara de por qué encajan contigo.",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" as const } },
};

export function HowItWorks() {
  return (
    <section id="como-funciona" className="container scroll-mt-20 py-16 sm:py-24">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl font-bold tracking-tight sm:text-[42px]">
          ¿Cómo funciona?
        </h2>
        <p className="mt-3 text-muted-foreground">
          Cuatro pasos entre tú y una recomendación estadísticamente
          fundamentada.
        </p>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.3 }}
        className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4"
      >
        {PASOS.map((paso) => (
          <motion.div
            key={paso.numero}
            variants={item}
            whileHover={{ y: -6 }}
            className="glass-panel relative rounded-2xl p-6"
          >
            <span className="font-display text-4xl font-bold text-primary/25">
              {paso.numero}
            </span>
            <span className="mt-3 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-brand text-white">
              <paso.icono className="h-5 w-5" />
            </span>
            <h3 className="mt-4 font-display text-lg font-semibold">{paso.titulo}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {paso.descripcion}
            </p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}