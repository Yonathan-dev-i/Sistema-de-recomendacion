"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import {
  ApiError,
  iniciarSesion,
  obtenerPerfil,
  refrescarToken,
  registrarUsuario,
  type Usuario,
} from "@/lib/api";

type AuthState = {
  usuario: Usuario | null;
  accessToken: string | null;
  refreshToken: string | null;
  /** true mientras se resuelve la sesión (login/registro/refresh en curso). */
  cargando: boolean;

  registrarse: (datos: {
    nombre_completo: string;
    email: string;
    password: string;
  }) => Promise<void>;
  iniciarSesion: (datos: { email: string; password: string }) => Promise<void>;
  cerrarSesion: () => void;
  /**
   * Intenta renovar el access token con el refresh token guardado. Si el
   * refresh también es inválido/expiró, limpia la sesión por completo
   * (equivalente a un logout silencioso).
   */
  refrescarSesion: () => Promise<string | null>;
};

/**
 * Estado global de sesión (Fase 9a). El token se guarda en `localStorage`
 * (vía el middleware `persist` de Zustand) para sobrevivir a un refresh de
 * página; el refresh automático del access token vencido ocurre bajo demanda
 * en `refrescarSesion`, pensado para ser llamado por cualquier fetch
 * protegido que reciba un 401.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      usuario: null,
      accessToken: null,
      refreshToken: null,
      cargando: false,

      async registrarse(datos) {
        set({ cargando: true });
        try {
          const resultado = await registrarUsuario(datos);
          set({
            usuario: resultado.usuario,
            accessToken: resultado.access_token,
            refreshToken: resultado.refresh_token,
          });
        } finally {
          set({ cargando: false });
        }
      },

      async iniciarSesion(datos) {
        set({ cargando: true });
        try {
          const resultado = await iniciarSesion(datos);
          set({
            usuario: resultado.usuario,
            accessToken: resultado.access_token,
            refreshToken: resultado.refresh_token,
          });
        } finally {
          set({ cargando: false });
        }
      },

      cerrarSesion() {
        set({ usuario: null, accessToken: null, refreshToken: null });
      },

      async refrescarSesion() {
        const { refreshToken } = get();
        if (!refreshToken) return null;
        try {
          const resultado = await refrescarToken(refreshToken);
          set({
            usuario: resultado.usuario,
            accessToken: resultado.access_token,
            refreshToken: resultado.refresh_token,
          });
          return resultado.access_token;
        } catch (err) {
          if (err instanceof ApiError && err.status === 401) {
            set({ usuario: null, accessToken: null, refreshToken: null });
          }
          return null;
        }
      },
    }),
    {
      name: "vocacional_auth",
      partialize: (state) => ({
        usuario: state.usuario,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
);

/**
 * Valida la sesión persistida contra el backend (`GET /auth/me`) al montar
 * la app. Si el access token guardado ya expiró, intenta renovarlo con el
 * refresh token antes de darse por vencido.
 */
export async function validarSesionActual(): Promise<void> {
  const { accessToken, refrescarSesion, cerrarSesion } = useAuthStore.getState();
  if (!accessToken) return;

  try {
    const usuario = await obtenerPerfil(accessToken);
    useAuthStore.setState({ usuario });
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      const nuevoToken = await refrescarSesion();
      if (!nuevoToken) cerrarSesion();
    }
  }
}
