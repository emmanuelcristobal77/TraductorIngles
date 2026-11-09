"""Ventana principal: UI-01 y UI-02, foco, mouse y teclado, legibilidad (T020)."""

import pytest
from PySide6.QtCore import Qt

from traductor import textos
from traductor.estado import ValorEstado
from traductor.ui.ventana import COLORES, contraste

pytestmark = pytest.mark.spec("RF-002", "RF-003", "RF-005", "RF-014", "RF-016", "CA-003",
                              "CA-010", "CA-016")


def _esperar_listo(qtbot, app):
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)


def test_ui01_muestra_el_atajo_y_cambia_de_texto(qtbot, armar_app):
    app = armar_app()
    boton = app.ventana.boton_traduccion
    assert textos.UI01_ACTIVAR in boton.text() and textos.UI01_ATAJO in boton.text()
    assert boton.accessibleName() == textos.UI01_NOMBRE_ACTIVAR
    _esperar_listo(qtbot, app)
    app.estado.activar()
    assert textos.UI01_DESACTIVAR in boton.text() and textos.UI01_ATAJO in boton.text()
    assert boton.accessibleName() == textos.UI01_NOMBRE_DESACTIVAR


def test_ui01_dice_desactivar_tambien_en_preparando(qtbot, armar_app):
    app = armar_app(bloquear_carga=True)
    app.estado.activar()
    assert app.estado.valor is ValorEstado.PREPARANDO
    assert textos.UI01_DESACTIVAR in app.ventana.boton_traduccion.text()


def test_ui02_sigue_el_estado(qtbot, armar_app):
    app = armar_app(bloquear_carga=True)
    etiqueta = app.ventana.etiqueta_estado
    assert etiqueta.text() == textos.UI02_DESACTIVADA
    assert etiqueta.accessibleName() == textos.UI02_DESACTIVADA
    app.estado.activar()
    assert etiqueta.text() == textos.UI02_PREPARANDO
    app.estado.modelos_listos()
    assert etiqueta.text() == textos.UI02_ACTIVA
    assert etiqueta.accessibleName() == textos.UI02_ACTIVA


def test_activa_cambia_texto_y_color(qtbot, armar_app):
    app = armar_app()
    _esperar_listo(qtbot, app)
    antes = (app.ventana.boton_traduccion.styleSheet(), app.ventana.etiqueta_estado.styleSheet())
    app.estado.activar()
    despues = (app.ventana.boton_traduccion.styleSheet(), app.ventana.etiqueta_estado.styleSheet())
    assert antes[0] != despues[0] and antes[1] != despues[1]


def test_foco_inicial_y_enter_activa(qtbot, armar_app):
    app = armar_app()
    _esperar_listo(qtbot, app)
    app.ventana.activateWindow()
    qtbot.waitUntil(lambda: app.ventana.boton_traduccion.hasFocus(), timeout=2000)
    qtbot.keyClick(app.ventana.boton_traduccion, Qt.Key_Return)
    assert app.estado.valor is ValorEstado.ACTIVA


def test_solo_mouse(qtbot, armar_app):
    app = armar_app()
    _esperar_listo(qtbot, app)
    qtbot.mouseClick(app.ventana.boton_traduccion, Qt.LeftButton)
    assert app.estado.valor is ValorEstado.ACTIVA
    qtbot.mouseClick(app.ventana.boton_traduccion, Qt.LeftButton)
    assert app.estado.valor is ValorEstado.DESACTIVADA


@pytest.mark.parametrize("tecla", [Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter])
def test_solo_teclado(qtbot, armar_app, tecla):
    app = armar_app()
    _esperar_listo(qtbot, app)
    qtbot.keyClick(app.ventana.boton_traduccion, tecla)
    assert app.estado.valor is ValorEstado.ACTIVA
    qtbot.keyClick(app.ventana.boton_traduccion, tecla)
    assert app.estado.valor is ValorEstado.DESACTIVADA


def test_letra_y_contraste(qtbot, armar_app):
    app = armar_app()
    for widget in (app.ventana.boton_traduccion, app.ventana.etiqueta_estado,
                   app.ventana.etiqueta_mensaje):
        widget.ensurePolished()
        assert widget.font().pixelSize() >= 16
    for texto, fondo in COLORES.values():
        assert contraste(texto, fondo) >= 4.5


def test_responde_antes_de_cargar_los_modelos(qtbot, armar_app):
    app = armar_app(bloquear_carga=True)
    assert app.ventana.isVisible()
    qtbot.mouseClick(app.ventana.boton_traduccion, Qt.LeftButton)
    assert app.estado.valor is ValorEstado.PREPARANDO
