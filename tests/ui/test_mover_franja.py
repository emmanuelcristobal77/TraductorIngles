"""Mover la franja con UI-06 y el teclado, o con el mouse (T038, contrato §2.1)."""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication

from traductor import textos
from traductor.ui.subtitulos import Subtitulo

pytestmark = pytest.mark.spec("RF-009", "RF-014", "CA-010", "CA-016")


@pytest.fixture
def app(armar_app, qtbot):
    aplicacion = armar_app()
    qtbot.addWidget(aplicacion.franja)
    aplicacion.ventana.activateWindow()
    return aplicacion


def orden_tab(ventana):
    vistos, w = [], ventana.boton_traduccion
    for _ in range(10):
        vistos.append(w)
        w = w.nextInFocusChain()
        while not (w.focusPolicy() & Qt.TabFocus) and w is not ventana.boton_traduccion:
            w = w.nextInFocusChain()
        if w is ventana.boton_traduccion:
            break
    return vistos


def test_ui06_texto_nombre_y_es_el_ultimo_del_tab(app):
    boton = app.ventana.boton_mover
    assert boton.text() == textos.UI06_TEXTO
    assert boton.accessibleName() == textos.UI06_NOMBRE
    orden = orden_tab(app.ventana)
    assert orden[0] is app.ventana.boton_traduccion and orden[-1] is boton


@pytest.mark.parametrize("como", ["clic", "enter"])
def test_entrar_al_modo_de_mover(qtbot, app, como):
    boton = app.ventana.boton_mover
    if como == "clic":
        qtbot.mouseClick(boton, Qt.LeftButton)
    else:
        qtbot.keyClick(boton, Qt.Key_Return)
    franja = app.franja
    assert franja.modo_mover and franja.isVisible()
    qtbot.waitUntil(franja.hasFocus, timeout=2000)
    assert franja.instruccion.text() == textos.INSTRUCCION_MOVER and franja.instruccion.isVisible()
    assert "3px solid #ffd400" in franja.marco.styleSheet()


def _entrar(qtbot, app):
    app.ventana.boton_mover.click()
    qtbot.waitUntil(app.franja.hasFocus, timeout=2000)
    franja = app.franja
    franja.mover_a(franja.screen().geometry().center() - QPoint(franja.width() // 2, 0))
    return franja


@pytest.mark.parametrize("tecla, dx, dy", [
    (Qt.Key_Left, -1, 0), (Qt.Key_Right, 1, 0), (Qt.Key_Up, 0, -1), (Qt.Key_Down, 0, 1),
])
def test_flechas_20_px_y_mayus_100_px(qtbot, app, tecla, dx, dy):
    franja = _entrar(qtbot, app)
    antes = franja.pos()
    qtbot.keyClick(franja, tecla)
    assert franja.pos() - antes == QPoint(20 * dx, 20 * dy)
    antes = franja.pos()
    qtbot.keyClick(franja, tecla, Qt.ShiftModifier)
    assert franja.pos() - antes == QPoint(100 * dx, 100 * dy)


@pytest.mark.parametrize("tecla", [Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down])
@pytest.mark.parametrize("mayus", [False, True])
def test_no_sale_de_la_pantalla_con_flechas(qtbot, app, tecla, mayus):
    franja = _entrar(qtbot, app)
    for _ in range(200):
        qtbot.keyClick(franja, tecla, Qt.ShiftModifier if mayus else Qt.NoModifier)
    assert franja.screen().geometry().contains(franja.frameGeometry())


@pytest.mark.parametrize("tecla", [Qt.Key_Return, Qt.Key_Escape])
def test_terminar_con_enter_o_esc(qtbot, app, tecla):
    franja = _entrar(qtbot, app)
    qtbot.keyClick(franja, tecla)
    assert not franja.modo_mover
    assert "3px solid #ffd400" not in franja.marco.styleSheet()
    assert franja.focusPolicy() == Qt.NoFocus
    qtbot.waitUntil(app.ventana.boton_mover.hasFocus, timeout=2000)
    assert not franja.isVisible()  # no había subtítulo vigente


def test_al_terminar_con_subtitulo_vigente_se_queda(qtbot, app):
    app.estado.modelos_listos()
    app.estado.activar()
    franja = _entrar(qtbot, app)
    franja.mostrar(Subtitulo("Hola", app.estado.sesion, 0.0), app.estado.sesion)
    qtbot.keyClick(franja, Qt.Key_Escape)
    assert franja.isVisible() and franja.texto_visible() == "Hola"


def test_perder_el_foco_termina_el_modo(qtbot, app):
    franja = _entrar(qtbot, app)
    app.ventana.activateWindow()
    qtbot.waitUntil(lambda: not franja.modo_mover, timeout=2000)
    assert not franja.isVisible()


def test_durante_el_modo_se_puede_arrastrar(qtbot, app):
    franja = _entrar(qtbot, app)
    antes = franja.pos()
    qtbot.mousePress(franja, Qt.LeftButton, pos=QPoint(10, 10))
    qtbot.mouseMove(franja, QPoint(60, 10))
    qtbot.mouseRelease(franja, Qt.LeftButton, pos=QPoint(60, 10))
    assert franja.pos() != antes and franja.modo_mover


def test_la_posicion_no_se_guarda(qtbot, app, appdata_temporal):
    franja = _entrar(qtbot, app)
    qtbot.keyClick(franja, Qt.Key_Left)
    qtbot.keyClick(franja, Qt.Key_Return)
    archivos = [p for p in appdata_temporal.rglob("*") if p.is_file()]
    assert archivos == []
