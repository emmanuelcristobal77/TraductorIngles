"""Zona de mensajes UI-05 y M-05 fijo (T021)."""

import pytest

from traductor import textos
from traductor.estado import ValorEstado
from traductor.motores.base import ErrorPreparacion

pytestmark = pytest.mark.spec("RF-013", "RF-005")


def _falla():
    raise ErrorPreparacion("modelos dañados")


def test_mensaje_se_vacia_a_los_10_s(qtbot, armar_app):
    app = armar_app()
    ventana = app.ventana
    ventana.mostrar_mensaje("M-04")
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-04"]
    assert ventana.etiqueta_mensaje.accessibleName() == textos.UI05_NOMBRE
    assert ventana.temporizador_mensaje.interval() == 10_000
    ventana.temporizador_mensaje.timeout.emit()  # reloj simulado: pasaron 10 s
    assert ventana.etiqueta_mensaje.text() == ""


def test_mensaje_se_vacia_al_cambiar_el_estado(qtbot, armar_app):
    app = armar_app()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.ventana.mostrar_mensaje("M-03")
    app.estado.activar()
    assert app.ventana.etiqueta_mensaje.text() == ""


def test_m05_queda_fijo_tras_una_falla_de_preparacion(qtbot, armar_app):
    app = armar_app(preparar=_falla, arrancar=False)
    app.estado.activar()
    assert app.estado.valor is ValorEstado.PREPARANDO
    app.arrancar()
    qtbot.waitUntil(lambda: app.estado.fallida, timeout=3000)
    ventana = app.ventana
    assert ventana.etiqueta_estado.text() == textos.UI02_DESACTIVADA
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-05"]
    ventana.temporizador_mensaje.timeout.emit()
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-05"]
    app.estado.activar()
    assert ventana.etiqueta_estado.text() == textos.UI02_DESACTIVADA
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-05"]


def test_otro_mensaje_con_m05_fijo_vuelve_a_m05(qtbot, armar_app):
    app = armar_app(preparar=_falla)
    qtbot.waitUntil(lambda: app.estado.fallida, timeout=3000)
    ventana = app.ventana
    ventana.mostrar_mensaje("M-08")
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-08"]  # RF-015c
    ventana.temporizador_mensaje.timeout.emit()
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-05"]
    ventana.mostrar_mensaje("M-09")
    ventana.actualizar_estado(app.estado)  # un cambio de estado también regresa a M-05
    assert ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-05"]


def test_mostrar_un_mensaje_no_quita_el_foco(qtbot, armar_app):
    from PySide6.QtWidgets import QLineEdit

    app = armar_app()
    otra = QLineEdit()
    qtbot.addWidget(otra)
    otra.show()
    otra.activateWindow()
    otra.setFocus()
    qtbot.waitUntil(otra.hasFocus, timeout=2000)
    app.ventana.mostrar_mensaje("M-04")
    qtbot.wait(50)
    assert otra.hasFocus()
