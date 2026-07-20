"use client";

import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

type ErrorStateProps = {
  message?: string;
  onRetry?: () => void;
  className?: string;
};

/**
 * Estado de error reutilizable para cualquier fetch fallido (preguntas,
 * carreras, envío de test, cálculo de recomendación), como pide la sección
 * "Componentes transversales (design system)" del prompt maestro.
 */
export function ErrorState({ message, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center gap-3 rounded-xl border border-danger/30 bg-danger/5 px-6 py-8 text-center ${className ?? ""}`}
      role="alert"
    >
      <AlertTriangle className="h-8 w-8 text-danger" aria-hidden="true" />
      <p className="text-sm text-foreground">
        {message ?? "No se pudo cargar la información. Verifica tu conexión e inténtalo de nuevo."}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </div>
  );
}
