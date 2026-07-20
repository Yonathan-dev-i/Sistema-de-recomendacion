"""
Tests de la Fase 2 — Motor de recomendación (Mahalanobis).

Usan directamente `data/carreras.csv` (vía `loaders.cargar_carreras`) para
construir la matriz `X` real de 37×17, sin depender de una base de datos ni
de FastAPI: el servicio de cálculo es puro por diseño (ver
`services/recomendacion_service.py`).

Cubre exactamente los 4 casos exigidos en el prompt maestro
("Requisitos no funcionales del cálculo"):
  (a) la matriz de covarianza se invierte sin error con los 37×17 datos reales.
  (b) el vector de distancias tiene longitud 37.
  (c) la carrera con distancia mínima corresponde al resultado top 1.
  (d) un vector de usuario idéntico al promedio general no lanza excepciones.
"""
import numpy as np
import pytest

from app.core.constants import AREAS
from app.data.loaders import cargar_carreras
from app.services.recomendacion_service import (
    calcular_distancias,
    calcular_matriz_covarianza,
    calcular_recomendacion,
)


@pytest.fixture(scope="module")
def matriz_carreras() -> tuple[list[str], np.ndarray]:
    carreras = cargar_carreras()
    nombres = [c["nombre"] for c in carreras]
    X = np.array([[c["puntajes"][area] for area in AREAS] for c in carreras], dtype=float)
    return nombres, X


@pytest.fixture(scope="module")
def inv_cov(matriz_carreras) -> np.ndarray:
    _, X = matriz_carreras
    _, inv_cov_matrix = calcular_matriz_covarianza(X)
    return inv_cov_matrix


# --- (a) La matriz de covarianza se invierte sin error con los datos reales ---


def test_matriz_covarianza_se_invierte_sin_error(matriz_carreras):
    _, X = matriz_carreras
    cov_matrix, inv_cov_matrix = calcular_matriz_covarianza(X)

    assert cov_matrix.shape == (17, 17)
    assert inv_cov_matrix.shape == (17, 17)
    assert np.all(np.isfinite(inv_cov_matrix))

    # inv_cov_matrix debe ser (aprox.) la inversa real de cov_matrix.
    identidad_aprox = cov_matrix @ inv_cov_matrix
    assert np.allclose(identidad_aprox, np.eye(17), atol=1e-2)


# --- (b) El vector de distancias tiene longitud 37 ---


def test_vector_de_distancias_tiene_longitud_37(matriz_carreras, inv_cov):
    nombres, X = matriz_carreras
    assert len(nombres) == 37

    x_usuario = X[0]  # cualquier vector válido de 17 dimensiones
    distancias = calcular_distancias(x_usuario, X, inv_cov)

    assert len(distancias) == 37
    assert all(isinstance(d, float) for d in distancias)
    assert all(d >= 0 for d in distancias)


# --- (c) La carrera con distancia mínima corresponde al resultado top 1 ---


def test_carrera_con_distancia_minima_es_el_top_1(matriz_carreras, inv_cov):
    nombres, X = matriz_carreras
    ids = list(range(1, len(nombres) + 1))

    # Vector de usuario = perfil exacto de una carrera conocida (ej. la #10).
    carrera_objetivo_idx = 10
    vector_usuario = dict(zip(AREAS, X[carrera_objetivo_idx], strict=True))

    resultados = calcular_recomendacion(
        vector_usuario=vector_usuario,
        X=X,
        carrera_ids=ids,
        carrera_nombres=nombres,
        areas=AREAS,
        inv_cov_matrix=inv_cov,
        top_n=5,
    )

    distancias_todas = calcular_distancias(X[carrera_objetivo_idx], X, inv_cov)
    idx_distancia_minima = int(np.argmin(distancias_todas))

    assert resultados[0].carrera_id == ids[idx_distancia_minima]
    assert resultados[0].nombre == nombres[idx_distancia_minima]
    # El propio perfil de la carrera objetivo debe ser (o empatar con) el más cercano.
    assert resultados[0].distancia_mahalanobis == pytest.approx(
        min(distancias_todas), abs=1e-6
    )
    # El top 1 debe tener la mayor afinidad del ranking.
    assert resultados[0].afinidad_pct == max(r.afinidad_pct for r in resultados)


def test_resultados_ordenados_de_mayor_a_menor_afinidad(matriz_carreras, inv_cov):
    nombres, X = matriz_carreras
    ids = list(range(1, len(nombres) + 1))
    vector_usuario = dict(zip(AREAS, X[3], strict=True))

    resultados = calcular_recomendacion(
        vector_usuario=vector_usuario,
        X=X,
        carrera_ids=ids,
        carrera_nombres=nombres,
        areas=AREAS,
        inv_cov_matrix=inv_cov,
        top_n=5,
    )

    assert len(resultados) == 5
    distancias = [r.distancia_mahalanobis for r in resultados]
    assert distancias == sorted(distancias)


# --- (d) Vector de usuario = promedio general no lanza excepciones ---


def test_vector_usuario_promedio_general_no_lanza_excepciones(matriz_carreras, inv_cov):
    nombres, X = matriz_carreras
    ids = list(range(1, len(nombres) + 1))

    promedio_general = X.mean(axis=0)
    vector_usuario = dict(zip(AREAS, promedio_general, strict=True))

    resultados = calcular_recomendacion(
        vector_usuario=vector_usuario,
        X=X,
        carrera_ids=ids,
        carrera_nombres=nombres,
        areas=AREAS,
        inv_cov_matrix=inv_cov,
        top_n=5,
    )

    assert len(resultados) == 5
    assert all(np.isfinite(r.distancia_mahalanobis) for r in resultados)
    assert all(0.0 <= r.afinidad_pct <= 100.0 for r in resultados)


def test_afinidad_maxima_es_100_para_el_top_1_del_ranking(matriz_carreras, inv_cov):
    """La conversión a % debe garantizar que el más cercano llegue (cerca) a 100%."""
    nombres, X = matriz_carreras
    ids = list(range(1, len(nombres) + 1))
    vector_usuario = dict(zip(AREAS, X[20], strict=True))

    resultados = calcular_recomendacion(
        vector_usuario=vector_usuario,
        X=X,
        carrera_ids=ids,
        carrera_nombres=nombres,
        areas=AREAS,
        inv_cov_matrix=inv_cov,
        top_n=37,  # todas, para verificar la normalización global 0-100
    )

    afinidades = [r.afinidad_pct for r in resultados]
    assert max(afinidades) == 100.0
    assert min(afinidades) == 0.0
