"""Franja de subtítulos (T037, contrato §2)."""

import time

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLineEdit

from traductor.ui.subtitulos import FranjaSubtitulos, Subtitulo, duracion_bloque

pytestmark = pytest.mark.spec("RF-008", "RF-009", "RF-012", "CA-004", "CA-006", "CA-016")


class Reloj:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


@pytest.fixture
def franja(qtbot):
    reloj = Reloj()
    f = FranjaSubtitulos(reloj=reloj, set_window_pos=lambda *a: 1)
    qtbot.addWidget(f)
    f.reloj_falso = reloj
    return f


def avanzar(franja, segundos, paso=0.05):
    inicio = franja.reloj_falso.t
    pasos = max(1, round(segundos / paso))
    for i in range(1, pasos + 1):
        franja.reloj_falso.t = inicio + segundos * i / pasos  # el último paso cae exacto en el final
        franja._tic()


def sub(texto, sesion=1):
    return Subtitulo(texto=texto, sesion=sesion, mostrado_en=0.0)


def test_banderas_y_no_quita_el_foco(qtbot, franja):
    flags = franja.windowFlags()
    assert flags & Qt.FramelessWindowHint and flags & Qt.WindowStaysOnTopHint and flags & Qt.Tool
    assert franja.testAttribute(Qt.WA_ShowWithoutActivating)
    otra = QLineEdit()
    qtbot.addWidget(otra)
    otra.show()
    otra.activateWindow()
    otra.setFocus()
    qtbot.waitUntil(otra.hasFocus, timeout=2000)
    franja.mostrar(sub("Hola"), 1)
    qtbot.wait(100)
    assert franja.isVisible() and otra.hasFocus()


def test_posicion_inicial(franja):
    pantalla = QGuiApplication.primaryScreen().geometry()
    franja.mostrar(sub("Hola"), 1)
    g = franja.frameGeometry()
    assert abs(g.center().x() - pantalla.center().x()) <= 2
    assert abs((pantalla.bottom() - g.bottom()) - 0.10 * pantalla.height()) <= 2


def test_estilo(franja):
    assert franja.etiqueta.font().pixelSize() == 28
    assert franja.COLOR_TEXTO == "#ffffff"
    assert franja.COLOR_FONDO.alpha() == round(0.75 * 255)


def test_maximo_dos_lineas_y_bloques(franja):
    texto = " ".join(["palabra"] * 120)
    franja.mostrar(sub(texto), 1)
    assert len(franja.bloques_totales) >= 2
    for bloque in franja.bloques_totales:
        assert franja.lineas_de(bloque) <= 2
    assert " ".join(franja.bloques_totales) == texto


def test_duracion_por_bloque():
    assert duracion_bloque("x" * 15) == 1.5
    assert duracion_bloque("x" * 45) == 3.0
    assert duracion_bloque("x" * 90) == 4.0


def test_bloques_uno_tras_otro_y_el_ultimo_se_queda(franja):
    franja.mostrar(sub(" ".join(["palabra"] * 120)), 1)
    bloques = list(franja.bloques_totales)
    assert franja.texto_visible() == bloques[0]
    for i, bloque in enumerate(bloques[1:], 1):
        avanzar(franja, duracion_bloque(bloques[i - 1]))
        assert franja.texto_visible() == bloque
    avanzar(franja, 3.9)
    assert franja.texto_visible() == bloques[-1]


def test_subtitulo_nuevo_descarta_bloques_pendientes(franja):
    franja.mostrar(sub(" ".join(["palabra"] * 120)), 1)
    franja.mostrar(sub("Nuevo"), 1)
    assert franja.texto_visible() == "Nuevo"
    avanzar(franja, 3.9)
    assert franja.texto_visible() == "Nuevo"


def test_se_vacia_4_s_sin_habla(franja):
    franja.mostrar(sub("Hola"), 1)
    avanzar(franja, 3.9)
    assert franja.isVisible()
    avanzar(franja, 0.2)
    assert not franja.isVisible() and franja.texto_visible() == ""


def test_voz_reinicia_los_4_s(franja):
    franja.mostrar(sub("Hola"), 1)
    avanzar(franja, 3.0)
    franja.marcar_voz()
    avanzar(franja, 3.9)
    assert franja.isVisible()
    avanzar(franja, 0.2)
    assert not franja.isVisible()


def test_tres_bloques_se_ven_todos_y_se_vacia_a_los_12_s(franja, monkeypatch):
    monkeypatch.setattr(franja, "dividir", lambda texto: ["a" * 60, "b" * 60, "c" * 10])
    franja.mostrar(sub("x"), 1)
    avanzar(franja, 4.0)
    assert franja.texto_visible() == "b" * 60
    avanzar(franja, 4.0)
    assert franja.texto_visible() == "c" * 10
    avanzar(franja, 3.9)
    assert franja.isVisible()
    avanzar(franja, 0.2)
    assert not franja.isVisible()


def test_ocultar_ya(franja):
    franja.mostrar(sub("Hola"), 1)
    inicio = time.monotonic()
    franja.ocultar_ya()
    assert not franja.isVisible() and time.monotonic() - inicio < 1.0


def test_otra_sesion_se_ignora(franja):
    franja.mostrar(sub("Viejo", sesion=1), 2)
    assert not franja.isVisible() and franja.texto_visible() == ""


def test_arrastre_con_mouse_sin_salir_de_la_pantalla(qtbot, franja):
    franja.mostrar(sub("Hola"), 1)
    inicio = franja.pos()
    qtbot.mousePress(franja, Qt.LeftButton, pos=QPoint(10, 10))
    qtbot.mouseMove(franja, QPoint(10, 10) + QPoint(-50, -80))
    qtbot.mouseRelease(franja, Qt.LeftButton, pos=QPoint(10, 10) + QPoint(-50, -80))
    assert franja.pos() != inicio
    franja.mover_a(QPoint(-10_000, -10_000))
    pantalla = franja.screen().geometry()
    assert pantalla.contains(franja.frameGeometry())
    franja.mover_a(QPoint(10_000, 10_000))
    assert pantalla.contains(franja.frameGeometry())


def test_refuerzo_de_siempre_encima(qtbot):
    llamadas = []
    f = FranjaSubtitulos(set_window_pos=lambda *a: llamadas.append(a) or 1)
    qtbot.addWidget(f)
    assert f.temporizador_encima.interval() == 2000
    f.temporizador_encima.timeout.emit()
    hwnd, despues, x, y, cx, cy, banderas = llamadas[-1]
    assert despues == -1  # HWND_TOPMOST
    assert banderas & 0x0010  # SWP_NOACTIVATE
    assert banderas & 0x0001 and banderas & 0x0002  # SWP_NOSIZE | SWP_NOMOVE
