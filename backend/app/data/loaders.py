"""
Carga de los datasets estáticos del dominio vocacional desde `app/data/`.

Estas funciones leen los archivos tal como se especifican en el prompt maestro
(`preguntas.json`, `areas.json`, `carreras.csv`) y son usadas tanto por el seed
inicial (carga a PostgreSQL) como por la validación de arranque.
"""
import csv
import json
from pathlib import Path
from typing import TypedDict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class AreaDict(TypedDict):
    key: str
    label: str


class PreguntaDict(TypedDict):
    id: int
    area: str
    texto: str


class CarreraDict(TypedDict):
    nombre: str
    puntajes: dict[str, int]


def cargar_areas() -> list[AreaDict]:
    """Carga las 17 áreas desde `data/areas.json`, en orden fijo."""
    with open(DATA_DIR / "areas.json", encoding="utf-8") as f:
        return json.load(f)


def cargar_preguntas() -> list[PreguntaDict]:
    """Carga las 85 preguntas desde `data/preguntas.json`, en orden de `id`."""
    with open(DATA_DIR / "preguntas.json", encoding="utf-8") as f:
        preguntas: list[PreguntaDict] = json.load(f)
    return sorted(preguntas, key=lambda p: p["id"])


def cargar_carreras() -> list[CarreraDict]:
    """Carga las 37 carreras x 17 áreas desde `data/carreras.csv`."""
    carreras: list[CarreraDict] = []
    with open(DATA_DIR / "carreras.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        area_cols = [c for c in (reader.fieldnames or []) if c != "carrera"]
        for row in reader:
            carreras.append(
                {
                    "nombre": row["carrera"],
                    "puntajes": {area: int(row[area]) for area in area_cols},
                }
            )
    return carreras
