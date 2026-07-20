/**
 * Un emoji por cada una de las 17 áreas del test (`AREAS` en el backend),
 * usado solo como apoyo visual para que el formulario y el chatbot se
 * sientan menos repetitivos al pasar de un área a otra. Puramente
 * decorativo: no participa en ningún cálculo.
 */
export const ICONO_POR_AREA: Record<string, string> = {
  desarrollo_personal: "🌱",
  ciencias_sociales: "🌍",
  educacion_fisica: "🏃",
  arte_cultura: "🎨",
  comunicacion: "💬",
  castellano_segunda: "📖",
  ingles_extranjero: "🌐",
  matematica: "🧮",
  ciencia_tecnologia: "🔬",
  educacion_trabajo: "🛠️",
  pensamiento_analitico: "🧩",
  alfabetizacion_digital: "💻",
  adaptabilidad_resiliencia: "🌤️",
  comunicacion_efectiva: "🗣️",
  inteligencia_emocional: "❤️",
  curiosidad_aprendizaje: "🔎",
  liderazgo_equipo: "🤝",
};

export function iconoDeArea(areaKey: string): string {
  return ICONO_POR_AREA[areaKey] ?? "✨";
}