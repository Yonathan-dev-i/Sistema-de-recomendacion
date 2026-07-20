import type { ResultadoCarrera } from "@/lib/api";

const CLAVE = "vocacional_ultimo_resultado";

export type UltimoResultado = {
  testId: number;
  vectorUsuario: Record<string, number>;
  resultados: ResultadoCarrera[];
};

/**
 * Guarda en `localStorage` el último resultado calculado (por cualquiera de
 * los dos métodos), para que la página de detalle de carrera (`/carrera/{id}`)
 * pueda ofrecer el toggle "Comparar con mi perfil" descrito en la sección 6
 * del diseño UI/UX, sin necesitar un backend con sesión/autenticación (que
 * llega recién en la Fase 9).
 */
export function guardarUltimoResultado(data: UltimoResultado): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(data));
  } catch {
    // localStorage puede fallar (modo privado, cuota llena); no es crítico.
  }
}

export function leerUltimoResultado(): UltimoResultado | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CLAVE);
    if (!raw) return null;
    return JSON.parse(raw) as UltimoResultado;
  } catch {
    return null;
  }
}
