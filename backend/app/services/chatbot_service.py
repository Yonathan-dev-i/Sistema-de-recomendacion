"""
Servicio del Método 2 — Chatbot híbrido: reglas + IA como capa adicional (Fase 6 + Fase 10).

Núcleo determinista (máquina de estados finita, sin IA, sin LLMs externos):
el guion, las transiciones y la validación son código explícito, EXACTAMENTE
igual que antes. La única adición (Fase 10) es una capa de IA opcional
(`app/services/ia/`, apagada por defecto vía `chatbot_ia_habilitada`) que
actúa como fallback SOLO en los puntos donde las reglas ya fallaron:
interpretar una respuesta Likert ambigua, redactar una FAQ ya encontrada de
forma más natural, y responder preguntas de seguimiento sobre el resultado
que no calzan con los patrones fijos. Ver
`docs/fases/fase-10-chatbot-hibrido.md` para el contrato completo.

Este módulo YA NO es 100% síncrono: las funciones que pueden llegar a
necesitar la capa de IA (`procesar_mensaje`, `_procesar_respuesta_likert`,
`responder_pregunta_seguimiento`) son `async def`, porque la llamada al LLM
es I/O de red. Sigue sin tocar la base de datos ni importar FastAPI — el
router (`app/api/chatbot.py`) sigue siendo el único responsable de
persistencia.

Este módulo recibe y devuelve un `dict` de estado de sesión (serializable a
JSON, tal como se persiste en `IntentoTest.estado_chat` para poder reanudar
tras un refresh) y `preguntas_por_area` (mismo insumo que ya usa
`test_service`), y aplica exactamente la misma Lógica Adaptativa de
Preguntas de la Fase 3 (`preguntas_a_formular`), pregunta por pregunta, en
tiempo real.

Estados de la FSM (`estado.fase`):
- "bienvenida": estado inicial, aún no se formuló ninguna pregunta.
- "esperando_respuesta_likert": el chatbot espera un 1-5 para la pregunta
  actual (`estado.pregunta_actual_id`).
- "esperando_confirmacion_final": las 17 áreas ya se recorrieron; el chatbot
  espera "sí"/"no" antes de calcular y persistir el resultado.
- "post_resultado": el test ya se calculó; solo quedan mensajes de cierre.

Garantía de equivalencia con el Método 1 (formulario): ante la misma
secuencia de respuestas Likert, área por área, este módulo consume las
preguntas en el mismo orden y aplica la misma regla de corte que
`adaptive_flow_service.preguntas_a_formular`, por lo que
`construir_vector_usuario` produce exactamente el mismo vector. La capa de
IA nunca decide un valor Likert por su cuenta: cuando la usa, solo TRADUCE
texto ambiguo a un entero 1-5 con un umbral de confianza, y ese entero pasa
por el mismo camino de reglas que si el usuario hubiera tipeado el dígito.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.core.constants import AREAS
from app.services.adaptive_flow_service import construir_vector_usuario
from app.services.faq_service import buscar_intent_faq, normalizar_texto
from app.services.ia.explicacion_resultado import responder_pregunta_sobre_resultado
from app.services.ia.faq_asistida import generar_respuesta_faq_asistida
from app.services.ia.interprete_respuestas import interpretar_respuesta_libre

logger = logging.getLogger("app.chatbot.ia")

LIMITE_REINTENTOS_INVALIDOS = 3
"""Tras N respuestas Likert inválidas seguidas, se ofrece cambiar al formulario."""

_PATRONES_POR_QUE = [r"por qu[e]", r"razon", r"explica"]
_PATRONES_COMPARAR = [r"compara", r"diferencia entre", r"\bvs\b"]

MENSAJE_BIENVENIDA = (
    "Hola. Soy tu orientador vocacional. Durante unos minutos conversaré "
    "contigo sobre tus gustos e intereses para recomendarte las carreras "
    "más afines a tu perfil. Responde cada pregunta con un número del 1 "
    "al 5, donde 1 = No me gusta nada y 5 = Me gusta mucho."
)

_TRANSICIONES = [
    "Perfecto, sigamos.",
    "Gracias por tu respuesta.",
    "Entendido, continuemos.",
    "Muy bien, avancemos.",
    "Anotado, sigamos con la siguiente.",
]

_MOTIVACION_CADA_N_PREGUNTAS = 6
_MENSAJE_MOTIVACION = "Vas muy bien, ya llevamos un buen tramo del test. ¡Sigamos!"

_PALABRAS_A_NUMERO = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
}
_PALABRAS_SI = {"si", "sí", "s", "yes", "confirmo", "dale", "ok", "okay"}
_PALABRAS_NO = {"no", "n"}

# Comandos especiales (funcionalidad #2 y #4 del catálogo de la Fase 7):
# cada texto normalizado del usuario que coincida con alguna de estas
# variantes dispara el comando correspondiente, en vez de tratarse como
# respuesta Likert inválida o intentar matchear contra el banco de FAQs.
_COMANDOS: dict[str, set[str]] = {
    "ayuda": {"ayuda", "help", "que puedo hacer", "comandos"},
    "repetir": {"repetir", "repite", "repetir pregunta", "puedes repetir"},
    "anterior": {
        "anterior",
        "atras",
        "regresar",
        "volver",
        "corregir",
        "corregir ultima respuesta",
    },
    "progreso": {"ver progreso", "progreso", "como voy", "cuanto me falta"},
    "pausar": {"pausar", "continuar despues", "guardar y salir"},
    "salir": {"salir"},
}


def _detectar_comando(texto: str) -> str | None:
    """Devuelve el nombre del comando reconocido, o None si no aplica."""
    texto_norm = normalizar_texto(texto)
    for comando, variantes in _COMANDOS.items():
        if texto_norm in variantes:
            return comando
    return None


class EstadoChatInvalidoError(ValueError):
    """La sesión de chat no tiene una forma reconocible (estado corrupto)."""


@dataclass
class MensajeBot:
    """Una o más burbujas que el bot envía en respuesta a un solo mensaje."""

    textos: list[str] = field(default_factory=list)
    chips: list[int] | None = None
    """Si no es None, el frontend debe mostrar chips numerados 1-5 (o los
    valores dados) además del campo de texto libre."""


def interpretar_likert(texto: str) -> int | None:
    """Acepta dígitos ('4') y números en palabras ('cuatro'). None si inválido."""
    valor = _PALABRAS_A_NUMERO.get(texto.strip().lower())
    return valor


def interpretar_si_no(texto: str) -> bool | None:
    t = texto.strip().lower()
    if t in _PALABRAS_SI:
        return True
    if t in _PALABRAS_NO:
        return False
    return None


def crear_sesion_inicial() -> dict:
    """Estado inicial de una nueva sesión de chat, antes de `iniciar_conversacion`."""
    return {
        "fase": "bienvenida",
        "area_idx": 0,
        "limite_area_actual": None,
        "respuestas_por_area": {area: [] for area in AREAS},
        "preguntas_usadas": [],
        "pregunta_actual_id": None,
        "total_formuladas": 0,
        "historial": [],
        "intentos_invalidos": 0,
        "pausado": False,
        "ultimo_resultado": None,
        "ultimo_vector_usuario": None,
        "analitica": {
            "intents_disparados": [],
            "respuestas_invalidas": 0,
            "area_abandono": None,
            # Fase 10 — trazabilidad reglas/IA: cuántas veces, en esta
            # sesión, una respuesta salió de la capa de IA en vez de una
            # regla determinista. Útil para logging/depuración; nunca
            # afecta el flujo del test.
            "respuestas_ia_usadas": 0,
        },
    }


def _texto_pregunta(preguntas_textos: dict[int, str], pregunta_id: int) -> str:
    return preguntas_textos.get(pregunta_id, f"(pregunta {pregunta_id})")


def _agregar(historial: list[dict], rol: str, texto: str) -> None:
    historial.append({"rol": rol, "texto": texto})


def _preguntar_area(
    estado: dict,
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    transicion: str | None,
) -> None:
    """Formula la primera pregunta pendiente del área actual (`area_idx`)."""
    area = AREAS[estado["area_idx"]]
    ids_area = preguntas_por_area.get(area, [])
    idx_en_area = len(estado["respuestas_por_area"][area])
    pregunta_id = ids_area[idx_en_area]
    estado["pregunta_actual_id"] = pregunta_id
    estado["fase"] = "esperando_respuesta_likert"

    prefijo = f"{transicion} " if transicion else ""
    estado["_ultimo_mensaje"] = (
        f"{prefijo}{_texto_pregunta(preguntas_textos, pregunta_id)}"
    )


def iniciar_conversacion(
    estado: dict,
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
) -> MensajeBot:
    """Primer turno: mensaje de bienvenida + primera pregunta del área 0."""
    if estado["fase"] != "bienvenida":
        raise EstadoChatInvalidoError("La conversación ya fue iniciada.")

    textos = [MENSAJE_BIENVENIDA]
    _agregar(estado["historial"], "bot", MENSAJE_BIENVENIDA)

    _preguntar_area(estado, preguntas_por_area, preguntas_textos, transicion=None)
    textos.append(estado["_ultimo_mensaje"])
    _agregar(estado["historial"], "bot", estado["_ultimo_mensaje"])

    return MensajeBot(textos=textos, chips=[1, 2, 3, 4, 5])


async def procesar_mensaje(
    estado: dict,
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    texto_usuario: str,
) -> tuple[MensajeBot, bool]:
    """
    Router central de mensajes: decide qué hacer según `estado["fase"]`.

    Returns:
        (mensaje_bot, listo_para_calcular) — `listo_para_calcular` es True
        únicamente cuando el usuario acaba de confirmar ("sí") en
        "esperando_confirmacion_final"; en ese caso el caller (router HTTP)
        debe llamar a `construir_vector_usuario` sobre
        `estado["respuestas_por_area"]` y al motor de Mahalanobis.
    """
    _agregar(estado["historial"], "usuario", texto_usuario)

    if estado["fase"] == "esperando_respuesta_likert":
        return await _procesar_respuesta_likert(
            estado, preguntas_por_area, preguntas_textos, texto_usuario
        ), False

    if estado["fase"] == "esperando_confirmacion_final":
        confirmado = interpretar_si_no(texto_usuario)
        if confirmado is None:
            intent = buscar_intent_faq(texto_usuario)
            if intent is not None:
                intent_id, respuesta_faq = intent
                estado["analitica"]["intents_disparados"].append(intent_id)
                textos = [
                    respuesta_faq,
                    "¿Confirmas que quieres ver tu resultado? Responde 'sí' o 'no'.",
                ]
                for t in textos:
                    _agregar(estado["historial"], "bot", t)
                return MensajeBot(textos=textos, chips=None), False

            msg = MensajeBot(
                textos=[
                    "No entendí tu respuesta. ¿Confirmas que quieres ver tu "
                    "resultado? Responde 'sí' o 'no'."
                ],
                chips=None,
            )
            _agregar(estado["historial"], "bot", msg.textos[0])
            return msg, False
        if confirmado:
            estado["fase"] = "post_resultado"
            return MensajeBot(textos=[]), True
        msg = MensajeBot(
            textos=[
                "Sin problema, revisemos: ¿confirmas que quieres calcular tu "
                "resultado ahora? Responde 'sí' o 'no'."
            ]
        )
        _agregar(estado["historial"], "bot", msg.textos[0])
        return msg, False

    if estado["fase"] == "post_resultado":
        texto = await responder_pregunta_seguimiento(texto_usuario, estado)
        _agregar(estado["historial"], "bot", texto)
        return MensajeBot(textos=[texto]), False

    raise EstadoChatInvalidoError(f"Fase de conversación desconocida: {estado['fase']!r}")


def _detectar_carreras_mencionadas(texto_norm: str, resultados: list[dict]) -> list[dict]:
    """Devuelve, en el orden en que aparecen en el Top 5, las carreras cuyo
    nombre (normalizado) el usuario mencionó en su mensaje."""
    mencionadas = []
    for resultado in resultados:
        if normalizar_texto(resultado["nombre"]) in texto_norm:
            mencionadas.append(resultado)
    return mencionadas


def _armar_comparacion(carreras: list[dict]) -> str:
    c1, c2 = carreras[0], carreras[1]
    diferencia = round(abs(c1["afinidad_pct"] - c2["afinidad_pct"]), 1)
    return (
        f"{c1['nombre']}: {c1['afinidad_pct']}% de afinidad, fortalezas en "
        f"{', '.join(c1['fortalezas'][:2]) or 'un perfil equilibrado'}.\n"
        f"{c2['nombre']}: {c2['afinidad_pct']}% de afinidad, fortalezas en "
        f"{', '.join(c2['fortalezas'][:2]) or 'un perfil equilibrado'}.\n"
        f"La diferencia de afinidad entre ambas es de {diferencia} puntos "
        "porcentuales."
    )


async def responder_pregunta_seguimiento(texto_usuario: str, estado: dict) -> str:
    """
    Funcionalidad #10 — preguntas de seguimiento tras el resultado. El orden
    es siempre reglas primero: (1) patrones fijos de "por qué"/"comparar",
    (2) banco de FAQs, y solo si ninguna de esas dos coincidió, (3) la capa
    de IA (Fase 10), respondiendo ÚNICAMENTE con los datos reales del Top 5
    ya calculado. Si la IA está deshabilitada o falla, se usa el mismo
    mensaje fijo de siempre — nunca se inventa una respuesta.
    """
    resultados = estado.get("ultimo_resultado") or []
    texto_norm = normalizar_texto(texto_usuario)

    if resultados and any(re.search(p, texto_norm) for p in _PATRONES_POR_QUE):
        c = resultados[0]
        fortalezas = ", ".join(c["fortalezas"][:3]) or "un perfil equilibrado en varias áreas"
        return (
            f"Te recomendé {c['nombre']} porque tu perfil mostró alta afinidad en "
            f"{fortalezas}, áreas clave para esa carrera. Tu distancia estadística "
            f"fue de {c['distancia_mahalanobis']}, la más baja entre las 37 "
            "carreras evaluadas."
        )

    if resultados and any(re.search(p, texto_norm) for p in _PATRONES_COMPARAR):
        mencionadas = _detectar_carreras_mencionadas(texto_norm, resultados)
        if len(mencionadas) >= 2:
            return _armar_comparacion(mencionadas[:2])
        return (
            "Dime cuáles dos carreras de tu Top 5 quieres comparar, por "
            "ejemplo: 'compara " + resultados[0]["nombre"] + " con "
            + (resultados[1]["nombre"] if len(resultados) > 1 else "otra carrera")
            + "'."
        )

    intent = buscar_intent_faq(texto_usuario)
    if intent is not None:
        intent_id, respuesta_faq = intent
        estado["analitica"]["intents_disparados"].append(intent_id)
        respuesta_final = await generar_respuesta_faq_asistida(texto_usuario, respuesta_faq)
        if respuesta_final != respuesta_faq:
            estado["analitica"]["respuestas_ia_usadas"] += 1
        return respuesta_final

    # Fase 10 — última instancia antes del fallback fijo: la IA responde
    # apoyándose ÚNICAMENTE en `resultados` (el Top 5 real ya calculado).
    # Nunca puede mencionar una carrera, % o distancia que no esté ahí.
    respuesta_ia = await responder_pregunta_sobre_resultado(texto_usuario, resultados)
    if respuesta_ia is not None:
        estado["analitica"]["respuestas_ia_usadas"] += 1
        return respuesta_ia

    estado["analitica"]["respuestas_invalidas"] += 1
    # Fallback fijo (funcionalidad #7) — nunca se inventa una respuesta.
    return (
        "No logré identificar tu pregunta. Puedo explicarte por qué te "
        "recomendé una carrera, o comparar dos carreras de tu Top 5. ¿Qué "
        "te gustaría saber?"
    )


def _resumen_progreso(estado: dict) -> str:
    areas_completadas = sum(
        1 for area in AREAS if len(estado["respuestas_por_area"][area]) > 0
    ) - (1 if estado["fase"] == "esperando_respuesta_likert" else 0)
    areas_completadas = max(areas_completadas, 0)
    return (
        f"Vas por el área {estado['area_idx'] + 1} de {len(AREAS)} "
        f"({areas_completadas} áreas ya completadas). "
        f"Llevas {estado['total_formuladas']} preguntas respondidas."
    )


def _repetir_pregunta_actual(estado: dict, preguntas_textos: dict[int, str]) -> MensajeBot:
    pregunta_id = estado["pregunta_actual_id"]
    texto = _texto_pregunta(preguntas_textos, pregunta_id)
    _agregar(estado["historial"], "bot", texto)
    return MensajeBot(textos=[texto], chips=[1, 2, 3, 4, 5])


def _procesar_comando_likert(
    comando: str,
    estado: dict,
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
) -> MensajeBot | None:
    """Maneja los comandos especiales durante `esperando_respuesta_likert`.

    Devuelve `None` si el comando no es uno de los reconocidos aquí (para que
    el caller siga con el resto de la lógica).
    """
    if comando == "ayuda":
        texto = (
            "Puedo ayudarte con esto: responde un número del 1 al 5 a cada "
            "pregunta; escribe 'repetir' para volver a leerla, 'anterior' "
            "para corregir tu última respuesta, 'ver progreso' para saber en "
            "qué área vas, o 'pausar' para guardar tu avance. También puedes "
            "preguntarme cosas como '¿cuánto dura el test?'."
        )
        _agregar(estado["historial"], "bot", texto)
        return MensajeBot(textos=[texto], chips=[1, 2, 3, 4, 5])

    if comando == "repetir":
        return _repetir_pregunta_actual(estado, preguntas_textos)

    if comando == "progreso":
        texto = _resumen_progreso(estado)
        _agregar(estado["historial"], "bot", texto)
        msg = _repetir_pregunta_actual(estado, preguntas_textos)
        return MensajeBot(textos=[texto, *msg.textos], chips=msg.chips)

    if comando in ("pausar", "salir"):
        estado["pausado"] = True
        texto = (
            "Tu avance quedó guardado. Puedes volver cuando quieras y "
            "continuaremos justo donde lo dejamos."
        )
        _agregar(estado["historial"], "bot", texto)
        return MensajeBot(textos=[texto], chips=None)

    if comando == "anterior":
        return _retroceder_pregunta(estado, preguntas_por_area, preguntas_textos)

    return None


def _retroceder_pregunta(
    estado: dict,
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
) -> MensajeBot:
    """
    Comando 'anterior': descarta la última respuesta registrada del área
    actual y vuelve a formular esa misma pregunta, recalculando el
    presupuesto del área con las mismas reglas de la Lógica Adaptativa.
    """
    area = AREAS[estado["area_idx"]]
    respuestas_area = estado["respuestas_por_area"][area]

    if not respuestas_area:
        texto = "No hay una respuesta previa en esta área para corregir."
        _agregar(estado["historial"], "bot", texto)
        msg = _repetir_pregunta_actual(estado, preguntas_textos)
        return MensajeBot(textos=[texto, *msg.textos], chips=msg.chips)

    respuestas_area.pop()
    estado["preguntas_usadas"].pop()
    estado["total_formuladas"] -= 1
    estado["limite_area_actual"] = respuestas_area[0] if respuestas_area else None

    ids_area = preguntas_por_area.get(area, [])
    idx_en_area = len(respuestas_area)
    estado["pregunta_actual_id"] = ids_area[idx_en_area]

    texto = "Sin problema, corrijamos esa respuesta."
    _agregar(estado["historial"], "bot", texto)
    msg = _repetir_pregunta_actual(estado, preguntas_textos)
    return MensajeBot(textos=[texto, *msg.textos], chips=msg.chips)


async def _procesar_respuesta_likert(
    estado: dict,
    preguntas_por_area: dict[str, list[int]],
    preguntas_textos: dict[int, str],
    texto_usuario: str,
) -> MensajeBot:
    comando = _detectar_comando(texto_usuario)
    if comando is not None:
        resultado_comando = _procesar_comando_likert(
            comando, estado, preguntas_por_area, preguntas_textos
        )
        if resultado_comando is not None:
            return resultado_comando

    valor = interpretar_likert(texto_usuario)
    origen_ia = False

    if valor is None:
        # Antes de tratarla como inválida, ¿es una pregunta abierta del
        # banco de FAQs (funcionalidad #2/#3)? Si coincide, se responde y se
        # repite la pregunta pendiente SIN avanzar el estado ni contar como
        # respuesta inválida.
        intent = buscar_intent_faq(texto_usuario)
        if intent is not None:
            intent_id, respuesta_faq = intent
            estado["analitica"]["intents_disparados"].append(intent_id)
            respuesta_final = await generar_respuesta_faq_asistida(
                texto_usuario, respuesta_faq
            )
            if respuesta_final != respuesta_faq:
                estado["analitica"]["respuestas_ia_usadas"] += 1
            _agregar(estado["historial"], "bot", respuesta_final)
            msg = _repetir_pregunta_actual(estado, preguntas_textos)
            return MensajeBot(textos=[respuesta_final, *msg.textos], chips=msg.chips)

        # Fase 10 — reglas ya fallaron (ni dígito/palabra clave, ni FAQ
        # conocida): último intento, vía IA, de interpretar una respuesta
        # ambigua a la pregunta Likert actual. Si la IA está deshabilitada,
        # falla, o no alcanza el umbral de confianza, `valor` sigue en
        # `None` y el flujo cae exactamente al mensaje de aclaración de
        # siempre — ningún comportamiento nuevo visible para el usuario en
        # ese caso.
        valor, _confianza = await interpretar_respuesta_libre(
            texto_usuario, _texto_pregunta(preguntas_textos, estado["pregunta_actual_id"])
        )
        if valor is not None:
            origen_ia = True
            estado["analitica"]["respuestas_ia_usadas"] += 1
            logger.info(
                "Respuesta Likert interpretada por IA (pregunta %s, confianza %.2f)",
                estado["pregunta_actual_id"],
                _confianza,
            )

    if valor is None:
        # Validación estricta: respuesta inválida no avanza el estado.
        estado["intentos_invalidos"] += 1
        estado["analitica"]["respuestas_invalidas"] += 1
        pregunta_id = estado["pregunta_actual_id"]
        textos = [
            "No entendí tu respuesta. Por favor responde con un número del "
            "1 al 5 (1 = No me gusta nada … 5 = Me gusta mucho).\n"
            f"{_texto_pregunta(preguntas_textos, pregunta_id)}"
        ]
        _agregar(estado["historial"], "bot", textos[0])

        if estado["intentos_invalidos"] >= LIMITE_REINTENTOS_INVALIDOS:
            oferta = (
                "Parece que el chat no es lo tuyo ahora mismo — ¿prefieres "
                "cambiar al formulario tradicional? Puedes hacerlo cuando "
                "quieras desde la pantalla de inicio; aquí también puedo "
                "seguir ayudándote."
            )
            textos.append(oferta)
            _agregar(estado["historial"], "bot", oferta)
            estado["intentos_invalidos"] = 0

        return MensajeBot(textos=textos, chips=[1, 2, 3, 4, 5])

    estado["intentos_invalidos"] = 0
    area = AREAS[estado["area_idx"]]
    ids_area = preguntas_por_area.get(area, [])
    respuestas_area = estado["respuestas_por_area"][area]

    respuestas_area.append(valor)
    estado["preguntas_usadas"].append(estado["pregunta_actual_id"])
    estado["total_formuladas"] += 1
    idx_en_area = len(respuestas_area) - 1  # índice de la respuesta recién agregada

    if idx_en_area == 0:
        estado["limite_area_actual"] = valor
        area_terminada = valor <= 1
    else:
        limite = estado["limite_area_actual"]
        if valor < 3:
            area_terminada = True
        else:
            area_terminada = (idx_en_area + 1) >= min(limite, len(ids_area))

    textos: list[str] = []
    chips: list[int] | None = [1, 2, 3, 4, 5]

    if origen_ia:
        # Transparencia: cuando la IA interpretó una respuesta ambigua, se
        # lo confirmamos al usuario en vez de avanzar en silencio — así, si
        # la interpretación fue incorrecta, el usuario lo nota de inmediato
        # y puede usar el comando "anterior" para corregirla.
        confirmacion = f"Entendí tu respuesta como un {valor} de 5."
        textos.append(confirmacion)
        _agregar(estado["historial"], "bot", confirmacion)

    if not area_terminada:
        _preguntar_area(estado, preguntas_por_area, preguntas_textos, transicion=None)
        textos.append(estado["_ultimo_mensaje"])
        _agregar(estado["historial"], "bot", estado["_ultimo_mensaje"])
    else:
        estado["limite_area_actual"] = None
        estado["area_idx"] += 1
        if estado["area_idx"] >= len(AREAS):
            estado["fase"] = "esperando_confirmacion_final"
            estado["pregunta_actual_id"] = None
            cierre = (
                "¡Con eso terminamos las 17 áreas! Ya tengo suficiente "
                "información sobre tus intereses. ¿Confirmas que quieres "
                "ver tu resultado ahora? Responde 'sí' o 'no'."
            )
            textos.append(cierre)
            _agregar(estado["historial"], "bot", cierre)
            chips = None
        else:
            transicion = _TRANSICIONES[estado["area_idx"] % len(_TRANSICIONES)]
            _preguntar_area(estado, preguntas_por_area, preguntas_textos, transicion)
            textos.append(estado["_ultimo_mensaje"])
            _agregar(estado["historial"], "bot", estado["_ultimo_mensaje"])

    if (
        estado["total_formuladas"] > 0
        and estado["total_formuladas"] % _MOTIVACION_CADA_N_PREGUNTAS == 0
        and estado["fase"] == "esperando_respuesta_likert"
    ):
        textos.append(_MENSAJE_MOTIVACION)
        _agregar(estado["historial"], "bot", _MENSAJE_MOTIVACION)

    return MensajeBot(textos=textos, chips=chips)


def construir_vector_desde_sesion(estado: dict) -> dict[str, float]:
    """Vector de usuario final, reutilizando la misma fórmula del Método 1."""
    return construir_vector_usuario(estado["respuestas_por_area"])
