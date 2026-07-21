"""
Tests de la Fase 10 — Chatbot híbrido (reglas + IA).

Estos tests cubren ÚNICAMENTE el paquete `app/services/ia/`, de forma
aislada de `chatbot_service.py` (que ya tiene su propia cobertura en
`test_fase6_chatbot.py` / `test_fase7_chatbot_avanzado.py` / `test_fase9c_...`,
y que no necesita mockear ningún LLM porque, con el feature flag apagado por
defecto, su comportamiento es 100% el mismo de antes).

Objetivo principal: probar que el "apagado seguro" funciona.
- Con `chatbot_ia_habilitada=False` (default), ninguna función de esta capa
  debe intentar una llamada de red — se verifica reemplazando
  `httpx.AsyncClient.post` por un stub que falla la prueba si se lo llama.
- Con el flag encendido pero sin `anthropic_api_key`, tampoco debe intentar
  la llamada de red (falta de configuración = apagado, no un error).
- El "parseo defensivo" de `interpretar_respuesta_libre` ante una respuesta
  del modelo que no es JSON válido, o que trae un valor fuera de 1-5.
"""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.ia import cliente_llm
from app.services.ia.explicacion_resultado import responder_pregunta_sobre_resultado
from app.services.ia.faq_asistida import generar_respuesta_faq_asistida
from app.services.ia.interprete_respuestas import interpretar_respuesta_libre


class _ClienteHttpQueFallaSiSeLlama:
    """Stub de `httpx.AsyncClient` que hace fallar el test si se intenta usar
    (es decir, si el código bajo prueba intentó una llamada de red pese a
    que el feature flag debería haberlo evitado)."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "_ClienteHttpQueFallaSiSeLlama":
        return self

    async def __aexit__(self, *exc) -> None:
        return None

    async def post(self, *args, **kwargs):  # pragma: no cover - no debería llamarse
        pytest.fail(
            "Se intentó una llamada de red a la API de Anthropic estando "
            "la capa de IA deshabilitada o mal configurada."
        )


@pytest.fixture(autouse=True)
def _bloquear_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """Aplica a TODOS los tests de este módulo: cualquier intento de llamada
    de red real hace fallar el test inmediatamente, en vez de intentar
    conectarse (lo que sería lento y no determinista en CI)."""
    monkeypatch.setattr(cliente_llm.httpx, "AsyncClient", _ClienteHttpQueFallaSiSeLlama)


def _settings(**overrides) -> Settings:
    base = {
        "chatbot_ia_habilitada": False,
        "anthropic_api_key": "",
        "anthropic_model": "claude-sonnet-4-6",
        "ia_timeout_segundos": 6.0,
        "ia_umbral_confianza": 0.6,
    }
    base.update(overrides)
    return Settings(**base)


# --- Apagado seguro (feature flag) ------------------------------------------


async def test_llamar_llm_no_hace_red_si_flag_apagado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings(chatbot_ia_habilitada=False))
    resultado = await cliente_llm.llamar_llm("system", "user")
    assert resultado is None


async def test_llamar_llm_no_hace_red_si_falta_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cliente_llm,
        "get_settings",
        lambda: _settings(chatbot_ia_habilitada=True, anthropic_api_key=""),
    )
    resultado = await cliente_llm.llamar_llm("system", "user")
    assert resultado is None


async def test_interpretar_respuesta_libre_cae_a_none_con_ia_apagada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings())
    valor, confianza = await interpretar_respuesta_libre("ni fu ni fa", "¿Te gusta la música?")
    assert valor is None
    assert confianza == 0.0


async def test_faq_asistida_devuelve_texto_original_con_ia_apagada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings())
    original = "El test dura entre 15 y 20 minutos."
    respuesta = await generar_respuesta_faq_asistida("¿cuánto dura?", original)
    assert respuesta == original


async def test_explicacion_resultado_devuelve_none_con_ia_apagada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings())
    resultados = [
        {
            "nombre": "Ingeniería de Sistemas",
            "afinidad_pct": 98.5,
            "fortalezas": ["matematica"],
            "distancia_mahalanobis": 0.4,
        }
    ]
    respuesta = await responder_pregunta_sobre_resultado("¿por qué esa carrera?", resultados)
    assert respuesta is None


async def test_explicacion_resultado_sin_top5_no_intenta_nada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Aunque la IA estuviera habilitada, sin resultados no hay contexto real
    # sobre el cual responder — debe devolver None sin siquiera intentar la
    # llamada (ver el guard `if not resultados` en el propio módulo).
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings(chatbot_ia_habilitada=True))
    respuesta = await responder_pregunta_sobre_resultado("¿por qué esa carrera?", [])
    assert respuesta is None


# --- Parseo defensivo de la respuesta del modelo ----------------------------


async def test_interpretar_respuesta_libre_ignora_json_invalido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings(chatbot_ia_habilitada=True))

    async def _llamar_llm_falso(*args, **kwargs) -> str:
        return "esto no es JSON"

    monkeypatch.setattr(
        "app.services.ia.interprete_respuestas.llamar_llm", _llamar_llm_falso
    )
    valor, confianza = await interpretar_respuesta_libre("bastante", "¿Te gusta?")
    assert valor is None
    assert confianza == 0.0


async def test_interpretar_respuesta_libre_ignora_valor_fuera_de_rango(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cliente_llm, "get_settings", lambda: _settings(chatbot_ia_habilitada=True))

    async def _llamar_llm_falso(*args, **kwargs) -> str:
        return '{"valor": 9, "confianza": 0.9}'

    monkeypatch.setattr(
        "app.services.ia.interprete_respuestas.llamar_llm", _llamar_llm_falso
    )
    valor, confianza = await interpretar_respuesta_libre("mucho", "¿Te gusta?")
    assert valor is None


async def test_interpretar_respuesta_libre_respeta_umbral_de_confianza(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cliente_llm,
        "get_settings",
        lambda: _settings(chatbot_ia_habilitada=True, ia_umbral_confianza=0.8),
    )

    async def _llamar_llm_falso(*args, **kwargs) -> str:
        return '{"valor": 4, "confianza": 0.5}'

    monkeypatch.setattr(
        "app.services.ia.interprete_respuestas.llamar_llm", _llamar_llm_falso
    )
    monkeypatch.setattr(
        "app.services.ia.interprete_respuestas.get_settings",
        lambda: _settings(chatbot_ia_habilitada=True, ia_umbral_confianza=0.8),
    )
    valor, confianza = await interpretar_respuesta_libre("bastante", "¿Te gusta?")
    # Confianza (0.5) por debajo del umbral configurado (0.8): debe
    # descartarse, igual que si la IA no hubiera reconocido nada.
    assert valor is None
    assert confianza == 0.5