"""Ajustes guardados: solo aviso_en_linea_aceptado (T057, research R-13)."""

import json
import os
from pathlib import Path

import pytest

from traductor.ajustes import Ajustes

pytestmark = pytest.mark.spec("RF-015a")


def _archivo() -> Path:
    return Path(os.environ["APPDATA"]) / "TraductorIngles" / "ajustes.json"


def test_sin_archivo_vale_false(appdata_temporal):
    assert Ajustes.cargar().aviso_en_linea_aceptado is False


def test_guardar_y_volver_a_cargar(appdata_temporal):
    ajustes = Ajustes.cargar()
    ajustes.aviso_en_linea_aceptado = True
    ajustes.guardar()
    assert Ajustes.cargar().aviso_en_linea_aceptado is True


@pytest.mark.parametrize("contenido", ["{no es json", "[1, 2]", '{"aviso_en_linea_aceptado": "sí"}'])
def test_archivo_danado_da_los_valores_por_defecto(appdata_temporal, contenido):
    _archivo().parent.mkdir(parents=True, exist_ok=True)
    _archivo().write_text(contenido, encoding="utf-8")
    assert Ajustes.cargar().aviso_en_linea_aceptado is False


def test_solo_guarda_una_llave(appdata_temporal):
    ajustes = Ajustes.cargar()
    ajustes.aviso_en_linea_aceptado = True
    ajustes.guardar()
    assert json.loads(_archivo().read_text(encoding="utf-8")) == {"aviso_en_linea_aceptado": True}
