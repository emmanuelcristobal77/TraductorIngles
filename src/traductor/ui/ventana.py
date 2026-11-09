"""Ventana principal (contrato §1): UI-01, UI-02 y UI-05; cerrar y minimizar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from traductor import textos
from traductor.estado import EstadoTraduccion, ValorEstado

RECURSOS = Path(__file__).resolve().parent.parent / "recursos"
DURACION_MENSAJE_MS = 10_000

# (texto, fondo) por elemento y estado. Todos con contraste de 4.5:1 o más (Principio VI).
COLORES = {
    "boton_desactivada": ("#ffffff", "#1f4e79"),
    "boton_activa": ("#ffffff", "#9b1c1c"),
    "estado_desactivada": ("#1a1a1a", "#ffffff"),
    "estado_preparando": ("#7a4a00", "#ffffff"),
    "estado_activa": ("#0b5d1e", "#ffffff"),
    "mensaje": ("#1a1a1a", "#ffffff"),
    "modo_sin_internet": ("#1a1a1a", "#ffffff"),
    "modo_en_linea": ("#ffffff", "#8a3b00"),
    "secundario": ("#1a1a1a", "#e8e8e8"),
}


def _luminancia(color: str) -> float:
    canales = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineal = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]


def contraste(texto: str, fondo: str) -> float:
    """Relación de contraste WCAG entre dos colores ``#rrggbb``."""
    claro, oscuro = sorted((_luminancia(texto), _luminancia(fondo)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def estilo(clave: str, extra: str = "") -> str:
    texto, fondo = COLORES[clave]
    return f"color: {texto}; background-color: {fondo}; font-size: 16px; {extra}"


def estilo_boton(clave: str) -> str:
    """Botón con un borde de foco visible para quien usa el teclado (Principio VI)."""
    texto, fondo = COLORES[clave]
    return (f"QPushButton {{ color: {texto}; background-color: {fondo}; font-size: 16px; "
            f"font-weight: bold; padding: 8px 16px; border-radius: 6px; "
            f"border: 3px solid {fondo}; }} "
            f"QPushButton:focus {{ border: 3px solid {COLOR_FOCO}; }}")


COLOR_FOCO = "#000000"


class BotonConEnter(QPushButton):
    """QPushButton que también se activa con Enter fuera de un QDialog (contrato §1)."""

    def keyPressEvent(self, evento: QKeyEvent) -> None:  # noqa: N802
        if evento.key() in (Qt.Key_Return, Qt.Key_Enter) and not evento.isAutoRepeat():
            self.click()
            return
        super().keyPressEvent(evento)


class VentanaPrincipal(QWidget):
    alternar_solicitado = Signal()
    cerrar_solicitado = Signal()
    mover_solicitado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(textos.NOMBRE_APP)
        self.setWindowIcon(QIcon(str(RECURSOS / "icono.ico")))
        self.setStyleSheet("background-color: #ffffff; font-size: 16px;")

        self.boton_traduccion = BotonConEnter()  # UI-01
        self.boton_traduccion.setMinimumHeight(48)
        self.boton_traduccion.clicked.connect(self.alternar_solicitado)

        self.etiqueta_estado = QLabel()  # UI-02
        self.etiqueta_estado.setTextInteractionFlags(Qt.NoTextInteraction)

        self.etiqueta_mensaje = QLabel()  # UI-05
        self.etiqueta_mensaje.setWordWrap(True)
        self.etiqueta_mensaje.setAccessibleName(textos.UI05_NOMBRE)
        self.etiqueta_mensaje.setStyleSheet(estilo("mensaje"))

        self.temporizador_mensaje = QTimer(self)
        self.temporizador_mensaje.setSingleShot(True)
        self.temporizador_mensaje.setInterval(DURACION_MENSAJE_MS)
        self.temporizador_mensaje.timeout.connect(self._fin_mensaje_temporal)
        self._m05_fijo = False

        self.boton_mover = BotonConEnter(textos.UI06_TEXTO)  # UI-06 (RF-009)
        self.boton_mover.setAccessibleName(textos.UI06_NOMBRE)
        self.boton_mover.setStyleSheet(estilo_boton("secundario"))
        self.boton_mover.clicked.connect(self.mover_solicitado)

        self.disposicion = QVBoxLayout(self)
        self.disposicion.addWidget(self.boton_traduccion)
        self.disposicion.addWidget(self.etiqueta_estado)
        self.disposicion.addWidget(self.etiqueta_mensaje)
        self.disposicion.addWidget(self.boton_mover)
        self.setMinimumWidth(420)
        QWidget.setTabOrder(self.boton_traduccion, self.boton_mover)

        self._pintar(ValorEstado.DESACTIVADA)
        self.boton_traduccion.setFocus()  # foco inicial en UI-01 (CA-003)

    # --- estado ---------------------------------------------------------------------------
    def actualizar_estado(self, estado: EstadoTraduccion) -> None:
        self._pintar(estado.valor)
        self._fin_mensaje_temporal()  # los mensajes temporales se borran al cambiar el estado

    def _pintar(self, valor: ValorEstado) -> None:
        desactivada = valor is ValorEstado.DESACTIVADA
        texto = textos.UI01_ACTIVAR if desactivada else textos.UI01_DESACTIVAR
        self.boton_traduccion.setText(f"{texto}  ·  {textos.UI01_ATAJO}")
        self.boton_traduccion.setAccessibleName(
            textos.UI01_NOMBRE_ACTIVAR if desactivada else textos.UI01_NOMBRE_DESACTIVAR)
        self.boton_traduccion.setStyleSheet(
            estilo_boton("boton_desactivada" if desactivada else "boton_activa"))

        texto_estado, clave = {
            ValorEstado.DESACTIVADA: (textos.UI02_DESACTIVADA, "estado_desactivada"),
            ValorEstado.PREPARANDO: (textos.UI02_PREPARANDO, "estado_preparando"),
            ValorEstado.ACTIVA: (textos.UI02_ACTIVA, "estado_activa"),
        }[valor]
        self.etiqueta_estado.setText(texto_estado)
        self.etiqueta_estado.setAccessibleName(texto_estado)
        self.etiqueta_estado.setStyleSheet(estilo(clave, "font-weight: bold;"))

    # --- mensajes (contrato §6) -----------------------------------------------------------
    def mostrar_mensaje(self, id_mensaje: str) -> None:
        self.etiqueta_mensaje.setText(textos.MENSAJES[id_mensaje])
        if id_mensaje == "M-05":
            self._m05_fijo = True
            self.temporizador_mensaje.stop()
        else:
            self.temporizador_mensaje.start()

    def _fin_mensaje_temporal(self) -> None:
        self.temporizador_mensaje.stop()
        self.etiqueta_mensaje.setText(textos.MENSAJES["M-05"] if self._m05_fijo else "")

    # --- ventana --------------------------------------------------------------------------
    def enfocar_mover(self) -> None:
        """Al terminar el modo de mover, el foco vuelve a UI-06 (contrato §2.1)."""
        self.activateWindow()
        self.boton_mover.setFocus(Qt.OtherFocusReason)

    def mostrar_y_traer(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, evento) -> None:  # noqa: N802 - cerrar la ventana cierra la app (RF-004a)
        evento.accept()
        self.cerrar_solicitado.emit()
