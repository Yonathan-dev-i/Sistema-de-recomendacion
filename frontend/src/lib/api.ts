/**
 * Cliente API del backend FastAPI. Centraliza los tipos y llamadas fetch
 * usadas por el flujo del Test Tradicional (Fase 4).
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Area = {
  key: string;
  label: string;
  orden: number;
};

export type Pregunta = {
  id: number;
  area: string;
  texto: string;
};

export type RespuestaItem = {
  pregunta_id: number;
  respuesta: number;
};

export type CarreraResumen = {
  id: number;
  nombre: string;
  facultad: string | null;
};

export type CarreraDetalle = {
  id: number;
  nombre: string;
  facultad: string | null;
  perfil_areas: Record<string, number>;
};

export type ResultadoCarrera = {
  carrera_id: number;
  nombre: string;
  distancia_mahalanobis: number;
  afinidad_pct: number;
  explicacion: string;
  fortalezas: string[];
  areas_por_mejorar: string[];
};

export type TestTradicionalOut = {
  test_id: number;
  vector_usuario: Record<string, number>;
  resultados: ResultadoCarrera[];
};

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detalle = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detalle = String(body.detail);
    } catch {
      // sin cuerpo JSON, se conserva el mensaje genérico
    }
    throw new ApiError(detalle, res.status);
  }
  return res.json() as Promise<T>;
}

/**
 * Igual que `fetchJson`, pero agrega el header `Authorization: Bearer` cuando
 * hay un access token disponible. Usado por los endpoints protegidos
 * (Fase 9a en adelante, ej. `/auth/me`, y el historial de la Fase 9b).
 */
async function fetchJsonAutenticado<T>(
  path: string,
  accessToken: string,
  init?: RequestInit,
): Promise<T> {
  return fetchJson<T>(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.headers ?? {}),
    },
  });
}

export function obtenerAreas(): Promise<Area[]> {
  return fetchJson<Area[]>("/areas");
}

export function obtenerPreguntas(): Promise<Pregunta[]> {
  return fetchJson<Pregunta[]>("/preguntas");
}

export function obtenerCarreras(): Promise<CarreraResumen[]> {
  return fetchJson<CarreraResumen[]>("/carreras");
}

export function obtenerCarreraDetalle(id: number): Promise<CarreraDetalle> {
  return fetchJson<CarreraDetalle>(`/carrera/${id}`);
}

// --- Método 2: Chatbot basado en reglas (Fase 6) ---------------------------

export type MensajeChat = {
  rol: "bot" | "usuario";
  texto: string;
};

export type ChatbotResultado = {
  test_id: number;
  vector_usuario: Record<string, number>;
  resultados: ResultadoCarrera[];
};

export type ChatbotIniciarOut = {
  sesion_id: number;
  mensajes: MensajeChat[];
  chips: number[] | null;
};

export type ChatbotMensajeOut = {
  mensajes: MensajeChat[];
  chips: number[] | null;
  terminado: boolean;
  resultado: ChatbotResultado | null;
};

export type ChatbotSesionOut = {
  sesion_id: number;
  fase: string;
  historial: MensajeChat[];
  chips: number[] | null;
  terminado: boolean;
  resultado: ChatbotResultado | null;
};

export function iniciarChat(accessToken?: string | null): Promise<ChatbotIniciarOut> {
  const init: RequestInit = { method: "POST" };
  return accessToken
    ? fetchJsonAutenticado<ChatbotIniciarOut>("/test/chatbot/iniciar", accessToken, init)
    : fetchJson<ChatbotIniciarOut>("/test/chatbot/iniciar", init);
}

export function enviarMensajeChat(
  sesionId: number,
  texto: string,
): Promise<ChatbotMensajeOut> {
  return fetchJson<ChatbotMensajeOut>(`/test/chatbot/${sesionId}/mensaje`, {
    method: "POST",
    body: JSON.stringify({ texto }),
  });
}

export function reanudarChat(sesionId: number): Promise<ChatbotSesionOut> {
  return fetchJson<ChatbotSesionOut>(`/test/chatbot/${sesionId}`);
}

export function enviarTestTradicional(
  respuestas: RespuestaItem[],
  accessToken?: string | null,
): Promise<TestTradicionalOut> {
  const init: RequestInit = { method: "POST", body: JSON.stringify({ respuestas }) };
  return accessToken
    ? fetchJsonAutenticado<TestTradicionalOut>("/test/tradicional", accessToken, init)
    : fetchJson<TestTradicionalOut>("/test/tradicional", init);
}

// --- Autenticación (Fase 9a) ------------------------------------------------

export type Usuario = {
  id: number;
  nombre_completo: string;
  email: string;
};

export type TokenOut = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  usuario: Usuario;
};

export function registrarUsuario(datos: {
  nombre_completo: string;
  email: string;
  password: string;
}): Promise<TokenOut> {
  return fetchJson<TokenOut>("/auth/registro", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function iniciarSesion(datos: { email: string; password: string }): Promise<TokenOut> {
  return fetchJson<TokenOut>("/auth/login", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function refrescarToken(refreshToken: string): Promise<TokenOut> {
  return fetchJson<TokenOut>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function obtenerPerfil(accessToken: string): Promise<Usuario> {
  return fetchJsonAutenticado<Usuario>("/auth/me", accessToken);
}

// --- Historial de intentos (Fase 9b) ----------------------------------------

export type IntentoResumen = {
  id: number;
  metodo: "tradicional" | "chatbot";
  estado: "en_progreso" | "completado" | "abandonado";
  iniciado_en: string;
  completado_en: string | null;
  carrera_top1_id: number | null;
  carrera_top1: string | null;
  afinidad_top1_pct: number | null;
};

/**
 * Lista los intentos del usuario autenticado, más reciente primero.
 * Requiere sesión activa (`401` si el token falta o expiró).
 */
export function obtenerMisIntentos(accessToken: string): Promise<IntentoResumen[]> {
  return fetchJsonAutenticado<IntentoResumen[]>("/usuarios/me/intentos", accessToken);
}

export { ApiError };
