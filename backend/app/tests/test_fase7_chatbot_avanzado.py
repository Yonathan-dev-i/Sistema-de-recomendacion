"""
Tests de la Fase 7 — Funcionalidades avanzadas del chatbot (FAQs, comandos de
navegación y seguimiento post-resultado).

Cubren, de forma pura (sin FastAPI ni base de datos), los 3 criterios de
aceptación explícitos de la fase:
1. El chatbot responde correctamente a al menos 5 preguntas frecuentes
   distintas sin salirse del flujo del test.
2. Tras mostrar un resultado, el usuario puede preguntar "¿por qué esa
   carrera?" y recibir una respuesta basada en los datos reales de su Top 5.
3. Ninguna respuesta proviene de generación de texto libre; todas son
   trazables a una plantilla + datos (verificado indirectamente: todas las
   respuestas de este módulo provienen de `data/intents.json` o de
   plantillas con datos del propio `estado`).
"""
import pytest

from app.core.constants import AREAS
from app.data.loaders import cargar_preguntas
from app.services.chatbot_service import (
    crear_sesion_inicial,
    iniciar_conversacion,
    procesar_mensaje,
    responder_pregunta_seguimiento,
)
from app.services.faq_service import buscar_intent_faq, normalizar_texto


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


@pytest.fixture()
def resultado_top5() -> list[dict]:
    """Top 5 de ejemplo con la forma real que produce `recomendacion_service`."""
    return [
        {
            "carrera_id": 1,
            "nombre": "Ingeniería de Sistemas",
            "distancia_mahalanobis": 0.412,
            "afinidad_pct": 98.5,
            "explicacion": "x",
            "fortalezas": ["matematica", "pensamiento_analitico", "ciencia_tecnologia"],
            "areas_por_mejorar": ["arte_cultura"],
        },
        {
            "carrera_id": 2,
            "nombre": "Ingeniería Civil",
            "distancia_mahalanobis": 1.203,
            "afinidad_pct": 80.1,
            "explicacion": "x",
            "fortalezas": ["matematica"],
            "areas_por_mejorar": ["comunicacion"],
        },
        {
            "carrera_id": 3,
            "nombre": "Educación Física",
            "distancia_mahalanobis": 2.5,
            "afinidad_pct": 40.0,
            "explicacion": "x",
            "fortalezas": ["educacion_fisica"],
            "areas_por_mejorar": ["matematica"],
        },
    ]


# --- Criterio 1: al menos 5 FAQs distintas, sin salir del flujo del test -----


@pytest.mark.parametrize(
    "pregunta",
    [
        "¿cuánto dura el test?",
        "¿mis datos son privados?",
        "¿en qué se diferencian el formulario y el chatbot?",
        "¿cómo se calcula la recomendación?",
        "¿el test tiene algún costo?",
        "¿puedo volver a hacer el test?",
    ],
)
def test_chatbot_responde_faqs_sin_salirse_del_flujo(
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    pregunta: str,
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)
    pregunta_actual_antes = estado["pregunta_actual_id"]
    fase_antes = estado["fase"]

    mensaje, listo = procesar_mensaje(
        estado, preguntas_por_area, preguntas_textos, pregunta
    )

    assert listo is False
    # No se sale del flujo del test: la misma pregunta pendiente se repite.
    assert estado["fase"] == fase_antes
    assert estado["pregunta_actual_id"] == pregunta_actual_antes
    assert estado["total_formuladas"] == 0
    # La respuesta FAQ se antepone al mensaje que repite la pregunta.
    assert len(mensaje.textos) >= 2
    # Ninguna respuesta inválida se contabilizó por hacer una pregunta FAQ.
    assert estado["intentos_invalidos"] == 0
    assert len(estado["analitica"]["intents_disparados"]) == 1


def test_al_menos_5_intents_distintos_configurados() -> None:
    """El banco de intenciones cubre al menos 5 FAQs distintas (por diseño)."""
    from app.services.faq_service import _cargar_intents

    assert len(_cargar_intents()) >= 5


# --- Criterio 2: seguimiento post-resultado con datos reales del Top 5 ------


def test_por_que_esa_carrera_usa_datos_reales_del_top5(resultado_top5: list[dict]) -> None:
    estado = {
        "ultimo_resultado": resultado_top5,
        "analitica": {"intents_disparados": [], "respuestas_invalidas": 0, "area_abandono": None},
    }
    respuesta = responder_pregunta_seguimiento("¿por qué me recomendaste esa carrera?", estado)

    top1 = resultado_top5[0]
    assert top1["nombre"] in respuesta
    assert str(top1["distancia_mahalanobis"]) in respuesta
    assert any(f in respuesta for f in top1["fortalezas"])


