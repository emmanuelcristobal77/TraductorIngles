"""Bitácora de errores sin contenido (T014a).

La marca RF-013 es la más cercana: este test cubre el supuesto de la spec sobre la bitácora de
diagnóstico ("solo la hora y el tipo de cada error, nunca audio, texto ni la clave"), que no
tiene identificador propio (research R-13).
"""

import os
from pathlib import Path

import pytest

from traductor import bitacora

pytestmark = pytest.mark.spec("RF-013")


def _log() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "TraductorIngles" / "errores.log"


def test_solo_guarda_hora_componente_y_tipo(appdata_temporal):
    bitacora.registrar_error("captura", ValueError("hola secreto clave-123"))
    contenido = _log().read_text(encoding="utf-8")
    assert "captura" in contenido
    assert "ValueError" in contenido
    for prohibido in ("hola", "secreto", "clave-123"):
        assert prohibido not in contenido
    assert len(contenido.strip().splitlines()) == 1


def test_crea_la_carpeta_si_no_existe(appdata_temporal):
    assert not _log().parent.exists()
    bitacora.registrar_error("motor", RuntimeError("x"))
    assert _log().exists()


def test_si_escribir_falla_no_lanza_nada(appdata_temporal, monkeypatch):
    def falla(*args, **kwargs):
        raise OSError("disco lleno")

    monkeypatch.setattr("builtins.open", falla)
    monkeypatch.setattr(Path, "open", falla)
    bitacora.registrar_error("captura", ValueError("x"))
