"""
Validación de arranque (obligatoria por el prompt maestro): las claves de
`AREAS` deben coincidir **exactamente**, nombre por nombre y en cantidad, con
las columnas del dataset de carreras (`data/carreras.csv`) y con las claves de
`data/areas.json`. Cualquier desalineación silenciosa produciría un vector de
usuario comparado contra la columna equivocada en el motor de Mahalanobis.

Se ejecuta en el evento `startup` de FastAPI (ver `app/main.py`) y falla de
forma explícita (`RuntimeError`) si algo no coincide, en vez de continuar con
datos corruptos.
"""
from app.core.constants import AREAS
from app.data.loaders import cargar_areas, cargar_carreras, cargar_preguntas


def validar_alineacion_areas() -> None:
    """Lanza `RuntimeError` si AREAS, areas.json y carreras.csv no coinciden."""
    if len(AREAS) != 17:
        raise RuntimeError(
            f"AREAS debe tener exactamente 17 elementos, tiene {len(AREAS)}."
        )

    areas_json_keys = [a["key"] for a in cargar_areas()]
    if areas_json_keys != AREAS:
        raise RuntimeError(
            "Las claves de data/areas.json no coinciden (en orden o contenido) "
            f"con la constante AREAS.\nAREAS={AREAS}\nareas.json={areas_json_keys}"
        )

    carreras = cargar_carreras()
    if len(carreras) != 37:
        raise RuntimeError(
            f"Se esperaban 37 carreras en data/carreras.csv, se encontraron {len(carreras)}."
        )

    columnas_csv = set(carreras[0]["puntajes"].keys())
    if columnas_csv != set(AREAS):
        faltantes = set(AREAS) - columnas_csv
        sobrantes = columnas_csv - set(AREAS)
        raise RuntimeError(
            "Las columnas de data/carreras.csv no coinciden con AREAS. "
            f"Faltantes: {faltantes or 'ninguna'}. Sobrantes: {sobrantes or 'ninguna'}."
        )


def validar_banco_preguntas() -> None:
    """Lanza `RuntimeError` si el banco de preguntas no tiene 34 entradas válidas."""
    preguntas = cargar_preguntas()
    if len(preguntas) != 34:
        raise RuntimeError(
            f"Se esperaban 34 preguntas en data/preguntas.json, se encontraron {len(preguntas)}."
        )
    areas_en_preguntas = {p["area"] for p in preguntas}
    areas_invalidas = areas_en_preguntas - set(AREAS)
    if areas_invalidas:
        raise RuntimeError(
            f"data/preguntas.json referencia áreas inexistentes: {areas_invalidas}"
        )


def run_startup_checks() -> None:
    """Punto único invocado desde el evento startup de FastAPI."""
    validar_alineacion_areas()
    validar_banco_preguntas()