def test_comparacion_conversacional_usa_datos_reales(resultado_top5: list[dict]) -> None:
    estado = {
        "ultimo_resultado": resultado_top5,
        "analitica": {"intents_disparados": [], "respuestas_invalidas": 0, "area_abandono": None},
    }
    respuesta = responder_pregunta_seguimiento(
        "compara Ingeniería de Sistemas con Ingeniería Civil", estado
    )

    assert "Ingeniería de Sistemas" in respuesta
    assert "Ingeniería Civil" in respuesta
    assert "98.5" in respuesta
    assert "80.1" in respuesta


def test_comparacion_sin_dos_carreras_identificadas_pide_aclaracion(
    resultado_top5: list[dict],
) -> None:
    estado = {
        "ultimo_resultado": resultado_top5,
        "analitica": {"intents_disparados": [], "respuestas_invalidas": 0, "area_abandono": None},
    }
    respuesta = responder_pregunta_seguimiento("compara dos carreras", estado)
    assert "Dime cuáles dos carreras" in respuesta


def test_post_resultado_tambien_responde_faqs(resultado_top5: list[dict]) -> None:
    estado = {
        "ultimo_resultado": resultado_top5,
        "analitica": {"intents_disparados": [], "respuestas_invalidas": 0, "area_abandono": None},
    }
    respuesta = responder_pregunta_seguimiento("¿mis datos son privados?", estado)
    assert "confidencial" not in respuesta or "recomendación" in respuesta
    assert len(estado["analitica"]["intents_disparados"]) == 1


def test_fallback_fijo_post_resultado_no_inventa_respuesta(resultado_top5: list[dict]) -> None:
    estado = {
        "ultimo_resultado": resultado_top5,
        "analitica": {"intents_disparados": [], "respuestas_invalidas": 0, "area_abandono": None},
    }
    respuesta = responder_pregunta_seguimiento("asdkjhaskdjh sin sentido", estado)
    assert "No logré identificar tu pregunta" in respuesta
    assert estado["analitica"]["respuestas_invalidas"] == 1


# --- Comandos de navegación dentro del chat ---------------------------------


def test_comando_repetir_no_avanza_el_estado(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)
    pregunta_antes = estado["pregunta_actual_id"]

    mensaje, listo = procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "repetir")

    assert listo is False
    assert estado["pregunta_actual_id"] == pregunta_antes
    assert estado["total_formuladas"] == 0


def test_comando_ver_progreso_no_avanza_el_estado(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)

    mensaje, listo = procesar_mensaje(
        estado, preguntas_por_area, preguntas_textos, "ver progreso"
    )

    assert listo is False
    assert "área" in mensaje.textos[0].lower()
    assert estado["total_formuladas"] == 0


def test_comando_anterior_corrige_la_ultima_respuesta(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)
    area0 = AREAS[0]

    procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "4")
    assert estado["respuestas_por_area"][area0] == [4]

    procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "anterior")
    assert estado["respuestas_por_area"][area0] == []
    assert estado["total_formuladas"] == 0
    # La pregunta actual vuelve a ser la primera del área.
    assert estado["pregunta_actual_id"] == preguntas_por_area[area0][0]


def test_comando_pausar_guarda_estado_sin_perder_avance(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)
    procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "4")

    mensaje, listo = procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "pausar")

    assert listo is False
    assert estado["pausado"] is True
    assert estado["respuestas_por_area"][AREAS[0]] == [4]


def test_comando_ayuda_lista_las_opciones_disponibles(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)

    mensaje, listo = procesar_mensaje(estado, preguntas_por_area, preguntas_textos, "ayuda")

    assert listo is False
    assert "repetir" in mensaje.textos[0]


# --- Límite de reintentos con oferta de cambio a formulario tradicional ------


def test_limite_de_reintentos_ofrece_cambiar_a_formulario(
    preguntas_por_area: dict[str, list[int]], preguntas_textos: dict[int, str]
) -> None:
    estado = crear_sesion_inicial()
    iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)

    mensaje = None
    for _ in range(3):
        mensaje, _ = procesar_mensaje(
            estado, preguntas_por_area, preguntas_textos, "xxzzqq sin sentido"
        )

    assert mensaje is not None
    assert any("formulario tradicional" in t for t in mensaje.textos)
    # El contador se reinicia tras ofrecer el cambio, no queda "atascado".
    assert estado["intentos_invalidos"] == 0


# --- Servicio de FAQ (matching por reglas) ----------------------------------


def test_normalizar_texto_quita_tildes_puntuacion_y_mayusculas() -> None:
    assert normalizar_texto("¿Cuánto DURA el Test?") == "cuanto dura el test"


def test_buscar_intent_faq_tolera_un_error_de_tipeo() -> None:
    intent = buscar_intent_faq("cuanro dura el test")
    assert intent is not None
    assert intent[0] == "duracion_test"


def test_buscar_intent_faq_devuelve_none_si_no_hay_match() -> None:
    assert buscar_intent_faq("hola buenos dias como estas") is None
