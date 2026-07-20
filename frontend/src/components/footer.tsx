import Link from "next/link";
import { GraduationCap, Mail, MapPin } from "lucide-react";

export function Footer() {
  const anio = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-muted/40">
      <div className="container grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <div className="flex items-center gap-2 font-display text-lg font-bold">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <GraduationCap className="h-5 w-5" />
            </span>
            Orientación Vocacional UNA Puno
          </div>
          <p className="mt-3 max-w-sm text-sm text-muted-foreground">
            Sistema inteligente de orientación vocacional de la Universidad
            Nacional del Altiplano, basado en la Distancia de Mahalanobis
            sobre el perfil de 37 carreras profesionales.
          </p>
          <div className="mt-4 space-y-1.5 text-sm text-muted-foreground">
            <p className="flex items-center gap-2">
              <MapPin className="h-4 w-4 shrink-0" /> Av. Floral 1153, Puno,
              Perú
            </p>
            <p className="flex items-center gap-2">
              <Mail className="h-4 w-4 shrink-0" /> orientacion@unap.edu.pe
            </p>
          </div>
        </div>

        <div>
          <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-foreground">
            Navegación
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>
              <Link href="/#como-funciona" className="hover:text-primary">
                ¿Cómo funciona?
              </Link>
            </li>
            <li>
              <Link href="/#metodos" className="hover:text-primary">
                Métodos del test
              </Link>
            </li>
            <li>
              <Link href="/#carreras" className="hover:text-primary">
                Carreras
              </Link>
            </li>
            <li>
              <Link href="/#faq" className="hover:text-primary">
                Preguntas frecuentes
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-foreground">
            Legal
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>
              <span className="cursor-default">Política de privacidad</span>
            </li>
            <li>
              <span className="cursor-default">Términos de uso</span>
            </li>
          </ul>
          <h3 className="mt-6 font-display text-sm font-semibold uppercase tracking-wide text-foreground">
            Universidad
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>
              <span className="cursor-default">Facebook UNA Puno</span>
            </li>
            <li>
              <span className="cursor-default">unap.edu.pe</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="container flex flex-col gap-2 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>© {anio} Universidad Nacional del Altiplano — Puno. Todos los derechos reservados.</p>
          <p className="max-w-xl">
            Este sistema es una herramienta de orientación vocacional y no
            constituye una decisión académica vinculante.
          </p>
        </div>
      </div>
    </footer>
  );
}
