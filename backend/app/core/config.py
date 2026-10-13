"""
Configuración central de la aplicación (Fase 0).

Todas las variables sensibles/ambientales se leen desde variables de entorno
(o un archivo .env en desarrollo), nunca hardcodeadas.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Información general de la app
    app_name: str = "Sistema de Orientación Vocacional UNA Puno"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # Base de datos
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/vocacional_db"
    )

    # Autenticación JWT
    jwt_secret_key: str = Field(default="CHANGE_ME_IN_PRODUCTION")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # --- Chatbot híbrido (reglas + IA) ---
    # Feature flag: apagada por defecto. Con esto en False, el chatbot se
    # comporta EXACTAMENTE igual que antes (100% reglas); no hay ningún
    # cambio de comportamiento hasta que alguien la active a propósito.
    chatbot_ia_habilitada: bool = Field(default=False)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-3.1-flash-lite")
    ia_timeout_segundos: float = Field(default=6.0)
    # Umbral mínimo de confianza para aceptar la interpretación de una
    # respuesta Likert en lenguaje libre hecha por la IA (ver
    # app/services/ia/interprete_respuestas.py). Por debajo de esto, se
    # trata igual que si la IA no hubiera reconocido nada (cae a reglas).
    ia_umbral_confianza: float = Field(default=0.6)


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada de la configuración (singleton)."""
    return Settings()