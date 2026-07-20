"""
Tests de la Fase 9c — Test de equivalencia formulario vs. chatbot.

Verifica de forma automatizada la garantía central del sistema (ver prompt
maestro, "Regla de oro"): ante la misma secuencia de respuestas, el Método 1
(formulario, `test_service.procesar_respuestas_tradicional`) y el Método 2
(chatbot, `chatbot_service`) deben producir exactamente el mismo
`vector_usuario` y, por lo tanto, el mismo Top 5 de Mahalanobis.

Estrategia:
- Para cada secuencia simulada, se construye primero el `respuestas_dict`
  {pregunta_id: respuesta} que *realmente* usaría la Lógica Adaptativa
  (Fase 3) aplicada a esa secuencia — esto se hace con la misma función
  `preguntas_a_formular` que usa internamente `test_service`.
- Ese `respuestas_dict` se alimenta tal cual al formulario
  (`procesar_respuestas_tradicional`).
- El mismo `respuestas_dict` se usa como "banco de respuestas" para
  responder al chatbot pregunta por pregunta, en el orden real en que el
  chatbot las formula (`chatbot_service.procesar_mensaje`), hasta confirmar
  el resultado final.
- No se ajusta manualmente ninguna secuencia para que "dé igual"
  artificialmente: ambos flujos consumen el `respuestas_dict` de forma
  independiente, aplicando cada uno su propia lógica de corte/extensión, que
  debe coincidir porque ambos delegan en `adaptive_flow_service`.

No requiere PostgreSQL: usa `data/preguntas.json` y `data/carreras.csv`
directamente (mismo patrón que `test_fase4_tradicional.py` y
`test_mahalanobis.py`), por lo que corre en cualquier pipeline de CI sin
levantar base de datos.
"""
import numpy as np
import pytest

from app.core.constants import AREAS
from app.data.loaders import cargar_carreras, cargar_preguntas
from app.services.adaptive_flow_service import preguntas_a_formular
from app.services.chatbot_service import (
    construir_vector_desde_sesion,
    crear_sesion_inicial,
    iniciar_conversacion,
    procesar_mensaje,
)
from app.services.recomendacion_service import calcular_matriz_covarianza, calcular_recomendacion
from app.services.test_service import procesar_respuestas_tradicional


# --------------------------------------------------------------------------
# Fixtures compartidos: preguntas reales, matriz de carreras real y su
# inversa de covarianza (cacheada una sola vez para todo el módulo, igual
# que en producción).
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def preguntas_por_area() -> dict[str, list[int]]:
    preguntas = cargar_preguntas()
    mapa: dict[str, list[int]] = {area: [] for area in AREAS}
    for p in preguntas:
        mapa[p["area"]].append(p["id"])
    for ids in mapa.values():
        ids.sort()
    return mapa


@pytest.fixture(scope="module")
def preguntas_textos() -> dict[int, str]:
    return {p["id"]: p["texto"] for p in cargar_preguntas()}


@pytest.fixture(scope="module")
def motor_recomendacion() -> dict:
    """Matriz de carreras real + inversa de covarianza, cacheadas (como en `main.py`)."""
    carreras = cargar_carreras()
    nombres = [c["nombre"] for c in carreras]
    ids = list(range(1, len(carreras) + 1))
    X = np.array([[c["puntajes"][area] for area in AREAS] for c in carreras], dtype=float)
    _, inv_cov = calcular_matriz_covarianza(X)
    return {"X": X, "ids": ids, "nombres": nombres, "inv_cov": inv_cov}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _respuestas_dict_desde_secuencias(
    preguntas_por_area: dict[str, list[int]],
    secuencias: dict[str, list[int]],
) -> dict[int, int]:
    """
    Dada una secuencia "candidata" de respuestas por área (hasta 5 valores,
    tal como las de la tabla de validación de la Fase 3), aplica la Lógica
    Adaptativa real (`preguntas_a_formular`) para saber exactamente qué
    respuestas se habrían registrado, y devuelve el `respuestas_dict`
    {pregunta_id: respuesta} correspondiente — el mismo insumo que produciría
    un usuario real completando el test.

    Áreas no mencionadas en `secuencias` reciben la secuencia por defecto
    `[1]` (equivalente al caso mínimo: no le interesa esa área).
    """
    respuestas_dict: dict[int, int] = {}
    for area, ids in preguntas_por_area.items():
        secuencia = secuencias.get(area, [1])
        indice = {"i": 0}

        def _callback(_pregunta_id: int, _seq=secuencia, _idx=indice) -> int:
            valor = _seq[_idx["i"]]
            _idx["i"] += 1
            return valor

        respuestas_area = preguntas_a_formular(ids, _callback)
        for pid, valor in zip(ids, respuestas_area):
            respuestas_dict[pid] = valor
    return respuestas_dict


