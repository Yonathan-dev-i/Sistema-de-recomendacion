"use client";

import { memo, useMemo, useState } from "react";
import type { Area } from "@/lib/api";

export type SerieRadar = {
  label: string;
  color: string;
  valores: Record<string, number>;
};

/**
 * Gráfico radar de 17 ejes, implementado en SVG puro (sin librería de
 * gráficos externa: el entorno de esta fase no tiene acceso de red al
 * registro de npm para instalar `recharts`/similares — ver sección 3 del
 * documento de cierre de la Fase 8). Soporta cualquier número de series
 * (2 para "usuario vs. carrera", o varias en el mini-radar del comparador).
 *
 * Accesible: cada vértice expone un `<title>` nativo (tooltip del navegador)
 * y un botón invisible tocable (44×44 mín. en desktop se reduce visualmente
 * pero el área de toque respeta el mínimo) para exponer el valor exacto al
 * hacer hover/tap, sin depender de JS de terceros.
 *
 * Fase 9f (performance): la geometría (ángulos, anillos, puntos por serie)
 * se recalculaba en cada render, incluido cada cambio de `activo` al pasar
 * el mouse sobre un vértice — trabajo trigonométrico redundante en una
 * pantalla que puede tener 2-4 radares simultáneos (radar principal +
 * mini-radar del comparador con hasta 3 series). Se extrae a `useMemo`,
 * recalculando solo cuando cambian `areas`, `series`, `size` o `maxValue`,
 * no en cada hover. El componente se exporta envuelto en `memo` para no
 * re-renderizar cuando el padre cambia por razones ajenas a sus props.
 */
