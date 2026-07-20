"""
Servicio del Método 1 — Test Tradicional (Fase 4).

Contiene la única función que conecta lo recibido desde el frontend
(`{pregunta_id, respuesta}[]`, de longitud variable) con la Lógica Adaptativa
de Preguntas (Fase 3) y el cálculo del vector de usuario, de forma
**pura y testeable sin base de datos**: recibe solo los ids de pregunta ya
agrupados y ordenados por área (`preguntas_por_area`), no modelos ORM.

El router de FastAPI (`api/test.py`) es el único responsable de tocar la
base de datos: carga las preguntas, llama a `procesar_respuestas_tradicional`,
y persiste el resultado.
"""
from app.core.constants import AREAS
from app.services.adaptive_flow_service import construir_vector_usuario, preguntas_a_formular


class RespuestasInvalidasError(ValueError):
    """
    Se lanza cuando el conjunto de respuestas recibido no es consistente con
    lo que la Lógica Adaptativa habría formulado (respuesta faltante para una
    pregunta que sí correspondía, o respuesta sobrante para una pregunta que
    el algoritmo nunca habría llegado a formular). Nunca se completa el vector
    ni se persiste nada en ese caso.
    """


def procesar_respuestas_tradicional(
    preguntas_por_area: dict[str, list[int]],
    respuestas_dict: dict[int, int],
) -> tuple[dict[str, float], dict[str, list[int]], list[int]]:
    """
    Args:
        preguntas_por_area: {area_key: [pregunta_id, ...]}, ids ordenados
            ascendentemente, para las 17 áreas de `AREAS` (hasta 5 ids c/u).
        respuestas_dict: {pregunta_id: respuesta 1-5} tal como lo envió el
            cliente (formulario), sin garantía de que sea exactamente el
            conjunto correcto.

    Returns:
        (vector_usuario, respuestas_por_area_valores, preguntas_usadas)
        - vector_usuario: dict de 17 claves, listo para el motor de Mahalanobis.
        - respuestas_por_area_valores: {area_key: [respuesta, ...]} solo con
          las preguntas realmente consumidas por el algoritmo.
        - preguntas_usadas: lista plana (todas las áreas) de los pregunta_id
          efectivamente usados, en el orden en que se consumieron.

    Raises:
        RespuestasInvalidasError: si falta una respuesta que correspondía
            formular, o si sobran respuestas para preguntas que el algoritmo
            adaptativo nunca habría llegado a pedir.
    """
    respuestas_por_area_valores: dict[str, list[int]] = {}
    preguntas_usadas: list[int] = []

    for area in AREAS:
        ids_area = preguntas_por_area.get(area, [])

        def _callback(pregunta_id: int, _area: str = area) -> int:
            if pregunta_id not in respuestas_dict:
                raise RespuestasInvalidasError(
                    f"Falta la respuesta para la pregunta {pregunta_id} "
                    f"(área '{_area}'), que sí correspondía formular."
                )
            return respuestas_dict[pregunta_id]

        respuestas_area = preguntas_a_formular(ids_area, _callback)
        respuestas_por_area_valores[area] = respuestas_area
        preguntas_usadas.extend(ids_area[: len(respuestas_area)])

    sobrantes = set(respuestas_dict.keys()) - set(preguntas_usadas)
    if sobrantes:
        raise RespuestasInvalidasError(
            "Se enviaron respuestas para preguntas que la Lógica Adaptativa "
            f"nunca habría formulado dado el resto de respuestas: {sorted(sobrantes)}."
        )

    vector_usuario = construir_vector_usuario(respuestas_por_area_valores)
    return vector_usuario, respuestas_por_area_valores, preguntas_usadas
