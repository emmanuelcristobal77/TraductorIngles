"""El instalador crea los accesos, no arranca solo y borra los datos al desinstalar (T074)."""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("RF-001", "RF-004", "RF-015a")

CARPETA = Path(__file__).resolve().parents[2] / "instalador"
ISS = (CARPETA / "traductor.iss").read_text(encoding="utf-8")
SPEC = (CARPETA / "traductor.spec").read_text(encoding="utf-8")


def seccion(nombre: str) -> str:
    m = re.search(rf"^\[{nombre}\]\s*$(.*?)(?=^\[|\Z)", ISS, re.M | re.S)
    return m.group(1) if m else ""


def sin_comentarios(texto: str) -> str:
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith((";", "#")))


@pytest.mark.parametrize("texto", [ISS, SPEC])
def test_no_lleva_datos_de_la_persona(texto):
    codigo = sin_comentarios(texto)
    for prohibido in ("cuenta_en_linea.bin", "ajustes.json", "Ocp-Apim-Subscription-Key",
                      "subscription"):
        assert prohibido not in codigo


def test_accesos_en_escritorio_y_menu_inicio():
    iconos = seccion("Icons")
    assert re.search(r'Name:\s*"\{autodesktop\}\\(\{#Nombre\}|TraductorIngles)"', iconos)
    assert re.search(r'Name:\s*"\{autoprograms\}\\(\{#Nombre\}|TraductorIngles)"', iconos)
    assert '#define Nombre "TraductorIngles"' in ISS


def test_sin_arranque_automatico():
    assert "CurrentVersion\\Run" not in seccion("Registry")
    assert "{autostartup}" not in ISS and "{userstartup}" not in ISS and "{commonstartup}" not in ISS


def test_borra_los_datos_al_desinstalar():
    borrar = seccion("UninstallDelete")
    assert "{userappdata}\\TraductorIngles" in borrar
    assert "{localappdata}\\TraductorIngles" in borrar


def test_textos_del_instalador_en_espanol():
    assert "Spanish.isl" in seccion("Languages")