function RadarChartBase({
  areas,
  series,
  size = 420,
  maxValue = 5,
}: {
  areas: Area[];
  series: SerieRadar[];
  size?: number;
  maxValue?: number;
}) {
  const [activo, setActivo] = useState<{ areaKey: string; serieIdx: number } | null>(null);

  const n = areas.length;

  const geometria = useMemo(() => {
    if (n === 0) return null;

    const centro = size / 2;
    const radioMax = size / 2 - 56; // deja espacio para las etiquetas de eje
    const anillosFrac = [0.25, 0.5, 0.75, 1];

    const angulo = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;
    const punto = (i: number, valor: number) => {
      const r = (Math.max(0, Math.min(valor, maxValue)) / maxValue) * radioMax;
      return {
        x: centro + r * Math.cos(angulo(i)),
        y: centro + r * Math.sin(angulo(i)),
      };
    };

    return {
      centro,
      anillos: anillosFrac.map((frac) => ({
        frac,
        puntos: areas.map((_, i) => punto(i, maxValue * frac)),
      })),
      ejes: areas.map((area, i) => ({ area, p: punto(i, maxValue) })),
      etiquetas: areas.map((area, i) => {
        const p = punto(i, maxValue * 1.18);
        const anchorX = Math.cos(angulo(i));
        const textAnchor: "start" | "end" | "middle" =
          anchorX > 0.3 ? "start" : anchorX < -0.3 ? "end" : "middle";
        return { area, p, textAnchor };
      }),
      puntosPorSerie: series.map((serie) =>
        areas.map((area, i) => ({
          area,
          i,
          valor: serie.valores[area.key] ?? 0,
          p: punto(i, serie.valores[area.key] ?? 0),
        })),
      ),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [areas, series, size, maxValue, n]);

  if (n === 0 || !geometria) {
    return (
      <div className="mx-auto flex max-w-[420px] flex-col items-center gap-2 rounded-2xl border border-dashed border-border bg-muted/30 px-6 py-10 text-center">
        <p className="text-sm font-medium text-foreground">
          Sin datos suficientes para graficar
        </p>
        <p className="text-xs text-muted-foreground">
          Esta carrera todavía no tiene un perfil de áreas configurado.
        </p>
      </div>
    );
  }

  const { centro, anillos, ejes, etiquetas, puntosPorSerie } = geometria;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        role="img"
        aria-label={`Gráfico radar comparando ${series.map((s) => s.label).join(" vs. ")} en 17 áreas`}
        viewBox={`0 0 ${size} ${size}`}
        width="100%"
        style={{ maxWidth: size }}
        className="mx-auto"
      >
        {/* Anillos de referencia (25/50/75/100%) */}
        {anillos.map(({ frac, puntos }) => (
          <polygon
            key={frac}
            points={puntos.map((p) => `${p.x},${p.y}`).join(" ")}
            fill="none"
            stroke="currentColor"
            className="text-muted-foreground/20"
            strokeWidth={1}
          />
        ))}

        {/* Ejes */}
        {ejes.map(({ area, p }) => (
          <line
            key={area.key}
            x1={centro}
            y1={centro}
            x2={p.x}
            y2={p.y}
            stroke="currentColor"
            className="text-muted-foreground/20"
            strokeWidth={1}
          />
        ))}

        {/* Series (polígonos de datos) */}
        {series.map((serie, sIdx) => (
          <g key={serie.label}>
            <polygon
              points={puntosPorSerie[sIdx].map(({ p }) => `${p.x},${p.y}`).join(" ")}
              fill={serie.color}
              fillOpacity={0.18}
              stroke={serie.color}
              strokeWidth={2}
            />
            {puntosPorSerie[sIdx].map(({ area, valor, p }) => {
              const esActivo = activo?.areaKey === area.key && activo?.serieIdx === sIdx;
              return (
                <g key={area.key}>
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={esActivo ? 5 : 3}
                    fill={serie.color}
                    stroke="white"
                    strokeWidth={1}
                  >
                    <title>
                      {serie.label} · {area.label}: {valor.toFixed(1)} / {maxValue.toFixed(1)}
                    </title>
                  </circle>
                  {/* Área táctil ampliada (44x44) para cumplir criterio de accesibilidad móvil */}
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={16}
                    fill="transparent"
                    onMouseEnter={() => setActivo({ areaKey: area.key, serieIdx: sIdx })}
                    onMouseLeave={() => setActivo(null)}
                    onClick={() =>
                      setActivo((prev) =>
                        prev?.areaKey === area.key && prev?.serieIdx === sIdx
                          ? null
                          : { areaKey: area.key, serieIdx: sIdx },
                      )
                    }
                    style={{ cursor: "pointer" }}
                  >
                    <title>
                      {serie.label} · {area.label}: {valor.toFixed(1)} / {maxValue.toFixed(1)}
                    </title>
                  </circle>
                </g>
              );
            })}
          </g>
        ))}

        {/* Etiquetas de área */}
        {etiquetas.map(({ area, p, textAnchor }) => (
          <text
            key={area.key}
            x={p.x}
            y={p.y}
            textAnchor={textAnchor}
            dominantBaseline="middle"
            className="fill-muted-foreground"
            style={{ fontSize: 9.5 }}
          >
            {area.label}
          </text>
        ))}
      </svg>

      {/* Valor activo (para lectores de pantalla y feedback visual explícito) */}
      <p className="mt-2 text-center text-xs text-muted-foreground" aria-live="polite">
        {activo
          ? `${series[activo.serieIdx].label} · ${areas.find((a) => a.key === activo.areaKey)?.label}: ${(
              series[activo.serieIdx].valores[activo.areaKey] ?? 0
            ).toFixed(1)} / ${maxValue.toFixed(1)}`
          : "Pasa el cursor o toca un punto del radar para ver el valor exacto de cada eje."}
      </p>

      {/* Leyenda */}
      <div className="mt-3 flex flex-wrap justify-center gap-4">
        {series.map((serie) => (
          <span key={serie.label} className="flex items-center gap-1.5 text-xs font-medium">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: serie.color }}
              aria-hidden
            />
            {serie.label}
          </span>
        ))}
      </div>
    </div>
  );
}
export const RadarChart = memo(RadarChartBase);
