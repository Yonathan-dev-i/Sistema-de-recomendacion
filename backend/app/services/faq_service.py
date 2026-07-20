"""
Reconocimiento de intención por reglas (Fase 7) — banco de FAQs.

Este módulo implementa la funcionalidad #2 del catálogo de "Funcionalidades
Avanzadas del Chatbot": preguntas abiertas del usuario respondidas SIEMPRE
desde un banco de intenciones predefinido (`data/intents.json`), nunca por
generación de texto libre. El matching es por palabras clave/normalización de
texto (minúsculas, sin tildes, sin puntuación) y tolerancia a errores de
tipeo vía distancia de edición (Levenshtein) a nivel de palabra — nunca por
un modelo de lenguaje.

Si ningún intent coincide, el caller (`chatbot_service`) es responsable de
aplicar el fallback fijo correspondiente al estado actual de la conversación;
este módulo solo se limita a devolver `None` en ese caso.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Tolerancia máxima de edición (Levenshtein) para considerar dos palabras
# "iguales" pese a un error de tipeo (ej. "cuanro" ~ "cuanto").
_TOLERANCIA_EDICION = 1


class IntentFAQ(TypedDict):
    id: str
    patrones: list[str]
    respuesta: str


def normalizar_texto(texto: str) -> str:
    """minúsculas, sin tildes/diacríticos, sin puntuación, espacios colapsados."""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    fila_anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        fila_actual = [i]
        for j, cb in enumerate(b, start=1):
            costo = 0 if ca == cb else 1
            fila_actual.append(
                min(
                    fila_anterior[j] + 1,  # borrado
                    fila_actual[j - 1] + 1,  # inserción
                    fila_anterior[j - 1] + costo,  # sustitución
                )
            )
        fila_anterior = fila_actual
    return fila_anterior[-1]


def _patron_coincide(patron_norm: str, texto_norm: str) -> bool:
    """
    Un patrón coincide si:
    1. Aparece como substring exacto en el texto normalizado, o
    2. Sus palabras aparecen en el mismo orden y de forma consecutiva en el
       texto, permitiendo que cada palabra individual difiera en hasta
       `_TOLERANCIA_EDICION` caracteres (Levenshtein), para tolerar errores
       de tipeo (ej. "cuanro dura" -> "cuanto dura").
    """
    if patron_norm in texto_norm:
        return True

    palabras_patron = patron_norm.split()
    palabras_texto = texto_norm.split()
    n = len(palabras_patron)
    if n == 0 or len(palabras_texto) < n:
        return False

    for inicio in range(len(palabras_texto) - n + 1):
        ventana = palabras_texto[inicio : inicio + n]
        if all(
            _levenshtein(pp, pt) <= _TOLERANCIA_EDICION
            for pp, pt in zip(palabras_patron, ventana, strict=True)
        ):
            return True
    return False


@lru_cache(maxsize=1)
def _cargar_intents() -> list[IntentFAQ]:
    with open(DATA_DIR / "intents.json", encoding="utf-8") as f:
        intents: list[IntentFAQ] = json.load(f)
    return intents


def buscar_intent_faq(texto_usuario: str) -> tuple[str, str] | None:
    """
    Busca, por reglas, si `texto_usuario` coincide con algún intent del banco
    de FAQs. Devuelve `(intent_id, respuesta)` o `None` si ninguno coincide.

    El primer intent cuyo patrón coincida gana (orden del archivo de datos);
    el archivo está pensado para tener patrones suficientemente específicos
    como para no solaparse entre intents distintos.
    """
    texto_norm = normalizar_texto(texto_usuario)
    if not texto_norm:
        return None

    for intent in _cargar_intents():
        for patron in intent["patrones"]:
            if _patron_coincide(normalizar_texto(patron), texto_norm):
                return intent["id"], intent["respuesta"]
    return None
