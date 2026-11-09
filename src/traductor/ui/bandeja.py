"""Ícono del área de notificación y su menú (contrato §4)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from traductor import textos
from traductor.estado import EstadoTraduccion, ValorEstado

RECURSOS = Path(__file__).resolve().parent.parent / "recursos"


class Bandeja(QSystemTrayIcon):
    alternar_solicitado = Signal()
    abrir_solicitado = Signal()
    salir_solicitado = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(QIcon(str(RECURSOS / "icono.ico")), parent)
        self.menu = QMenu()
        self.accion_alternar = self.menu.addAction(textos.MENU_ACTIVAR)
        self.accion_abrir = self.menu.addAction(textos.MENU_ABRIR)
        self.accion_salir = self.menu.addAction(textos.MENU_SALIR)
        self.accion_alternar.triggered.connect(self.alternar_solicitado)
        self.accion_abrir.triggered.connect(self.abrir_solicitado)
        self.accion_salir.triggered.connect(self.salir_solicitado)
        # El menú se abre aquí (clic derecho, tecla Menú o Mayús+F10) y no con setContextMenu,
        # para que el mouse y el teclado sigan el mismo camino.
        self.activated.connect(self._activado)
        self.messageClicked.connect(self.abrir_solicitado)
        self.setToolTip(textos.TOOLTIP_DESACTIVADA)

    def _activado(self, razon: QSystemTrayIcon.ActivationReason) -> None:
        if razon == QSystemTrayIcon.Trigger:
            self.abrir_solicitado.emit()
        elif razon == QSystemTrayIcon.Context:
            self.menu.popup(QCursor.pos())

    def actualizar_estado(self, estado: EstadoTraduccion) -> None:
        self.setToolTip({
            ValorEstado.DESACTIVADA: textos.TOOLTIP_DESACTIVADA,
            ValorEstado.PREPARANDO: textos.TOOLTIP_PREPARANDO,
            ValorEstado.ACTIVA: textos.TOOLTIP_ACTIVA,
        }[estado.valor])
        self.accion_alternar.setText(
            textos.MENU_ACTIVAR if estado.valor is ValorEstado.DESACTIVADA else textos.MENU_DESACTIVAR)

    def avisar(self, id_mensaje: str) -> None:
        """Aviso normal de Windows: no quita el foco y se cierra solo (contrato §4)."""
        self.showMessage(textos.AVISO_TITULO, textos.MENSAJES[id_mensaje])
