"""Textos visibles copiados del contrato de interfaz (T014)."""

import re
from pathlib import Path

import pytest

from traductor import textos

pytestmark = pytest.mark.spec("RF-013", "RF-014")

CONTRATO = (Path(__file__).resolve().parents[2] / "specs" / "001-traductor-subtitulos-v0"
            / "contracts" / "interfaz-usuario.md").read_text(encoding="utf-8")


def test_estan_todos_los_mensajes():
    assert sorted(textos.MENSAJES) == [f"M-{i:02d}" for i in range(1, 10)]


@pytest.mark.parametrize("id_mensaje", sorted(textos.MENSAJES))
def test_mensaje_igual_al_contrato(id_mensaje):
    fila = re.search(rf"^\| {id_mensaje} \|.*\| \"(.+)\" \|$", CONTRATO, re.M)
    assert fila, f"{id_mensaje} no está en el contrato"
    assert textos.MENSAJES[id_mensaje] == fila.group(1)


@pytest.mark.parametrize("texto", [
    textos.UI01_ACTIVAR, textos.UI01_DESACTIVAR, textos.UI01_NOMBRE_ACTIVAR,
    textos.UI01_NOMBRE_DESACTIVAR, textos.UI02_DESACTIVADA, textos.UI02_PREPARANDO,
    textos.UI02_ACTIVA, textos.UI03_SIN_INTERNET, textos.UI03_EN_LINEA, textos.UI04_TEXTO,
    textos.UI04_NOMBRE_APAGADO, textos.UI04_NOMBRE_ENCENDIDO, textos.UI06_TEXTO,
    textos.UI06_NOMBRE, textos.INSTRUCCION_MOVER, textos.D01_SI, textos.D01_NO,
    textos.D02_EXPLICACION, textos.D02_NOMBRE_CLAVE, textos.D02_NOMBRE_REGION,
    textos.D02_GUARDAR, textos.D02_COMPROBANDO, textos.TOOLTIP_DESACTIVADA,
    textos.TOOLTIP_PREPARANDO, textos.TOOLTIP_ACTIVA, textos.MENU_ABRIR,
])
def test_cada_texto_de_interfaz_aparece_en_el_contrato(texto):
    assert texto in CONTRATO


@pytest.mark.parametrize("texto", textos.MENSAJES.values())
def test_mensajes_sin_codigos_tecnicos(texto):
    assert not re.search(r"\d", texto.replace("Ctrl+Alt+T", ""))
    for palabra in ("error", "exception", "code", "ratón"):
        assert palabra not in texto.lower()
    assert len(texto) <= 160


@pytest.mark.parametrize("control", sorted(textos.NOMBRES_ACCESIBLES))
def test_cada_control_tiene_nombre_accesible(control):
    assert textos.NOMBRES_ACCESIBLES[control].strip()
