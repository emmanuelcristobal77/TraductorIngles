"""La franja queda encima de una ventana a pantalla completa sin quitarle el foco (T053)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from traductor.ui.subtitulos import (HWND_TOPMOST, SWP_NOACTIVATE, FranjaSubtitulos, Subtitulo)

pytestmark = pytest.mark.spec("CA-006", "RF-008")


def test_no_quita_el_foco_a_una_ventana_a_pantalla_completa(qtbot):
    video = QLineEdit()
    video.setWindowFlags(Qt.FramelessWindowHint)
    qtbot.addWidget(video)
    video.showFullScreen()
    video.activateWindow()
    video.setFocus()
    qtbot.waitUntil(video.hasFocus, timeout=2000)

    llamadas = []
    franja = FranjaSubtitulos(set_window_pos=lambda *a: llamadas.append(a) or 1)
    qtbot.addWidget(franja)
    franja.mostrar(Subtitulo("Hola", 1, 0.0), 1)
    qtbot.wait(100)
    assert franja.isVisible() and video.hasFocus() and video.isActiveWindow()

    franja.temporizador_encima.timeout.emit()  # refuerzo de cada 2 s
    _, despues, *_, banderas = llamadas[-1]
    assert despues == HWND_TOPMOST and banderas & SWP_NOACTIVATE
    assert video.hasFocus()


def test_refuerzo_real_no_activa_la_franja(qtbot):
    """Con SetWindowPos real: la franja queda arriba sin volverse la ventana activa."""
    video = QLineEdit()
    qtbot.addWidget(video)
    video.show()
    video.activateWindow()
    video.setFocus()
    qtbot.waitUntil(video.hasFocus, timeout=2000)
    franja = FranjaSubtitulos()
    qtbot.addWidget(franja)
    franja.mostrar(Subtitulo("Hola", 1, 0.0), 1)
    franja.temporizador_encima.timeout.emit()
    qtbot.wait(100)
    assert not franja.isActiveWindow() and video.hasFocus()
