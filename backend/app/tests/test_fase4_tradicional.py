"""
Tests de la Fase 4 — Test Tradicional (formulario) end-to-end.

Estos tests cubren `services/test_service.procesar_respuestas_tradicional`,
que es la función pura que conecta lo que envía el formulario con la Lógica
Adaptativa (Fase 3) y el vector de usuario. No requieren base de datos: usan
directamente `data/preguntas.json` (vía `loaders.cargar_preguntas`), igual que
`test_mahalanobis.py` usa `data/carreras.csv` sin depender de PostgreSQL.

Las pruebas de integración HTTP contra `POST /test/tradicional` (con
PostgreSQL real) se documentan como manuales en
`docs/fases/fase-4-test-tradicional.md`, ya que este entorno de CI no levanta
una base de datos Postgres para los tests unitarios (ver esa nota en la
sección "Pruebas realizadas" del documento de cierre).
"""
import pytest

from app.core.constants import AREAS
from app.data.loaders import cargar_preguntas
from app.services.test_service import RespuestasInvalidasError, procesar_respuestas_tradicional


@pytest.fixture(scope="module")
def preguntas_por_area() -> dict[str, list[int]]:
    preguntas = cargar_preguntas()
    mapa: dict[str, list[int]] = {area: [] for area in AREAS}
    for p in preguntas:
        mapa[p["area"]].append(p["id"])
    for ids in mapa.values():
        ids.sort()
    return mapa


def _respuesta_minima_para_todas_las_areas(
    preguntas_por_area: dict[str, list[int]], valor: int = 1
) -> dict[int, int]:
    """Responde `valor` (por defecto 1) a la primera pregunta de cada área."""
    return {ids[0]: valor for ids in preguntas_por_area.values()}


def test_respuesta_1_en_todas_las_areas_produce_17_respuestas_totales(preguntas_por_area):
    respuestas_dict = _respuesta_minima_para_todas_las_areas(preguntas_por_area, valor=1)
    vector, respuestas_por_area, preguntas_usadas = procesar_respuestas_tradicional(
        preguntas_por_area, respuestas_dict
    )
    assert len(preguntas_usadas) == 17
    assert set(vector.keys()) == set(AREAS)
    assert all(v == 1.0 for v in vector.values())
    assert all(len(r) == 1 for r in respuestas_por_area.values())


def test_respuesta_5_constante_formula_las_2_preguntas_de_cada_area(preguntas_por_area):
    respuestas_dict = {
        pid: 5 for ids in preguntas_por_area.values() for pid in ids
    }
    vector, respuestas_por_area, preguntas_usadas = procesar_respuestas_tradicional(
        preguntas_por_area, respuestas_dict
    )
    assert len(preguntas_usadas) == 34
    assert all(len(r) == 2 for r in respuestas_por_area.values())
    assert all(v == 5.0 for v in vector.values())


def test_caso_mixto_recorta_solo_las_areas_con_respuesta_baja(preguntas_por_area):
    """
    Área 'matematica': [3, 5] -> con solo 2 preguntas en el banco, una primera
    respuesta de 3 (que en la escala Likert habilitaría hasta 3) igual se
    acota a las 2 preguntas reales del área, así que se formulan ambas. El
    resto de áreas: solo 1 respuesta (presupuesto 1), como en el caso mínimo.
    """
    respuestas_dict = _respuesta_minima_para_todas_las_areas(preguntas_por_area, valor=1)
    ids_matematica = preguntas_por_area["matematica"]
    respuestas_dict[ids_matematica[0]] = 3
    respuestas_dict[ids_matematica[1]] = 5

    vector, respuestas_por_area, preguntas_usadas = procesar_respuestas_tradicional(
        preguntas_por_area, respuestas_dict
    )
    assert respuestas_por_area["matematica"] == [3, 5]
    assert vector["matematica"] == pytest.approx(4.0)  # promedio de [3, 5]
    # 16 áreas con 1 pregunta + matemática con 2 = 18 preguntas usadas
    assert len(preguntas_usadas) == 16 + 2


def test_falta_una_respuesta_que_si_correspondia_lanza_error(preguntas_por_area):
    """
    'matematica': la primera respuesta es 3 (que en la escala Likert
    habilitaría presupuesto de 3, acotado a las 2 preguntas reales del área),
    pero no se envía la respuesta a la 2da pregunta del área, que sí
    correspondía formular. Debe rechazarse en vez de completar el vector con
    datos parciales.
    """
    respuestas_dict = _respuesta_minima_para_todas_las_areas(preguntas_por_area, valor=1)
    ids_matematica = preguntas_por_area["matematica"]
    respuestas_dict[ids_matematica[0]] = 3  # falta la 2da respuesta

    with pytest.raises(RespuestasInvalidasError):
        procesar_respuestas_tradicional(preguntas_por_area, respuestas_dict)


def test_respuesta_sobrante_mas_alla_del_presupuesto_lanza_error(preguntas_por_area):
    """
    Enviar una respuesta para una pregunta que la Lógica Adaptativa nunca
    habría llegado a formular (ej. primera respuesta = 1, pero igual se envía
    una segunda respuesta) debe rechazarse.
    """
    respuestas_dict = _respuesta_minima_para_todas_las_areas(preguntas_por_area, valor=1)
    ids_matematica = preguntas_por_area["matematica"]
    # presupuesto es 1 (respuesta=1), pero agregamos una 2da respuesta indebida.
    respuestas_dict[ids_matematica[1]] = 4

    with pytest.raises(RespuestasInvalidasError):
        procesar_respuestas_tradicional(preguntas_por_area, respuestas_dict)


def test_vector_usuario_resultante_tiene_17_claves_en_rango_valido(preguntas_por_area):
    # valor=2 -> presupuesto de 2 preguntas por área; respondemos ambas.
    respuestas_dict: dict[int, int] = {}
    for ids in preguntas_por_area.values():
        respuestas_dict[ids[0]] = 2
        respuestas_dict[ids[1]] = 4
    vector, _, _ = procesar_respuestas_tradicional(preguntas_por_area, respuestas_dict)
    assert len(vector) == 17
    assert all(1.0 <= v <= 5.0 for v in vector.values())