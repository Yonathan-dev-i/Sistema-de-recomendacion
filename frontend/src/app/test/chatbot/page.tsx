"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, User } from "lucide-react";

import { Breadcrumb } from "@/components/breadcrumb";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import {
  ApiError,
  ChatbotResultado,
  MensajeChat,
  enviarMensajeChat,
  iniciarChat,
  reanudarChat,
} from "@/lib/api";
import { PantallaResultados } from "@/components/resultados/pantalla-resultados";
import { useAuthStore } from "@/lib/auth-store";

const STORAGE_KEY = "vocacional_chatbot_sesion_id";

type EstadoUI = "cargando" | "conversando" | "error";

export default function ChatbotPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [estado, setEstado] = useState<EstadoUI>("cargando");
  const [sesionId, setSesionId] = useState<number | null>(null);
  const [mensajes, setMensajes] = useState<MensajeChat[]>([]);
  const [chips, setChips] = useState<number[] | null>(null);
  const [escribiendo, setEscribiendo] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [texto, setTexto] = useState("");
  const [terminado, setTerminado] = useState(false);
  const [resultado, setResultado] = useState<ChatbotResultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false);
  const finRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void arrancarOResumirSesion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes, escribiendo]);

  async function arrancarOResumirSesion() {
    setEstado("cargando");
    setError(null);
    const guardado = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;

    try {
      if (guardado) {
        const id = Number(guardado);
        try {
          const sesion = await reanudarChat(id);
          setSesionId(sesion.sesion_id);
          setMensajes([
            ...sesion.historial,
            sesion.terminado
              ? { rol: "bot" as const, texto: "Continuemos donde lo dejamos: tu resultado ya está listo abajo." }
              : { rol: "bot" as const, texto: "Continuemos donde lo dejamos." },
          ]);
          setChips(sesion.chips);
          setTerminado(sesion.terminado);
          setResultado(sesion.resultado);
          setEstado("conversando");
          return;
        } catch {
          // La sesión guardada ya no existe (p.ej. reinicio del backend): se
          // descarta y se inicia una nueva, en vez de dejar al usuario varado.
          localStorage.removeItem(STORAGE_KEY);
        }
      }

      const inicio = await iniciarChat(accessToken);
      setSesionId(inicio.sesion_id);
      setMensajes(inicio.mensajes.map((m) => ({ rol: "bot" as const, texto: m.texto })));
      setChips(inicio.chips);
      localStorage.setItem(STORAGE_KEY, String(inicio.sesion_id));
      setEstado("conversando");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo conectar con el chatbot.");
      setEstado("error");
    }
  }

  /**
   * Descarta la sesión actual (aunque el cuestionario no esté terminado) y
   * arranca una conversación completamente nueva. Se usa desde el botón
   * "Empezar de nuevo", tras la confirmación del modal.
   */
  async function empezarDeNuevo() {
    setMostrarConfirmacion(false);
    if (typeof window !== "undefined") localStorage.removeItem(STORAGE_KEY);
    setEstado("cargando");
    setError(null);
    setMensajes([]);
    setChips(null);
    setTerminado(false);
    setResultado(null);

    try {
      const inicio = await iniciarChat(accessToken);
      setSesionId(inicio.sesion_id);
      setMensajes(inicio.mensajes.map((m) => ({ rol: "bot" as const, texto: m.texto })));
      setChips(inicio.chips);
      localStorage.setItem(STORAGE_KEY, String(inicio.sesion_id));
      setEstado("conversando");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo conectar con el chatbot.");
      setEstado("error");
    }
  }

  async function enviar(valor: string) {
    if (!sesionId || enviando || !valor.trim()) return;
    setEnviando(true);
    setMensajes((prev) => [...prev, { rol: "usuario", texto: valor }]);
    setTexto("");
    setChips(null);

    // Feedback inmediato: indicador de "escribiendo..." antes de la respuesta real.
    setEscribiendo(true);
    const espera = 400 + Math.random() * 400;

    try {
      const respuesta = await enviarMensajeChat(sesionId, valor);
      await new Promise((r) => setTimeout(r, espera));
      setMensajes((prev) => [
        ...prev,
        ...respuesta.mensajes.map((m) => ({ rol: "bot" as const, texto: m.texto })),
      ]);
      setChips(respuesta.chips);
      setTerminado(respuesta.terminado);
      if (respuesta.resultado) setResultado(respuesta.resultado);
    } catch (err) {
      setMensajes((prev) => [
        ...prev,
        {
          rol: "bot",
          texto:
            err instanceof ApiError
              ? `Ocurrió un error: ${err.message}`
              : "No pude procesar tu respuesta, intenta de nuevo.",
        },
      ]);
    } finally {
      setEscribiendo(false);
      setEnviando(false);
    }
  }

  if (estado === "cargando") {
    return <SkeletonChat />;
  }

  if (estado === "error") {
    return (
      <main
        id="contenido"
        className="mx-auto flex min-h-screen w-full max-w-2xl flex-col items-center justify-center px-4 py-8"
      >
        <ErrorState
          message={error ?? "No se pudo iniciar el chat."}
          onRetry={() => void arrancarOResumirSesion()}
        />
      </main>
    );
  }

  if (terminado && resultado) {
    return (
      <main id="contenido">
        <PantallaResultados
          testId={resultado.test_id}
          vectorUsuario={resultado.vector_usuario}
          resultados={resultado.resultados}
          metodo="chatbot"
        />
      </main>
    );
  }

  return (
    <main id="contenido" className="flex min-h-screen flex-col">
      <div className="mx-auto flex w-full max-w-2xl items-center justify-between px-4">
        <Breadcrumb items={[{ label: "Test", href: "/test" }, { label: "Chatbot" }]} />
        <button
          type="button"
          onClick={() => setMostrarConfirmacion(true)}
          className="min-h-[36px] shrink-0 rounded-lg border border-border bg-background px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          Empezar de nuevo
        </button>
      </div>

      {mostrarConfirmacion && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-confirmacion-reinicio"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
          onClick={() => setMostrarConfirmacion(false)}
        >
          <div
            className="w-full max-w-sm rounded-2xl border border-border bg-background p-5 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="titulo-confirmacion-reinicio" className="text-base font-semibold text-foreground">
              ¿Empezar de nuevo?
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Se descartará tu conversación actual y el progreso del cuestionario. Esta acción no se puede deshacer.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={() => setMostrarConfirmacion(false)}>
                Cancelar
              </Button>
              <Button type="button" onClick={() => void empezarDeNuevo()}>
                Sí, empezar de nuevo
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 pb-4">
        <div
          role="log"
          aria-live="polite"
          className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-2xl border border-border bg-muted/30 p-4"
          style={{ maxHeight: "60vh", minHeight: "50vh" }}
        >
          <AnimatePresence initial={false}>
            {mensajes.map((m, i) => (
              <Burbuja key={i} mensaje={m} />
            ))}
          </AnimatePresence>
          {escribiendo && <IndicadorEscribiendo />}
          <div ref={finRef} />
        </div>

        {!terminado && (
          <div className="mt-4 flex flex-col gap-2">
            {chips && (
              <div className="flex flex-wrap gap-2" role="group" aria-label="Respuestas rápidas">
                {chips.map((n) => (
                  <button
                    key={n}
                    type="button"
                    disabled={enviando}
                    aria-label={`Responder ${n}`}
                    onClick={() => void enviar(String(n))}
                    className="min-h-[44px] min-w-[44px] rounded-xl border border-primary/30 bg-background px-4 py-2 text-sm font-semibold text-primary transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50"
                  >
                    {n}
                  </button>
                ))}
              </div>
            )}
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                void enviar(texto);
              }}
            >
              <input
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                disabled={enviando}
                placeholder="Escribe tu respuesta, una pregunta (ej. '¿cuánto dura?') o un comando ('ayuda')..."
                aria-label="Mensaje al chatbot"
                className="h-11 flex-1 rounded-lg border border-border bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <Button type="submit" disabled={enviando || !texto.trim()}>
                Enviar
              </Button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}

function Burbuja({ mensaje }: { mensaje: MensajeChat }) {
  const esBot = mensaje.rol === "bot";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex items-end gap-2 ${esBot ? "justify-start" : "justify-end"}`}
    >
      {esBot && (
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
          <Bot className="h-4 w-4" />
        </span>
      )}
      <div
        className={`max-w-[80%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm ${
          esBot
            ? "rounded-bl-sm bg-background text-foreground shadow-sm"
            : "rounded-br-sm bg-primary text-primary-foreground"
        }`}
      >
        {mensaje.texto}
      </div>
      {!esBot && (
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <User className="h-4 w-4" />
        </span>
      )}
    </motion.div>
  );
}

function IndicadorEscribiendo() {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
        <Bot className="h-4 w-4" />
      </span>
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-background px-4 py-3 shadow-sm">
        <span className="sr-only">El orientador vocacional está escribiendo…</span>
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            aria-hidden="true"
            className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Skeleton que imita la estructura real de la ventana de chat (burbujas
 * alternadas + chips numerados) mientras se inicia o retoma la sesión,
 * en vez de un spinner genérico de pantalla completa.
 */
function SkeletonChat() {
  return (
    <main id="contenido" className="flex min-h-screen flex-col">
      <Breadcrumb items={[{ label: "Test", href: "/test" }, { label: "Chatbot" }]} />
      <div
        className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 pb-4"
        role="status"
        aria-live="polite"
      >
        <span className="sr-only">Conectando con tu orientador vocacional…</span>
        <div
          className="flex flex-1 flex-col gap-3 rounded-2xl border border-border bg-muted/30 p-4"
          style={{ maxHeight: "60vh", minHeight: "50vh" }}
        >
          <Skeleton className="h-10 w-2/3 rounded-2xl rounded-bl-sm" />
          <Skeleton className="ml-auto h-8 w-1/2 rounded-2xl rounded-br-sm" />
          <Skeleton className="h-14 w-3/4 rounded-2xl rounded-bl-sm" />
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-11 w-11 rounded-xl" />
          ))}
        </div>
      </div>
    </main>
  );
}