def _ejecutar_chatbot_completo(
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    respuestas_dict: dict[int, int],
) -> tuple[dict[str, float], dict[str, list[int]]]:
    """
    Recorre el chatbot de punta a punta (bienvenida -> 17 áreas ->
    confirmación final), respondiendo cada pregunta que el propio chatbot
    formula con el valor correspondiente de `respuestas_dict` (indexado por
    `pregunta_id`, no por posición), y confirma el resultado al final.

    Devuelve `(vector_usuario, respuestas_por_area)` tal como quedaron en la
    sesión del chatbot, listos para compararse con el resultado del
    formulario.
    """
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)

    guardia = 0
    while estado["fase"] == "esperando_respuesta_likert":
        guardia += 1
        assert guardia <= 200, "El chatbot no debería necesitar más de 85 turnos."
        pregunta_id = estado["pregunta_actual_id"]
        valor = respuestas_dict[pregunta_id]
        procesar_mensaje(estado, preguntas_por_area, preguntas_textos, str(valor))

    assert estado["fase"] == "esperando_confirmacion_final"
    _, listo_para_calcular = procesar_mensaje(
        estado, preguntas_por_area, preguntas_textos, "sí"
    )
    assert listo_para_calcular

    vector_usuario = construir_vector_desde_sesion(estado)
    return vector_usuario, estado["respuestas_por_area"]


def _top5_nombres(vector_usuario: dict[str, float], motor: dict) -> list[str]:
    resultados = calcular_recomendacion(
        vector_usuario,
        motor["X"],
        motor["ids"],
        motor["nombres"],
        AREAS,
        motor["inv_cov"],
    )
    return [r.nombre for r in resultados]


# --------------------------------------------------------------------------
# Las 10+ secuencias de validación.
#
# Cada entrada: (id_caso, {area: [secuencia de respuestas]}).
# Las 7 primeras reutilizan, aplicadas a un área real distinta cada vez, los
# 7 casos exactos de la tabla de validación de la Fase 3 (recorte y
# extensión de la Lógica Adaptativa). Las siguientes cubren combinaciones
# multi-área, el caso extremo "todo mínimo", el caso extremo "todo máximo" y
# un perfil mixto realista con recorte en varias áreas a la vez.
# --------------------------------------------------------------------------

