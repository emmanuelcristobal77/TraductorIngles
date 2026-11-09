"""Cada RF y CA de la spec tiene al menos un test o una justificación manual (Principio IV, T011)."""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SPEC = RAIZ / "specs" / "001-traductor-subtitulos-v0" / "spec.md"
TESTS = RAIZ / "tests"
MANUALES = TESTS / "solo_manuales.toml"
PATRON = re.compile(r"\b(RF-\d{3}[a-z]?|CA-\d{3})\b")


def ids_de_la_spec() -> set[str]:
    return set(PATRON.findall(SPEC.read_text(encoding="utf-8")))


def _es_marca_spec(nodo: ast.AST) -> bool:
    # pytest.mark.spec(...)
    return (
        isinstance(nodo, ast.Attribute)
        and nodo.attr == "spec"
        and isinstance(nodo.value, ast.Attribute)
        and nodo.value.attr == "mark"
    )


def ids_de_los_tests() -> set[str]:
    encontrados: set[str] = set()
    for ruta in TESTS.rglob("*.py"):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call) and _es_marca_spec(nodo.func):
                for arg in nodo.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        encontrados.add(arg.value)
    return encontrados


def cargar_manuales() -> dict:
    with MANUALES.open("rb") as f:
        return tomllib.load(f)


def test_cada_identificador_de_la_spec_tiene_test_o_justificacion():
    faltantes = ids_de_la_spec() - ids_de_los_tests() - set(cargar_manuales())
    assert not faltantes, f"Sin test ni justificación manual: {sorted(faltantes)}"


def test_cada_entrada_manual_tiene_justificacion():
    sin_justificar = [k for k, v in cargar_manuales().items() if not v.get("justificacion")]
    assert not sin_justificar, f"Entradas sin justificacion: {sorted(sin_justificar)}"


def test_cada_entrada_manual_existe_en_la_spec():
    inexistentes = set(cargar_manuales()) - ids_de_la_spec()
    assert not inexistentes, f"No existen en la spec: {sorted(inexistentes)}"
