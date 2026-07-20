"""
Tests de la Fase 9b — Intentos asociados a usuario e historial.

Cubren `app.services.historial_service`, que es lógica pura (no toca la
sesión de base de datos): recibe instancias de `IntentoTest` ya construidas
en memoria y arma el resumen/orden que expone `GET /usuarios/me/intentos`.
Igual que en fases anteriores, la verificación HTTP end-to-end (asociar
`usuario_id` de verdad al enviar `POST /test/tradicional` con un token, y
consultar el endpoint contra PostgreSQL) queda documentada como manual en
`docs/fases/fase-9b-intentos-historial.md`, ya que este entorno de CI no
levanta una base de datos Postgres real.
"""
import datetime as dt

from app.models.intento_test import EstadoIntento, IntentoTest, MetodoTest
from app.services.historial_service import ordenar_intentos_por_fecha_desc, resumen_intento


def _intento(
    *,
    id: int,
    iniciado_en: dt.datetime,
    metodo: MetodoTest = MetodoTest.TRADICIONAL,
    estado: EstadoIntento = EstadoIntento.COMPLETADO,
    top5_resultado: list | None = None,
    completado_en: dt.datetime | None = None,
) -> IntentoTest:
    """Construye un `IntentoTest` en memoria, sin tocar la base de datos."""
    intento = IntentoTest(
        metodo=metodo,
        estado=estado,
        top5_resultado=top5_resultado,
        completado_en=completado_en,
    )
    intento.id = id
    intento.iniciado_en = iniciado_en
    return intento


def test_resumen_intento_completado_incluye_carrera_top1():
    top5 = [
        {"carrera_id": 3, "nombre": "Ingeniería de Sistemas", "afinidad_pct": 91.4},
        {"carrera_id": 7, "nombre": "Ingeniería Civil", "afinidad_pct": 80.1},
    ]
    intento = _intento(
        id=1,
        iniciado_en=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
        completado_en=dt.datetime(2026, 7, 1, 0, 12, tzinfo=dt.UTC),
        top5_resultado=top5,
    )

    resumen = resumen_intento(intento)

    assert resumen["id"] == 1
    assert resumen["metodo"] == MetodoTest.TRADICIONAL
    assert resumen["estado"] == EstadoIntento.COMPLETADO
    assert resumen["carrera_top1_id"] == 3
    assert resumen["carrera_top1"] == "Ingeniería de Sistemas"
    assert resumen["afinidad_top1_pct"] == 91.4


def test_resumen_intento_en_progreso_no_tiene_top1():
    intento = _intento(
        id=2,
        iniciado_en=dt.datetime(2026, 7, 2, tzinfo=dt.UTC),
        metodo=MetodoTest.CHATBOT,
        estado=EstadoIntento.EN_PROGRESO,
        top5_resultado=None,
        completado_en=None,
    )

    resumen = resumen_intento(intento)

    assert resumen["carrera_top1_id"] is None
    assert resumen["carrera_top1"] is None
    assert resumen["afinidad_top1_pct"] is None
    assert resumen["completado_en"] is None


def test_ordenar_intentos_por_fecha_desc_pone_el_mas_reciente_primero():
    viejo = _intento(id=1, iniciado_en=dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    intermedio = _intento(id=2, iniciado_en=dt.datetime(2026, 6, 1, tzinfo=dt.UTC))
    reciente = _intento(id=3, iniciado_en=dt.datetime(2026, 7, 10, tzinfo=dt.UTC))

    ordenados = ordenar_intentos_por_fecha_desc([intermedio, viejo, reciente])

    assert [i.id for i in ordenados] == [3, 2, 1]


def test_ordenar_intentos_no_muta_la_lista_original():
    a = _intento(id=1, iniciado_en=dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    b = _intento(id=2, iniciado_en=dt.datetime(2026, 2, 1, tzinfo=dt.UTC))
    original = [a, b]

    ordenar_intentos_por_fecha_desc(original)

    assert original == [a, b]
