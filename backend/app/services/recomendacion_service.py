"""
Motor de recomendación (Distancia de Mahalanobis) — Fase 2.

Todas las funciones de este módulo son **puras**: reciben la matriz de
perfiles de carreras (`X`), sus nombres/ids y el vector del usuario como
parámetros, y no dependen de FastAPI ni de una sesión de base de datos. Esto
permite testearlas de forma aislada y reutilizarlas desde cualquier endpoint
(`/recomendacion`, `/test/tradicional`, `/test/chatbot`) sin duplicar lógica.

Ver especificación exacta en el prompt maestro, sección
"Algoritmo de recomendación — Distancia de Mahalanobis".
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial.distance import mahalanobis

CONDICION_MAXIMA_ACEPTABLE = 1e10
EPSILON_SHRINKAGE = 1e-6


@dataclass
class ResultadoCarrera:
    carrera_id: int
    nombre: str
    distancia_mahalanobis: float
    afinidad_pct: float
    explicacion: str
    fortalezas: list[str] = field(default_factory=list)
    areas_por_mejorar: list[str] = field(default_factory=list)


def calcular_matriz_covarianza(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Estima la matriz de covarianza (17×17) de `X` (forma `(37, 17)`) y su
    inversa, aplicando el manejo obligatorio de estabilidad numérica descrito
    en el prompt maestro:

    1. Intentar invertir directamente.
    2. Si es singular o está mal condicionada (`cond > 1e10`), aplicar
       shrinkage (`cov + epsilon * I`) y reintentar.
    3. Si aún falla, usar la pseudo-inversa de Moore-Penrose como fallback.

    Devuelve `(cov_matrix, inv_cov_matrix)`. `cov_matrix` es la que realmente
    se usó para invertir (con o sin shrinkage aplicado), para trazabilidad.
    """
    cov_matrix = np.cov(X, rowvar=False)

    def _mal_condicionada(m: np.ndarray) -> bool:
        try:
            return np.linalg.cond(m) > CONDICION_MAXIMA_ACEPTABLE
        except np.linalg.LinAlgError:
            return True

    try:
        if _mal_condicionada(cov_matrix):
            raise np.linalg.LinAlgError("Matriz de covarianza mal condicionada")
        inv_cov_matrix = np.linalg.inv(cov_matrix)
        return cov_matrix, inv_cov_matrix
    except np.linalg.LinAlgError:
        pass

    cov_matrix_reg = cov_matrix + EPSILON_SHRINKAGE * np.eye(cov_matrix.shape[0])
    try:
        if _mal_condicionada(cov_matrix_reg):
            raise np.linalg.LinAlgError("Matriz regularizada aún mal condicionada")
        inv_cov_matrix = np.linalg.inv(cov_matrix_reg)
        return cov_matrix_reg, inv_cov_matrix
    except np.linalg.LinAlgError:
        pass

    # Último recurso: pseudo-inversa de Moore-Penrose (siempre existe).
    inv_cov_matrix = np.linalg.pinv(cov_matrix_reg)
    return cov_matrix_reg, inv_cov_matrix


def calcular_distancias(
    x_usuario: np.ndarray, X: np.ndarray, inv_cov_matrix: np.ndarray
) -> list[float]:
    """Devuelve un vector de distancias de Mahalanobis, una por fila de `X`."""
    return [float(mahalanobis(x_usuario, fila, inv_cov_matrix)) for fila in X]


def _distancias_a_afinidad(distancias: list[float]) -> list[float]:
    """Normaliza distancias a un % de afinidad relativo al propio ranking (0-100)."""
    d_min, d_max = min(distancias), max(distancias)
    if d_max == d_min:
        return [100.0 for _ in distancias]
    return [round(100 * (1 - (d - d_min) / (d_max - d_min)), 1) for d in distancias]


def _explicacion(carrera_nombre: str, fortalezas: list[str], areas_labels: dict[str, str]) -> str:
    if not fortalezas:
        return (
            f"Tu perfil muestra un buen equilibrio general de competencias, "
            f"compatible con {carrera_nombre}."
        )
    labels = [areas_labels.get(a, a) for a in fortalezas[:3]]
    if len(labels) == 1:
        texto_areas = labels[0]
    else:
        texto_areas = ", ".join(labels[:-1]) + f" y {labels[-1]}"
    return (
        f"Tu perfil muestra una fuerte afinidad en {texto_areas}, "
        f"competencias clave para {carrera_nombre}."
    )


def calcular_recomendacion(
    vector_usuario: dict[str, float],
    X: np.ndarray,
    carrera_ids: list[int],
    carrera_nombres: list[str],
    areas: list[str],
    inv_cov_matrix: np.ndarray,
    areas_labels: dict[str, str] | None = None,
    top_n: int = 5,
) -> list[ResultadoCarrera]:
    """
    Función pura central del motor de recomendación.

    Args:
        vector_usuario: dict {area_key: promedio 1.0-5.0}, con exactamente las
            17 claves de `areas` (mismo orden no requerido, se reordena aquí).
        X: matriz `(37, 17)` de perfiles de carreras, columnas en el orden de `areas`.
        carrera_ids: ids de BD de las 37 carreras, mismo orden que las filas de `X`.
        carrera_nombres: nombres de las 37 carreras, mismo orden que las filas de `X`.
        areas: las 17 claves de área, en el orden de las columnas de `X`.
        inv_cov_matrix: inversa (o pseudo-inversa) de la matriz de covarianza, cacheada.
        areas_labels: mapa opcional {area_key: label legible} para las explicaciones.
        top_n: cuántos resultados devolver (por defecto 5).

    Returns:
        Lista de `ResultadoCarrera`, ordenada de mayor a menor afinidad, longitud `top_n`.
    """
    areas_labels = areas_labels or {}
    x_usuario = np.array([vector_usuario[area] for area in areas], dtype=float)

    distancias = calcular_distancias(x_usuario, X, inv_cov_matrix)
    afinidades = _distancias_a_afinidad(distancias)

    orden = sorted(range(len(distancias)), key=lambda i: distancias[i])

    resultados: list[ResultadoCarrera] = []
    for i in orden[:top_n]:
        mu_c = X[i]
        fortalezas = sorted(
            (
                area
                for j, area in enumerate(areas)
                if x_usuario[j] >= mu_c[j] and x_usuario[j] >= 4
            ),
            key=lambda area: -x_usuario[areas.index(area)],
        )
        brechas = [
            (area, mu_c[j] - x_usuario[j])
            for j, area in enumerate(areas)
            if x_usuario[j] < mu_c[j]
        ]
        areas_por_mejorar = [
            area for area, _ in sorted(brechas, key=lambda t: -t[1])[:3]
        ]

        resultados.append(
            ResultadoCarrera(
                carrera_id=carrera_ids[i],
                nombre=carrera_nombres[i],
                distancia_mahalanobis=round(distancias[i], 3),
                afinidad_pct=afinidades[i],
                explicacion=_explicacion(carrera_nombres[i], fortalezas, areas_labels),
                fortalezas=fortalezas,
                areas_por_mejorar=areas_por_mejorar,
            )
        )
    return resultados
