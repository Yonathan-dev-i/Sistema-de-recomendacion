/**
 * Espejo en el cliente de `services/adaptive_flow_service.py` (Fase 3).
 *
 * Se usa exclusivamente para decidir, en vivo dentro del formulario, cuántas
 * preguntas mostrar de cada área y cuándo pasar a la siguiente. La fuente de
 * verdad sigue siendo el backend: `POST /test/tradicional` vuelve a aplicar
 * este mismo algoritmo sobre lo recibido y rechaza cualquier payload que no
 * sea consistente con él (ver `services/test_service.py`).
 */

/** Dado el presupuesto que habilitó la primera respuesta de un área, indica
 * si corresponde formular una pregunta más dado el índice (0-based) dentro
 * del área y las respuestas ya dadas en esa área. */
export function siguientePreguntaIndiceEnArea(
  respuestasArea: number[],
  totalPreguntasArea: number,
): number | null {
  if (respuestasArea.length === 0) {
    return 0; // siempre se formula la primera pregunta del área
  }
  const limiteArea = respuestasArea[0];
  if (limiteArea <= 1) {
    return null; // presupuesto agotado de inmediato
  }
  // El corte por "<3" solo aplica a respuestas POSTERIORES a la primera
  // (igual que en el backend: `for i in range(1, ...)`). La primera
  // respuesta ya se evaluó arriba contra `limiteArea <= 1`; no debe
  // volver a evaluarse aquí, o un r1 == 2 cortaría el área de más
  // (divergencia con `adaptive_flow_service.preguntas_a_formular`).
  if (respuestasArea.length > 1) {
    const ultimaRespuesta = respuestasArea[respuestasArea.length - 1];
    if (ultimaRespuesta < 3) {
      return null; // el interés decayó, se corta el área aquí
    }
  }
  const siguienteIndice = respuestasArea.length;
  if (siguienteIndice >= Math.min(limiteArea, totalPreguntasArea)) {
    return null; // se alcanzó el presupuesto (o el total real de preguntas)
  }
  return siguienteIndice;
}

/** Progreso estimado (0-100) dado en qué área/pregunta va el usuario. */
export function progresoEstimadoPct(areaIndex: number, totalAreas: number): number {
  return Math.round((areaIndex / totalAreas) * 100);
}