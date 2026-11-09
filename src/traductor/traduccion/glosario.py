"""Postproceso es-MX: reemplaza vocabulario de España por el de México (research R-06).

Cada fila de ``glosario_es_mx.tsv`` es ``origen<TAB>reemplazo``; ``origen`` puede tener varias
palabras. Solo entran palabras con un solo sentido. Se reemplaza por palabra o frase completa,
primero las entradas más largas, sin distinguir mayúsculas al buscar y conservando la mayúscula
inicial del original. Aplicarlo dos veces da el mismo resultado.
"""

from __future__ import annotations

import re
from pathlib import Path

ARCHIVO = Path(__file__).resolve().parent.parent / "recursos" / "glosario_es_mx.tsv"


def _cargar(ruta: Path) -> dict[str, str]:
    pares: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.startswith("#"):
            continue
        partes = linea.split("\t")
        if len(partes) != 2 or not partes[0].strip() or not partes[1].strip():
            continue  # fila mal formada: se ignora
        pares[partes[0].strip().lower()] = partes[1].strip()
    return pares


class Glosario:
    def __init__(self, ruta: Path | None = None) -> None:
        self.pares = _cargar(ruta or ARCHIVO)
        origenes = sorted(self.pares, key=len, reverse=True)
        if origenes:
            alternativas = "|".join(re.escape(o) for o in origenes)
            self._patron = re.compile(rf"(?<!\w)(?:{alternativas})(?!\w)", re.IGNORECASE)
        else:
            self._patron = None

    def _reemplazo(self, coincidencia: re.Match) -> str:
        original = coincidencia.group(0)
        nuevo = self.pares[original.lower()]
        if original[:1].isupper():
            nuevo = nuevo[:1].upper() + nuevo[1:]
        return nuevo

    def aplicar(self, texto: str) -> str:
        if not self._patron:
            return texto
        return self._patron.sub(self._reemplazo, texto)
