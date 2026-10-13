"""
Lógica Adaptativa de Preguntas por Área — Fase 3.

Módulo único y compartido entre el Método 1 (formulario) y el Método 2
(chatbot): ambos deben producir exactamente el mismo comportamiento ante las
mismas respuestas, por lo que ninguno de los dos implementa esta lógica por
su cuenta — ambos llaman a `preguntas_a_formular` desde aquí.

Idea general (ver especificación completa en el prompt maestro):
- La primera respuesta de un área define el "presupuesto" máximo de preguntas
  de esa área (1 a 5 en la escala Likert), pero el presupuesto real nunca
  puede superar la cantidad de preguntas que el área realmente tiene
  (`len(preguntas_area)`, hoy 2 tras la reducción del banco) — de ahí el
  `min(limite_area, len(preguntas_area))` en el bucle de abajo. La función no
  asume ningún tamaño fijo de banco: sirve igual si un área tuviera 2, 3 o 5
  preguntas.
- Las respuestas siguientes pueden **recortar** ese presupuesto (si alguna es
  menor a 3, el área se corta ahí mismo), pero **nunca lo extienden** por
  encima de lo que habilitó la primera respuesta, aunque una respuesta
  posterior sea mayor.
"""
from collections.abc import Callable, Sequence
from typing import TypeVar

Pregunta = TypeVar("Pregunta")


def preguntas_a_formular(
    preguntas_area: Sequence[Pregunta],
    respuestas_callback: Callable[[Pregunta], int],
) -> list[int]:
    """
    Recorre hasta las preguntas disponibles de un área (según `preguntas_area`),
    aplicando la Lógica Adaptativa.

    Args:
        preguntas_area: las (hasta 5) preguntas del área, ordenadas por id ascendente.
            Puede ser cualquier secuencia (modelos ORM, dicts, ids simples): esta
            función no le exige forma, solo se la pasa tal cual a `respuestas_callback`.
        respuestas_callback: función que "formula" la siguiente pregunta (form o
            chatbot) y devuelve la respuesta Likert (1-5) del usuario para ella.

    Returns:
        La lista de respuestas efectivamente registradas para el área (longitud 1-5).
    """
    if not preguntas_area:
        return []

    respuestas: list[int] = []

    # 1) Siempre se formula la primera pregunta del área.
    r1 = respuestas_callback(preguntas_area[0])
    respuestas.append(r1)

    # 2) La primera respuesta define el "presupuesto" máximo de preguntas del área.
    limite_area = r1  # r1 está en el rango 1-5; se acota al tamaño real del área abajo.

    # 3) Si el presupuesto es 1 (no le gusta nada), no se formulan más preguntas de esta área.
    if limite_area <= 1:
        return respuestas

    # 4) Formular preguntas adicionales solo hasta el límite definido por r1,
    #    pero cortar antes si alguna respuesta posterior es menor a 3.
    for i in range(1, min(limite_area, len(preguntas_area))):
        r_i = respuestas_callback(preguntas_area[i])
        respuestas.append(r_i)
        if r_i < 3:
            # Interés decayó: se recorta el área aquí, sin llegar al presupuesto original.
            break
        # Si r_i >= 3, se continúa, pero jamás más allá de `limite_area`
        # preguntas en total, aunque r_i sea mayor que r1.

    return respuestas


def construir_vector_usuario(respuestas_por_area: dict[str, list[int]]) -> dict[str, float]:
    """
    Calcula el vector de 17 dimensiones del usuario: el promedio aritmético de
    las respuestas *realmente formuladas* en cada área (1 a 5 valores según la
    Lógica Adaptativa), no siempre sobre 5.

    Args:
        respuestas_por_area: p.ej. {"matematica": [4, 5, 3], "comunicacion": [5], ...}.
            Debe contener las 17 áreas, cada una con al menos 1 respuesta.

    Returns:
        dict {area_key: promedio redondeado a 2 decimales}, valores en [1.0, 5.0].
    """
    return {
        area: round(sum(respuestas) / len(respuestas), 2)
        for area, respuestas in respuestas_por_area.items()
    }