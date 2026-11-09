"""Ícono del área de notificación: aviso emergente, menú, aviso de M-05 y teclado (T022)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSystemTrayIcon

from traductor import textos
from traductor.estado import ValorEstado
from traductor.motores.base import ErrorPreparacion

pytestmark = pytest.mark.spec("RF-001", "RF-002", "RF-003", "RF-005", "RF-004a", "RF-014")


def _textos_menu(bandeja):
    return [a.text() for a in bandeja.menu.actions()]


def test_aviso_emergente_y_menu_siguen_el_estado(qtbot, armar_app):
    app = armar_app(bloquear_carga=True)
    bandeja = app.bandeja
    assert bandeja.toolTip() == textos.TOOLTIP_DESACTIVADA
    assert _textos_menu(bandeja) == [textos.MENU_ACTIVAR, textos.MENU_ABRIR, textos.MENU_SALIR]
    app.estado.activar()
    assert bandeja.toolTip() == textos.TOOLTIP_PREPARANDO
    assert _textos_menu(bandeja)[0] == textos.MENU_DESACTIVAR
    app.estado.modelos_listos()
    assert bandeja.toolTip() == textos.TOOLTIP_ACTIVA
    assert _textos_menu(bandeja)[0] == textos.MENU_DESACTIVAR


def test_opcion_1_en_preparando_desactiva(qtbot, armar_app):
    app = armar_app(bloquear_carga=True)
    app.estado.activar()
    app.bandeja.accion_alternar.trigger()
    assert app.estado.valor is ValorEstado.DESACTIVADA


def test_opcion_1_alterna(qtbot, armar_app):
    app = armar_app()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.bandeja.accion_alternar.trigger()
    assert app.estado.valor is ValorEstado.ACTIVA
    app.bandeja.accion_alternar.trigger()
    assert app.estado.valor is ValorEstado.DESACTIVADA


def test_m05_sale_como_aviso_del_icono_sin_activar_ventanas(qtbot, armar_app, monkeypatch):
    def falla():
        raise ErrorPreparacion("x")

    app = armar_app(preparar=falla, arrancar=False)
    avisos = []
    monkeypatch.setattr(app.bandeja, "showMessage", lambda *a, **k: avisos.append(a[:2]))
    app.ventana.show()
    app.ventana.showMinimized()
    app.estado.activar()
    app.arrancar()
    qtbot.waitUntil(lambda: app.estado.fallida, timeout=3000)
    esperado = (textos.AVISO_TITULO, textos.MENSAJES["M-05"])
    assert avisos == [esperado]
    app.bandeja.accion_alternar.trigger()
    app.atajo.presionado.emit()
    assert avisos == [esperado] * 3
    assert app.ventana.isMinimized()


def test_sin_falla_nunca_hay_aviso_del_icono(qtbot, armar_app, monkeypatch):
    app = armar_app(arrancar=False)
    avisos = []
    monkeypatch.setattr(app.bandeja, "showMessage", lambda *a, **k: avisos.append(a))
    app.arrancar()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.estado.alternar()
    app.estado.alternar()
    assert avisos == []


def test_clic_izquierdo_y_abrir_muestran_la_ventana(qtbot, armar_app):
    app = armar_app()
    app.ventana.hide()
    app.bandeja.activated.emit(QSystemTrayIcon.Trigger)
    assert app.ventana.isVisible()
    app.ventana.showMinimized()
    app.bandeja.accion_abrir.trigger()
    assert app.ventana.isVisible() and not app.ventana.isMinimized()


def test_salir_ejecuta_el_cierre(qtbot, armar_app):
    llamadas = []
    app = armar_app(salir=lambda: llamadas.append("quit"))
    app.bandeja.accion_salir.trigger()
    assert llamadas == ["quit"]


def test_con_teclado(qtbot, armar_app, monkeypatch):
    """Enter sobre el ícono = Trigger; tecla Menú o Mayús+F10 = Context (contrato §4)."""
    app = armar_app()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.ventana.hide()
    app.bandeja.activated.emit(QSystemTrayIcon.Trigger)
    assert app.ventana.isVisible()

    abiertos = []
    monkeypatch.setattr(app.bandeja.menu, "popup", lambda *a, **k: abiertos.append(True))
    app.bandeja.activated.emit(QSystemTrayIcon.Context)
    assert abiertos == [True]

    menu = app.bandeja.menu
    menu.show()
    menu.setActiveAction(menu.actions()[0])
    qtbot.keyClick(menu, Qt.Key_Return)
    assert app.estado.valor is ValorEstado.ACTIVA

    menu.show()
    menu.setActiveAction(menu.actions()[0])
    qtbot.keyClick(menu, Qt.Key_Down)
    assert menu.activeAction() is app.bandeja.accion_abrir
    app.ventana.hide()
    qtbot.keyClick(menu, Qt.Key_Return)
    assert app.ventana.isVisible()

    llamadas = []
    app.control.salir = lambda: llamadas.append("quit")
    menu.show()
    menu.setActiveAction(app.bandeja.accion_abrir)
    qtbot.keyClick(menu, Qt.Key_Down)
    assert menu.activeAction() is app.bandeja.accion_salir
    qtbot.keyClick(menu, Qt.Key_Return)
    assert llamadas == ["quit"]
