"""Schemas Pydantic v2 para `POST /test/chatbot/*` (Fase 6)."""
from pydantic import BaseModel, Field

from app.schemas.recomendacion import ResultadoCarreraOut


class MensajeChatOut(BaseModel):
    rol: str  # "bot" | "usuario"
    texto: str


class ChatbotIniciarOut(BaseModel):
    sesion_id: int
    mensajes: list[MensajeChatOut]
    chips: list[int] | None = None


class ChatbotMensajeIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=500)


class ChatbotResultadoOut(BaseModel):
    test_id: int
    vector_usuario: dict[str, float]
    resultados: list[ResultadoCarreraOut]


class ChatbotMensajeOut(BaseModel):
    mensajes: list[MensajeChatOut]
    """Solo los mensajes nuevos generados por este turno (no todo el historial)."""
    chips: list[int] | None = None
    terminado: bool
    resultado: ChatbotResultadoOut | None = None


class ChatbotSesionOut(BaseModel):
    """Usado para reanudar la conversación tras un refresh (`GET /test/chatbot/{sesion_id}`)."""

    sesion_id: int
    fase: str
    historial: list[MensajeChatOut]
    chips: list[int] | None = None
    terminado: bool
    resultado: ChatbotResultadoOut | None = None