CASOS: list[tuple[str, dict[str, list[int]]]] = [
    ("area_se_corta_de_inmediato_1", {"matematica": [1]}),
    ("presupuesto_3_no_se_extiende_3_5_4", {"comunicacion": [3, 5, 4]}),
    ("presupuesto_5_se_corta_por_baja_5_1", {"ciencia_tecnologia": [5, 1]}),
    ("presupuesto_5_agota_las_5_preguntas", {"pensamiento_analitico": [5, 5, 5, 5, 5]}),
    ("presupuesto_4_se_corta_antes_4_4_2", {"arte_cultura": [4, 4, 2]}),
    ("presupuesto_2_se_respeta_2_1", {"ingles_extranjero": [2, 1]}),
    ("presupuesto_2_nunca_se_extiende_2_4", {"liderazgo_equipo": [2, 4]}),
    (
        "multiples_areas_con_recorte_simultaneo",
        {
            "matematica": [5, 4, 2],
            "comunicacion": [3, 5, 4],
            "arte_cultura": [1],
            "ciencia_tecnologia": [4, 3, 3, 5],
        },
    ),
    ("todas_las_areas_en_minimo", {area: [1] for area in AREAS}),
    ("todas_las_areas_al_maximo", {area: [5, 5, 5, 5, 5] for area in AREAS}),
    (
        "perfil_mixto_realista_variado_por_area",
        {
            "desarrollo_personal": [4, 4, 3, 5],
            "ciencias_sociales": [2, 1],
            "educacion_fisica": [1],
            "arte_cultura": [3, 3, 3],
            "comunicacion": [5, 5, 4, 5, 4],
            "castellano_segunda": [2, 4],
            "ingles_extranjero": [3, 2],
            "matematica": [5, 5, 5, 4, 5],
            "ciencia_tecnologia": [5, 4, 3, 3, 4],
            "educacion_trabajo": [1],
            "pensamiento_analitico": [4, 5, 3, 3],
            "alfabetizacion_digital": [3, 5, 2],
            "adaptabilidad_resiliencia": [4, 4, 4, 4],
            "comunicacion_efectiva": [2, 3],
            "inteligencia_emocional": [5, 3, 4, 2],
            "curiosidad_aprendizaje": [4, 4, 4, 4, 4],
            "liderazgo_equipo": [3, 4, 5],
        },
    ),
]

assert len(CASOS) >= 10, "La Fase 9c exige cubrir al menos 10 secuencias distintas."


@pytest.mark.parametrize("id_caso, secuencias", CASOS, ids=[c[0] for c in CASOS])
def test_formulario_y_chatbot_producen_el_mismo_vector_y_top5(
    id_caso, secuencias, preguntas_por_area, preguntas_textos, motor_recomendacion
):
    respuestas_dict = _respuestas_dict_desde_secuencias(preguntas_por_area, secuencias)

    vector_formulario, respuestas_area_formulario, _ = procesar_respuestas_tradicional(
        preguntas_por_area, respuestas_dict
    )
    vector_chatbot, respuestas_area_chatbot = _ejecutar_chatbot_completo(
        preguntas_por_area, preguntas_textos, respuestas_dict
    )

    # 1) Mismas respuestas efectivamente registradas por área (mismo largo,
    #    mismos valores, en el mismo orden) en ambos métodos.
    assert respuestas_area_formulario == respuestas_area_chatbot, (
        f"[{id_caso}] Las respuestas por área registradas difieren entre "
        "formulario y chatbot."
    )

    # 2) Mismo vector_usuario (17 dimensiones, valores idénticos).
    assert vector_formulario == vector_chatbot, (
        f"[{id_caso}] El vector_usuario difiere entre formulario y chatbot."
    )

    # 3) Mismo Top 5 (mismas carreras, mismo orden) al pasar ambos vectores
    #    por el motor de Mahalanobis real.
    top5_formulario = _top5_nombres(vector_formulario, motor_recomendacion)
    top5_chatbot = _top5_nombres(vector_chatbot, motor_recomendacion)
    assert top5_formulario == top5_chatbot, (
        f"[{id_caso}] El Top 5 difiere entre formulario y chatbot."
    )


def test_hay_al_menos_una_secuencia_con_recorte_y_una_con_extension_maxima():
    """
    Confirma explícitamente que la suite cubre tanto el caso de recorte
    (menos de 5 preguntas en un área) como el de extensión hasta el máximo
    (las 5 preguntas de un área), tal como exige el criterio de aceptación.
    """
    ids_casos = {id_caso for id_caso, _ in CASOS}
    assert "area_se_corta_de_inmediato_1" in ids_casos
    assert "presupuesto_5_agota_las_5_preguntas" in ids_casos
    assert "todas_las_areas_al_maximo" in ids_casos
    assert "todas_las_areas_en_minimo" in ids_casos
