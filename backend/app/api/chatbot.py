"""
Endpoints del Método 2 — Chatbot basado en reglas (Fase 6).

El router solo orquesta (nunca calcula): carga preguntas desde PostgreSQL,
delega toda la máquina de estados en `services/chatbot_service.py` (puro),
persiste el estado de la sesión en `IntentoTest.estado_chat` para poder
reanudar tras un refresh, y —al confirmarse el cierre— reutiliza exactamente
el mismo `recomendacion_service.calcular_recomendacion` que
`POST /test/tradicional`, garantizando resultados idénticos ante las mismas
respuestas (regla de oro del prompt maestro).

Fase 9b: `POST /test/chatbot/iniciar` asocia la sesión a `usuario_id` si la
petición trae un access token válido, igual que `POST /test/tradicional`.
Los siguientes endpoints (`/mensaje`, `GET /{sesion_id}`) no necesitan volver
a resolver el usuario: la asociación ya quedó fijada en el intento desde
`/iniciar`.
"""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.constants import AREAS
from app.core.database import get_db
from app.core.deps import obtener_usuario_opcional
from app.data.loaders import cargar_areas
from app.models import EstadoIntento, IntentoTest, MetodoTest, Pregunta, RespuestaTest, Usuario
from app.schemas.chatbot import (
    ChatbotIniciarOut,
    ChatbotMensajeIn,
    ChatbotMensajeOut,
    ChatbotResultadoOut,
    ChatbotSesionOut,
    MensajeChatOut,
)
from app.services.chatbot_service import (
    EstadoChatInvalidoError,
    construir_vector_desde_sesion,
    crear_sesion_inicial,
    iniciar_conversacion,
    procesar_mensaje,
)
from app.services.recomendacion_service import calcular_recomendacion

router = APIRouter(prefix="/test/chatbot", tags=["chatbot"])

_AREAS_LABELS = {a["key"]: a["label"] for a in cargar_areas()}


async def _cargar_preguntas(
    db: AsyncSession,
) -> tuple[dict[str, list[int]], dict[int, str]]:
    result = await db.execute(
        select(Pregunta.id, Pregunta.area_key, Pregunta.texto).order_by(Pregunta.id)
    )
    preguntas_por_area: dict[str, list[int]] = {area: [] for area in AREAS}
    preguntas_textos: dict[int, str] = {}
    for pregunta_id, area_key, texto in result.all():
        preguntas_por_area[area_key].append(pregunta_id)
        preguntas_textos[pregunta_id] = texto
    return preguntas_por_area, preguntas_textos


async def _obtener_intento(db: AsyncSession, sesion_id: int) -> IntentoTest:
    intento = await db.get(IntentoTest, sesion_id)
    if intento is None or intento.metodo != MetodoTest.CHATBOT:
        raise HTTPException(status_code=404, detail="Sesión de chat no encontrada.")
    return intento


async def _finalizar_y_persistir(
    db: AsyncSession, request: Request, intento: IntentoTest, estado: dict
) -> ChatbotResultadoOut:
    vector_usuario = construir_vector_desde_sesion(estado)

    cache = request.app.state.recomendacion_cache
    resultados = calcular_recomendacion(
        vector_usuario=vector_usuario,
        X=cache.X,
        carrera_ids=cache.carrera_ids,
        carrera_nombres=cache.carrera_nombres,
        areas=AREAS,
        inv_cov_matrix=cache.inv_cov_matrix,
        areas_labels=_AREAS_LABELS,
        top_n=5,
    )
    resultados_dict = [r.__dict__ for r in resultados]

    estado["ultimo_resultado"] = resultados_dict
    estado["ultimo_vector_usuario"] = vector_usuario

    intento.estado = EstadoIntento.COMPLETADO
    intento.vector_usuario = vector_usuario
    intento.top5_resultado = resultados_dict
    intento.completado_en = dt.datetime.now(dt.UTC)
    intento.estado_chat = estado
    # Ver nota en app/models/intento_test.py ("Bug corregido"): sin esto,
    # las mutaciones anidadas dentro de `estado` (listas, dicts internos) no
    # siempre se detectan solo con MutableDict, así que se fuerza el marcado
    # explícito para garantizar que SIEMPRE se persista.
    flag_modified(intento, "estado_chat")

    # `preguntas_usadas` se llenó en el mismo orden (área por área, pregunta
    # por pregunta) que el aplanado de `respuestas_por_area` sobre `AREAS`,
    # así que ambas listas se corresponden posicionalmente 1 a 1.
    respuestas_planas_valores = [
        r for area in AREAS for r in estado["respuestas_por_area"][area]
    ]

    for pregunta_id, respuesta in zip(
        estado["preguntas_usadas"], respuestas_planas_valores, strict=True
    ):
        db.add(
            RespuestaTest(intento_id=intento.id, pregunta_id=pregunta_id, respuesta=respuesta)
        )

    await db.commit()

    return ChatbotResultadoOut(
        test_id=intento.id, vector_usuario=vector_usuario, resultados=resultados_dict
    )


