"use client";

import { motion } from "framer-motion";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const FAQS = [
  {
    pregunta: "¿Cuánto dura el test?",
    respuesta:
      "Depende de tus respuestas: el sistema recorta preguntas automáticamente por área, así que puede tomar entre 10 y 20 minutos aproximadamente, tanto en el formulario como en el chatbot.",
  },
  {
    pregunta: "¿Mis datos son privados?",
    respuesta:
      "Tus respuestas se usan únicamente para calcular tu recomendación vocacional y quedan asociadas a tu intento de test para fines de trazabilidad. No se comparten con terceros.",
  },
  {
    pregunta: "¿Puedo repetir el test?",
    respuesta:
      "Sí. Puedes realizar el test tantas veces como quieras, ya sea con el formulario tradicional o con el chatbot, y cada intento se calcula de forma independiente.",
  },
  {
    pregunta: "¿Qué diferencia hay entre el formulario y el chatbot?",
    respuesta:
      "Ambos usan exactamente el mismo banco de preguntas y el mismo motor de recomendación (Distancia de Mahalanobis), por lo que ante las mismas respuestas producen el mismo resultado. La diferencia es solo la experiencia: un formulario paso a paso o una conversación guiada.",
  },
  {
    pregunta: "¿Cómo se calcula la recomendación?",
    respuesta:
      "Construimos un vector de 17 áreas a partir de tus respuestas y lo comparamos estadísticamente contra el perfil de 37 carreras de la UNA Puno usando la Distancia de Mahalanobis, que considera la correlación entre áreas en vez de una simple distancia euclidiana.",
  },
];

export function Faq() {
  return (
    <section id="faq" className="scroll-mt-20 bg-muted/40 py-16 sm:py-24">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Preguntas frecuentes
          </h2>
          <p className="mt-3 text-muted-foreground">
            Si tienes otra duda, escríbenos a orientacion@unap.edu.pe.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="mx-auto mt-10 max-w-2xl rounded-2xl border border-border bg-card px-6"
        >
          <Accordion type="single" collapsible className="w-full">
            {FAQS.map((f, i) => (
              <AccordionItem key={f.pregunta} value={`item-${i}`}>
                <AccordionTrigger>{f.pregunta}</AccordionTrigger>
                <AccordionContent>{f.respuesta}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
}
