"""
Lógica pura de la Fase 9b: convertir un `IntentoTest` (modelo SQLAlchemy) en
el resumen que se expone en `GET /usuarios/me/intentos`.

Se separa del router (igual patrón que `recomendacion_service`,
`test_service`, `chatbot_service` en fases anteriores) para poder testearla
sin necesitar PostgreSQL: solo depende de los atributos ya cargados en el
objeto `IntentoTest`, no de la sesión de base de datos.
"""
from app.models.intento_test import IntentoTest


def resumen_intento(intento: IntentoTest) -> dict:
    """
    Arma el dict que consume `IntentoResumenOut`.

    - `carrera_top1` / `afinidad_top1_pct` quedan en `None` cuando el intento
      todavía está en progreso (`top5_resultado` nulo) — típicamente una
      sesión de chatbot que el usuario abandonó a mitad de la conversación.
    - Se usa `top5_resultado[0]` en vez de recalcular nada: es exactamente el
      snapshot ya persistido al completar el intento (misma fuente de verdad
      que la pantalla de resultados), así el historial nunca puede mostrar
      un Top 1 distinto al que el usuario vio al terminar el test.
    """
    top1 = intento.top5_resultado[0] if intento.top5_resultado else None

    return {
        "id": intento.id,
        "metodo": intento.metodo,
        "estado": intento.estado,
        "iniciado_en": intento.iniciado_en,
        "completado_en": intento.completado_en,
        "carrera_top1_id": top1["carrera_id"] if top1 else None,
        "carrera_top1": top1["nombre"] if top1 else None,
        "afinidad_top1_pct": top1["afinidad_pct"] if top1 else None,
    }


def ordenar_intentos_por_fecha_desc(intentos: list[IntentoTest]) -> list[IntentoTest]:
    """
    Orden del historial: más reciente primero. `iniciado_en` (no
    `completado_en`) porque un intento en progreso no tiene fecha de cierre
    y de todas formas debe aparecer ubicado por cuándo se empezó.
    """
    return sorted(intentos, key=lambda i: i.iniciado_en, reverse=True)
