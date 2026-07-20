"""
Tests de la Fase 3 — Lógica Adaptativa de Preguntas por Área.

Cubre exactamente los 7 casos de la tabla de validación del prompt maestro,
más los tests de `construir_vector_usuario` exigidos por los criterios de
aceptación.
"""
from typing import Any

import pytest

from app.services.adaptive_flow_service import construir_vector_usuario, preguntas_a_formular


def _simular(respuestas_en_orden: list[int], numero_preguntas_area: int = 5) -> list[int]:
    """
    Helper de test: envuelve una secuencia fija de respuestas simuladas
    (ej. `[3, 5, 4]`) en un `respuestas_callback` compatible con
    `preguntas_a_formular`, usando ids de pregunta genéricos.
    """
    preguntas_area = list(range(1, numero_preguntas_area + 1))
    iterador = iter(respuestas_en_orden)

    def callback(_pregunta: Any) -> int:
        return next(iterador)

    return preguntas_a_formular(preguntas_area, callback)


# --- Los 7 casos exactos de la tabla de validación del prompt maestro ---


@pytest.mark.parametrize(
    "respuestas_en_orden, cantidad_esperada",
    [
        ([1], 1),
        ([3, 5, 4], 3),
        ([5, 1], 2),
        ([5, 5, 5, 5, 5], 5),
        ([4, 4, 2], 3),
        ([2, 1], 2),
        ([2, 4], 2),
    ],
)
def test_casos_tabla_de_validacion(respuestas_en_orden, cantidad_esperada):
    resultado = _simular(respuestas_en_orden)
    assert len(resultado) == cantidad_esperada
    assert resultado == respuestas_en_orden[:cantidad_esperada]


def test_caso_1_area_se_corta_de_inmediato():
    assert _simular([1]) == [1]


def test_caso_3_5_4_no_extiende_presupuesto():
    assert _simular([3, 5, 4]) == [3, 5, 4]


def test_caso_5_1_se_corta_por_respuesta_baja():
    assert _simular([5, 1]) == [5, 1]


def test_caso_todas_altas_agota_las_5_preguntas():
    assert _simular([5, 5, 5, 5, 5]) == [5, 5, 5, 5, 5]


def test_caso_4_4_2_se_corta_antes_del_presupuesto():
    assert _simular([4, 4, 2]) == [4, 4, 2]


def test_caso_2_1_presupuesto_de_2_se_respeta():
    assert _simular([2, 1]) == [2, 1]


def test_caso_2_4_presupuesto_de_2_nunca_se_extiende():
    assert _simular([2, 4]) == [2, 4]


# --- Casos adicionales de robustez ---


def test_preguntas_a_formular_no_llama_callback_mas_alla_del_presupuesto():
    """El callback jamás debe invocarse para una pregunta más allá del presupuesto."""
    llamadas: list[int] = []

    def callback(pregunta_id: int) -> int:
        llamadas.append(pregunta_id)
        respuestas = {1: 2, 2: 5}  # presupuesto=2, la 2ª respuesta no debería extenderlo
        return respuestas[pregunta_id]

    resultado = preguntas_a_formular([1, 2, 3, 4, 5], callback)
    assert resultado == [2, 5]
    assert llamadas == [1, 2]  # nunca se llamó a la pregunta 3, 4 o 5


def test_area_con_menos_de_5_preguntas_no_lanza_excepcion():
    """Un área con, por ejemplo, solo 3 preguntas definidas no debe romperse
    aunque el presupuesto habilitado sea mayor (ej. respuesta inicial = 5)."""
    resultado = _simular([5, 5, 4], numero_preguntas_area=3)
    assert resultado == [5, 5, 4]


def test_preguntas_area_vacia_devuelve_lista_vacia():
    assert preguntas_a_formular([], lambda p: 5) == []


# --- construir_vector_usuario ---


def test_construir_vector_usuario_devuelve_17_claves_en_rango_valido():
    respuestas_por_area = {
        "matematica": [4, 5, 3],
        "comunicacion": [5],
        "arte_cultura": [1],
        "ciencia_tecnologia": [5, 5, 5, 5, 5],
    }
    vector = construir_vector_usuario(respuestas_por_area)

    assert set(vector.keys()) == set(respuestas_por_area.keys())
    for valor in vector.values():
        assert 1.0 <= valor <= 5.0


def test_construir_vector_usuario_calcula_promedio_correcto():
    respuestas_por_area = {"matematica": [4, 5, 3]}
    vector = construir_vector_usuario(respuestas_por_area)
    assert vector["matematica"] == pytest.approx(4.0, abs=1e-6)


def test_construir_vector_usuario_con_una_sola_respuesta_por_area():
    respuestas_por_area = {"arte_cultura": [1]}
    vector = construir_vector_usuario(respuestas_por_area)
    assert vector["arte_cultura"] == 1.0


def test_construir_vector_usuario_con_las_17_areas_reales():
    """Simula un intento completo: cada una de las 17 áreas con una cantidad
    variable de respuestas (1 a 5), como produciría un intento real."""
    from app.core.constants import AREAS

    respuestas_por_area = {area: [3, 4, 5][: (i % 3) + 1] for i, area in enumerate(AREAS)}
    vector = construir_vector_usuario(respuestas_por_area)

    assert len(vector) == 17
    assert set(vector.keys()) == set(AREAS)
    assert all(1.0 <= v <= 5.0 for v in vector.values())
