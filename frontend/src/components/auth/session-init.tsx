"use client";

import { useEffect } from "react";

import { validarSesionActual } from "@/lib/auth-store";

/**
 * Componente sin UI: al montar el árbol (una sola vez, desde `layout.tsx`),
 * valida el access token persistido contra `GET /auth/me` y, si expiró,
 * intenta renovarlo con el refresh token. Así, tras un refresh de página, el
 * Header y cualquier pantalla que dependa de `useAuthStore` reflejan el
 * estado real de la sesión en vez de confiar ciegamente en lo guardado en
 * `localStorage`.
 */
export function SessionInit() {
  useEffect(() => {
    void validarSesionActual();
  }, []);

  return null;
}