@router.post("/iniciar", response_model=ChatbotIniciarOut)
async def iniciar_chat(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario | None = Depends(obtener_usuario_opcional),
) -> dict:
    preguntas_por_area, preguntas_textos = await _cargar_preguntas(db)

    estado = crear_sesion_inicial()
    mensaje = iniciar_conversacion(estado, preguntas_por_area, preguntas_textos)

    intento = IntentoTest(
        usuario_id=usuario.id if usuario else None,
        metodo=MetodoTest.CHATBOT,
        estado=EstadoIntento.EN_PROGRESO,
        estado_chat=estado,
    )
    db.add(intento)
    await db.commit()
    await db.refresh(intento)

    return {
        "sesion_id": intento.id,
        "mensajes": [{"rol": "bot", "texto": t} for t in mensaje.textos],
        "chips": mensaje.chips,
    }


@router.post("/{sesion_id}/mensaje", response_model=ChatbotMensajeOut)
async def enviar_mensaje(
    sesion_id: int,
    payload: ChatbotMensajeIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    intento = await _obtener_intento(db, sesion_id)

    if intento.estado == EstadoIntento.COMPLETADO:
        raise HTTPException(
            status_code=409, detail="Esta sesión de chat ya fue completada."
        )

    preguntas_por_area, preguntas_textos = await _cargar_preguntas(db)
    estado = intento.estado_chat

    try:
        mensaje, listo_para_calcular = await procesar_mensaje(
            estado, preguntas_por_area, preguntas_textos, payload.texto
        )
    except EstadoChatInvalidoError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    resultado_out: ChatbotResultadoOut | None = None
    if listo_para_calcular:
        resultado_out = await _finalizar_y_persistir(db, request, intento, estado)
        cierre = (
            f"¡Listo! Tu carrera con mayor afinidad es "
            f"{resultado_out.resultados[0].nombre} "
            f"({resultado_out.resultados[0].afinidad_pct}% de afinidad). "
            "Puedes revisar tu Top 5 completo en la pantalla de resultados."
        )
        estado["historial"].append({"rol": "bot", "texto": cierre})
        mensaje.textos = [*mensaje.textos, cierre]
    else:
        intento.estado_chat = estado
        # Sin esto, este UPDATE podía quedar completamente vacío (ver nota
        # en app/models/intento_test.py) y la conversación nunca avanzaba
        # de verdad en la base de datos.
        flag_modified(intento, "estado_chat")
        await db.commit()

    return {
        "mensajes": [{"rol": "bot", "texto": t} for t in mensaje.textos],
        "chips": mensaje.chips,
        "terminado": estado["fase"] == "post_resultado",
        "resultado": resultado_out,
    }


@router.get("/{sesion_id}", response_model=ChatbotSesionOut)
async def reanudar_chat(sesion_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Permite reconstruir visualmente la conversación completa desde el estado
    guardado en backend tras un refresh o cierre de pestaña.
    """
    intento = await _obtener_intento(db, sesion_id)
    estado = intento.estado_chat or {}
    historial = estado.get("historial", [])

    resultado_out = None
    if intento.estado == EstadoIntento.COMPLETADO and intento.vector_usuario:
        resultado_out = ChatbotResultadoOut(
            test_id=intento.id,
            vector_usuario=intento.vector_usuario,
            resultados=intento.top5_resultado or [],
        )

    fase = estado.get("fase", "bienvenida")
    chips = [1, 2, 3, 4, 5] if fase == "esperando_respuesta_likert" else None

    return {
        "sesion_id": intento.id,
        "fase": fase,
        "historial": [MensajeChatOut(**m) for m in historial],
        "chips": chips,
        "terminado": intento.estado == EstadoIntento.COMPLETADO,
        "resultado": resultado_out,
    }