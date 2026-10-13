"""
Seed idempotente de la base de datos: carga las 17 áreas, las 34 preguntas y
las 37 carreras (con sus 17 puntajes cada una) desde `data/areas.json`,
`data/preguntas.json` y `data/carreras.csv`.

Idempotente: puede ejecutarse múltiples veces sin duplicar filas — usa
"insertar si no existe" (`merge`/chequeo previo) por clave natural
(`Area.key`, `Pregunta.id`, `Carrera.nombre`).

Uso:
    python -m app.scripts.seed_data
"""
import asyncio

from sqlalchemy import select

from app.core.constants import AREAS
from app.core.database import AsyncSessionLocal, engine
from app.core.startup_checks import run_startup_checks
from app.data.loaders import cargar_areas, cargar_carreras, cargar_preguntas
from app.models import Area, Carrera, CarreraPuntaje, Pregunta


async def seed_areas(db) -> None:
    existentes = {a.key for a in (await db.execute(select(Area))).scalars().all()}
    for orden, area in enumerate(cargar_areas()):
        if area["key"] in existentes:
            continue
        db.add(Area(key=area["key"], label=area["label"], orden=orden))
    await db.flush()


async def seed_preguntas(db) -> None:
    existentes = {p.id for p in (await db.execute(select(Pregunta))).scalars().all()}
    for pregunta in cargar_preguntas():
        if pregunta["id"] in existentes:
            continue
        db.add(
            Pregunta(id=pregunta["id"], area_key=pregunta["area"], texto=pregunta["texto"])
        )
    await db.flush()


async def seed_carreras(db) -> None:
    existentes = {
        c.nombre: c for c in (await db.execute(select(Carrera))).scalars().all()
    }
    for carrera_data in cargar_carreras():
        carrera = existentes.get(carrera_data["nombre"])
        if carrera is None:
            carrera = Carrera(nombre=carrera_data["nombre"])
            db.add(carrera)
            await db.flush()  # necesario para tener carrera.id antes de crear puntajes

        puntajes_existentes = {
            p.area_key
            for p in (
                await db.execute(
                    select(CarreraPuntaje).where(CarreraPuntaje.carrera_id == carrera.id)
                )
            )
            .scalars()
            .all()
        }
        for area in AREAS:
            if area in puntajes_existentes:
                continue
            db.add(
                CarreraPuntaje(
                    carrera_id=carrera.id,
                    area_key=area,
                    valor=carrera_data["puntajes"][area],
                )
            )
    await db.flush()


async def run_seed() -> None:
    # Falla rápido y explícito si los datasets no están alineados antes de escribir nada.
    run_startup_checks()

    async with AsyncSessionLocal() as db:
        await seed_areas(db)
        await seed_preguntas(db)
        await seed_carreras(db)
        await db.commit()

    # dispose() debe correr en el mismo event loop que el resto del seed,
    # o asyncpg falla con "Event loop is closed" al cerrar la conexión.
    await engine.dispose()

    print("Seed completado: 17 áreas, 34 preguntas, 37 carreras (idempotente).")


if __name__ == "__main__":
    asyncio.run(run_seed())