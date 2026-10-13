"""
Tests de la Fase 6 — Chatbot basado en reglas (núcleo conversacional).

Cubren `services/chatbot_service.py` de forma pura (sin FastAPI ni base de
datos), igual que `test_fase4_tradicional.py` prueba `test_service.py`:
- La FSM valida entrada Likert estricta y no avanza el estado ante datos
  inválidos.
- El "test de equivalencia" central de la Fase 6/9: ante la misma secuencia
  de respuestas, el chatbot produce exactamente el mismo `vector_usuario`
  que `procesar_respuestas_tradicional` (Fase 4).
"""
import pytest

from app.core.constants import AREAS
from app.data.loaders import cargar_preguntas
from app.services.chatbot_service import (
    construir_vector_desde_sesion,
    crear_sesion_inicial,
    iniciar_conversacion,
    interpretar_likert,
    interpretar_si_no,
    procesar_mensaje,
)
from app.services.test_service import procesar_respuestas_tradicional


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


def _correr_conversacion_completa(
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    respuestas_por_area_secuencia: dict[str, list[int]],
) -> dict:
    """
    Simula una conversación completa alimentando, área por área, la secuencia
    de respuestas dada, y devuelve el estado final (ya con `fase ==
    "post_resultado"`).
    """
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)

    for area_idx, area in enumerate(AREAS):
        for valor in respuestas_por_area_secuencia.get(area, [1]):
            # Se corta tanto si el test terminó (confirmación final) como si
            # ya se avanzó a la siguiente área (esta ya recibió todas las
            # respuestas que el banco real tiene para ella) — sin este
            # segundo chequeo, los valores sobrantes de una secuencia más
            # larga que el banco del área (ej. [5, 5, 5, 5, 5] con un banco
            # de solo 2 preguntas/área) se filtrarían como respuestas de la
            # primera pregunta del área siguiente.
            if estado["fase"] != "esperando_respuesta_likert" or estado["area_idx"] != area_idx:
                break
            procesar_mensaje(estado, preguntas_por_area, preguntas_textos, str(valor))

    # Confirmación final.
    assert estado["fase"] == "esperando_confirmacion_final"
    _, listo = procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "sí")
    assert listo is True
    assert estado["fase"] == "post_resultado"
    return estado


# --- interpretación de entrada -------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1", 1),
        ("5", 5),
        ("tres", 3),
        ("CUATRO", 4),
        ("cero", None),
        ("6", None),
        ("no sé", None),
        ("", None),
    ],
)
def test_interpretar_likert(texto: str, esperado: int | None) -> None:
    assert interpretar_likert(texto) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("sí", True), ("si", True), ("SI", True), ("no", False), ("tal vez", None)],
)
def test_interpretar_si_no(texto: str, esperado: bool | None) -> None:
    assert interpretar_si_no(texto) == esperado


# --- validación estricta: no avanza el estado ante respuesta inválida ---------


def test_respuesta_invalida_no_avanza_el_estado(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)
    pregunta_antes = estado["pregunta_actual_id"]
    fase_antes = estado["fase"]

    mensaje, listo = procesar_mensaje(
        estado, preguntas_por_area, preguntas_textos, "no entiendo"
    )

    assert listo is False
    assert estado["pregunta_actual_id"] == pregunta_antes
    assert estado["fase"] == fase_antes
    assert estado["total_formuladas"] == 0
    assert "1 al 5" in mensaje.textos[0]


def test_confirmacion_invalida_no_avanza_a_post_resultado(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)
    for area in AREAS:
        while estado["fase"] == "esperando_respuesta_likert" and len(
            estado["respuestas_por_area"][area]
        ) < 1:
            procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "1")

    assert estado["fase"] == "esperando_confirmacion_final"
    _, listo = procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "tal vez")
    assert listo is False
    assert estado["fase"] == "esperando_confirmacion_final"


# --- test de equivalencia formulario vs. chatbot (regla de oro) ---------------


@pytest.mark.parametrize(
    "secuencias",
    [
        # Presupuesto mínimo: 1 en la primera pregunta de todas las áreas.
        {area: [1] for area in AREAS},
        # Presupuesto máximo: 5 constante en todas las preguntas (el banco
        # solo tiene 2 por área, así que el helper corta ahí; el 5 extra
        # queda deliberadamente en la secuencia para probar que no se filtra
        # a la siguiente área).
        {area: [5, 5, 5, 5, 5] for area in AREAS},
        # Caso mixto: recorte a mitad de camino en varias áreas.
        {
            **{area: [3, 5, 4] for area in AREAS[:5]},
            **{area: [5, 1] for area in AREAS[5:10]},
            **{area: [2, 4] for area in AREAS[10:]},
        },
        # Otro caso mixto, con áreas de presupuesto 4 recortadas por una caída.
        {
            **{area: [4, 4, 2] for area in AREAS[:8]},
            **{area: [2, 1] for area in AREAS[8:]},
        },
    ],
)
def test_equivalencia_chatbot_vs_formulario(
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    secuencias: dict[str, list[int]],
) -> None:
    # --- Método 2: chatbot ---
    estado_chat = _correr_conversacion_completa(
        preguntas_por_area, preguntas_textos, secuencias
    )
    vector_chatbot = construir_vector_desde_sesion(estado_chat)

    # --- Método 1: formulario, reconstruyendo el mismo payload que hubiera
    #     enviado un cliente que respondió exactamente la misma secuencia ---
    respuestas_dict: dict[int, int] = {}
    for area in AREAS:
        ids = preguntas_por_area[area]
        respuestas = []
        for i, pid in enumerate(ids):
            valores = secuencias.get(area, [1])
            if i >= len(valores):
                break
            respuestas_dict[pid] = valores[i]
            respuestas.append(valores[i])
            if i == 0:
                limite = valores[0]
                if limite <= 1:
                    break
            else:
                if valores[i] < 3:
                    break
                if (i + 1) >= min(limite, len(ids)):
                    break

    vector_formulario, _, _ = procesar_respuestas_tradicional(
        preguntas_por_area, respuestas_dict
    )

    assert vector_chatbot == vector_formulario
    assert estado_chat["preguntas_usadas"] == [
        pid for pid in respuestas_dict
    ] or set(estado_chat["preguntas_usadas"]) == set(respuestas_dict.keys())