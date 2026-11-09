"""Atajo global Ctrl+Alt+T con RegisterHotKey simulado (T023)."""

import ctypes
import time
from ctypes import wintypes

import pytest

from traductor import textos
from traductor.estado import ValorEstado
from traductor.ui.atajo import ID_ATAJO, WM_HOTKEY

pytestmark = pytest.mark.spec("RF-016", "RF-016a", "CA-014")


def _hotkey(atajo, ident=ID_ATAJO):
    msg = wintypes.MSG()
    msg.message = WM_HOTKEY
    msg.wParam = ident
    return atajo.filtro.nativeEventFilter(b"windows_generic_MSG", ctypes.addressof(msg))


def test_se_registra_con_ctrl_alt_t_sin_repeticion(qtbot, armar_app):
    app = armar_app()
    (_, ident, mods, vk), = app.atajo.user32.registros
    assert ident == ID_ATAJO
    assert mods == 0x0001 | 0x0002 | 0x4000
    assert vk == 0x54


def test_wm_hotkey_alterna_sin_activar_la_ventana(qtbot, armar_app):
    app = armar_app()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.ventana.showMinimized()
    inicio = time.monotonic()
    _hotkey(app.atajo)
    assert app.estado.valor is ValorEstado.ACTIVA
    _hotkey(app.atajo)
    assert app.estado.valor is ValorEstado.DESACTIVADA
    assert time.monotonic() - inicio < 1.0
    assert app.ventana.isMinimized()


def test_otro_id_no_hace_nada(qtbot, armar_app):
    app = armar_app()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    _hotkey(app.atajo, ident=ID_ATAJO + 1)
    assert app.estado.valor is ValorEstado.DESACTIVADA


def test_atajo_ocupado_muestra_m06_y_lo_demas_sigue(qtbot, armar_app):
    app = armar_app(ocupado=True)
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    assert app.ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-06"]
    app.ventana.boton_traduccion.click()
    assert app.estado.valor is ValorEstado.ACTIVA
    app.bandeja.accion_alternar.trigger()
    assert app.estado.valor is ValorEstado.DESACTIVADA


def test_liberar_se_puede_llamar_dos_veces(qtbot, armar_app):
    app = armar_app()
    app.atajo.liberar()
    app.atajo.liberar()
    assert len(app.atajo.user32.liberaciones) == 1
