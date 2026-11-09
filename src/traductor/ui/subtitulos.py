"""Franja de subtítulos siempre encima (contrato §2) y su modo de mover (§2.1)."""

from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QKeyEvent, QPainter
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from traductor import textos

SIN_HABLA_S = 4.0
PASO_CORTO = 20
PASO_LARGO = 100
HWND_TOPMOST = -1
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010


@dataclass
class Subtitulo:
    texto: str  # español de México, ya con el glosario; no vacío
    sesion: int
    mostrado_en: float


def duracion_bloque(bloque: str) -> float:
    """1 s por cada 15 caracteres, entre 1.5 y 4 s (contrato §2, "Texto largo")."""
    return min(4.0, max(1.5, len(bloque) / 15))


def _set_window_pos_real(hwnd, despues, x, y, cx, cy, banderas):
    return ctypes.windll.user32.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(despues),
                                             x, y, cx, cy, banderas)


class FranjaSubtitulos(QWidget):
    modo_mover_terminado = Signal()

    COLOR_TEXTO = "#ffffff"
    COLOR_FONDO = QColor(0, 0, 0, round(0.75 * 255))
    COLOR_RESALTE = "#ffd400"

    def __init__(self, reloj: Callable[[], float] = time.monotonic,
                 set_window_pos: Callable[..., int] | None = None) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.NoFocus)
        self._reloj = reloj
        self._set_window_pos = set_window_pos or _set_window_pos_real
        self.modo_mover = False

        self.marco = QFrame(self)
        self.etiqueta = QLabel(self.marco)
        fuente = QFont(self.etiqueta.font())
        fuente.setPixelSize(28)
        self.etiqueta.setFont(fuente)
        self.etiqueta.setWordWrap(True)
        self.etiqueta.setAlignment(Qt.AlignCenter)
        self.etiqueta.setStyleSheet(f"color: {self.COLOR_TEXTO}; background: transparent;")
        self.instruccion = QLabel(textos.INSTRUCCION_MOVER, self.marco)
        self.instruccion.setAlignment(Qt.AlignCenter)
        self.instruccion.setStyleSheet(
            f"color: {self.COLOR_RESALTE}; background: transparent; font-size: 18px;")
        self.instruccion.hide()
        capa = QVBoxLayout(self.marco)
        capa.setContentsMargins(20, 10, 20, 10)
        capa.addWidget(self.etiqueta)
        capa.addWidget(self.instruccion)
        externa = QVBoxLayout(self)
        externa.setContentsMargins(0, 0, 0, 0)
        externa.addWidget(self.marco)
        self._pintar_marco()

        pantalla = QGuiApplication.primaryScreen().geometry()
        self.ancho_texto = int(min(1100, pantalla.width() * 0.8))
        alto = QFontMetrics(fuente).lineSpacing() * 2 + 20 + 20
        self.setFixedSize(self.ancho_texto + 40, alto + 34)
        self._posicion_inicial(pantalla)

        self.bloques_totales: list[str] = []
        self._pendientes: list[str] = []
        self._t_siguiente_bloque: float | None = None
        self._t_vaciar: float | None = None
        self._vigente = False
        self._arrastre: QPoint | None = None

        self.temporizador = QTimer(self)
        self.temporizador.setInterval(50)
        self.temporizador.timeout.connect(self._tic)
        self.temporizador_encima = QTimer(self)
        self.temporizador_encima.setInterval(2000)
        self.temporizador_encima.timeout.connect(self._reforzar_encima)
        self.temporizador_encima.start()

    # --- apariencia -----------------------------------------------------------------------
    def _pintar_marco(self) -> None:
        borde = f"border: 3px solid {self.COLOR_RESALTE};" if self.modo_mover else "border: none;"
        self.marco.setStyleSheet(f"QFrame {{ background: transparent; {borde} border-radius: 10px; }}")

    def paintEvent(self, evento) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(self.COLOR_FONDO)
        p.drawRoundedRect(self.rect(), 10, 10)

    def _posicion_inicial(self, pantalla: QRect) -> None:
        x = pantalla.center().x() - self.width() // 2
        y = pantalla.bottom() - int(0.10 * pantalla.height()) - self.height() + 1
        self.move(x, y)

    def _reforzar_encima(self) -> None:
        if self.isVisible() or self._set_window_pos is not _set_window_pos_real:
            self._set_window_pos(int(self.winId()), HWND_TOPMOST, 0, 0, 0, 0,
                                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    # --- texto ----------------------------------------------------------------------------
    def lineas_de(self, texto: str) -> int:
        metricas = QFontMetrics(self.etiqueta.font())
        rect = metricas.boundingRect(QRect(0, 0, self.ancho_texto, 10_000), Qt.TextWordWrap, texto)
        return max(1, round(rect.height() / metricas.lineSpacing()))

    def dividir(self, texto: str) -> list[str]:
        """Bloques de hasta 2 líneas al ancho de la franja, cortando entre palabras."""
        bloques, actual = [], []
        for palabra in texto.split():
            prueba = " ".join(actual + [palabra])
            if actual and self.lineas_de(prueba) > 2:
                bloques.append(" ".join(actual))
                actual = [palabra]
            else:
                actual.append(palabra)
        if actual:
            bloques.append(" ".join(actual))
        return bloques

    def texto_visible(self) -> str:
        return self.etiqueta.text()

    def mostrar(self, subtitulo: Subtitulo, sesion_actual: int) -> None:
        if subtitulo.sesion != sesion_actual or not subtitulo.texto.strip():
            return
        ahora = self._reloj()
        subtitulo.mostrado_en = ahora
        self.bloques_totales = self.dividir(subtitulo.texto)
        self._pendientes = list(self.bloques_totales)
        self._vigente = True
        self._siguiente_bloque(ahora)
        self.show()
        self.temporizador.start()

    def _siguiente_bloque(self, ahora: float) -> None:
        bloque = self._pendientes.pop(0)
        self.etiqueta.setText(bloque)
        if self._pendientes:
            self._t_siguiente_bloque = ahora + duracion_bloque(bloque)
            self._t_vaciar = None  # mientras falten bloques, la franja no se vacía
        else:
            self._t_siguiente_bloque = None
            self._t_vaciar = ahora + SIN_HABLA_S

    def marcar_voz(self) -> None:
        if self._vigente and not self._pendientes:
            self._t_vaciar = self._reloj() + SIN_HABLA_S

    def _tic(self) -> None:
        ahora = self._reloj()
        if self._pendientes and self._t_siguiente_bloque is not None and ahora >= self._t_siguiente_bloque:
            self._siguiente_bloque(ahora)
        if self._t_vaciar is not None and ahora >= self._t_vaciar:
            self._vaciar()

    def _vaciar(self) -> None:
        self._vigente = False
        self._pendientes = []
        self._t_vaciar = self._t_siguiente_bloque = None
        self.etiqueta.setText("")
        self.temporizador.stop()
        if not self.modo_mover:
            self.hide()

    def ocultar_ya(self) -> None:
        self._vaciar()

    # --- mover ----------------------------------------------------------------------------
    def mover_a(self, punto: QPoint) -> None:
        """Mueve la franja sin que salga de la pantalla en la que está."""
        pantalla = (self.screen() or QGuiApplication.primaryScreen()).geometry()
        x = min(max(punto.x(), pantalla.left()), pantalla.right() - self.width() + 1)
        y = min(max(punto.y(), pantalla.top()), pantalla.bottom() - self.height() + 1)
        self.move(x, y)

    def mousePressEvent(self, evento) -> None:  # noqa: N802
        if evento.button() == Qt.LeftButton:
            self._arrastre = evento.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, evento) -> None:  # noqa: N802
        if self._arrastre is not None and evento.buttons() & Qt.LeftButton:
            self.mover_a(evento.globalPosition().toPoint() - self._arrastre)

    def mouseReleaseEvent(self, evento) -> None:  # noqa: N802
        self._arrastre = None

    def entrar_modo_mover(self) -> None:
        self.modo_mover = True
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.instruccion.show()
        self._pintar_marco()
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.OtherFocusReason)

    def terminar_modo_mover(self) -> None:
        if not self.modo_mover:
            return
        self.modo_mover = False
        self.instruccion.hide()
        self._pintar_marco()
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        if not self._vigente:
            self.hide()
        self.modo_mover_terminado.emit()

    def keyPressEvent(self, evento: QKeyEvent) -> None:  # noqa: N802
        if not self.modo_mover:
            return super().keyPressEvent(evento)
        paso = PASO_LARGO if evento.modifiers() & Qt.ShiftModifier else PASO_CORTO
        desplazamientos = {Qt.Key_Left: QPoint(-paso, 0), Qt.Key_Right: QPoint(paso, 0),
                           Qt.Key_Up: QPoint(0, -paso), Qt.Key_Down: QPoint(0, paso)}
        if evento.key() in desplazamientos:
            self.mover_a(self.pos() + desplazamientos[evento.key()])
        elif evento.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
            self.terminar_modo_mover()
        else:
            super().keyPressEvent(evento)

    def focusOutEvent(self, evento) -> None:  # noqa: N802
        super().focusOutEvent(evento)
        if self.modo_mover:
            self.terminar_modo_mover()
