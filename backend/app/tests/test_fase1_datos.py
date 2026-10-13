"""
Tests de la Fase 1: validación de alineación entre AREAS, data/areas.json y
data/carreras.csv, y verificación del tamaño del banco de preguntas.

Estos tests no requieren una base de datos activa: prueban las funciones puras
de `core/constants.py`, `core/startup_checks.py` y `data/loaders.py`, que leen
directamente los archivos JSON/CSV.
"""
import pytest

from app.core.constants import AREAS
from app.core.startup_checks import validar_alineacion_areas, validar_banco_preguntas
from app.data.loaders import cargar_areas, cargar_carreras, cargar_preguntas


def test_areas_tiene_exactamente_17_elementos():
    assert len(AREAS) == 17


def test_areas_coincide_con_areas_json_en_orden_y_contenido():
    areas_json_keys = [a["key"] for a in cargar_areas()]
    assert areas_json_keys == AREAS


def test_areas_coincide_con_columnas_de_carreras_csv():
    carreras = cargar_carreras()
    assert len(carreras) == 37
    columnas = set(carreras[0]["puntajes"].keys())
    assert columnas == set(AREAS)


def test_validacion_de_arranque_no_lanza_excepcion():
    # No debe lanzar RuntimeError si los datasets están correctamente alineados.
    validar_alineacion_areas()


def test_banco_de_preguntas_tiene_34_entradas():
    preguntas = cargar_preguntas()
    assert len(preguntas) == 34
    validar_banco_preguntas()  # no debe lanzar


def test_preguntas_ids_son_1_a_34_sin_huecos():
    preguntas = cargar_preguntas()
    ids = sorted(p["id"] for p in preguntas)
    assert ids == list(range(1, 35))


def test_cada_area_tiene_exactamente_2_preguntas():
    preguntas = cargar_preguntas()
    conteo_por_area: dict[str, int] = {}
    for p in preguntas:
        conteo_por_area[p["area"]] = conteo_por_area.get(p["area"], 0) + 1
    assert conteo_por_area == {area: 2 for area in AREAS}


def test_validar_alineacion_falla_explicitamente_si_falta_un_area(monkeypatch):
    """Si AREAS tuviera un área de más que no existe en el dataset, debe fallar
    con un RuntimeError explícito, nunca de forma silenciosa."""
    import app.core.startup_checks as sc

    def areas_incompletas():
        return [{"key": k, "label": k} for k in AREAS[:-1]] + [
            {"key": "area_inventada", "label": "Área inventada"}
        ]

    monkeypatch.setattr(sc, "cargar_areas", areas_incompletas)

    with pytest.raises(RuntimeError):
        sc.validar_alineacion_areas()