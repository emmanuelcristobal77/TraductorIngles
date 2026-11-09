"""Cuadros del modo en línea: D-01 aviso y D-02 cuenta (contrato §3)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout)

from traductor import cuenta as modulo_cuenta
from traductor import textos
from traductor.cuenta import CuentaEnLinea, ResultadoValidacion

REGIONES = Path(__file__).resolve().parent.parent / "recursos" / "regiones_azure.txt"
ESTILO = "font-size: 16px;"


class AvisoEnLinea(QMessageBox):
    """D-01: sale una vez por instalación. El foco empieza en "No"."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(textos.NOMBRE_APP)
        self.setIcon(QMessageBox.Warning)
        self.setText(textos.MENSAJES["M-01"])
        self.setStyleSheet(ESTILO)
        self.boton_si = self.addButton(textos.D01_SI, QMessageBox.YesRole)
        self.boton_no = self.addButton(textos.D01_NO, QMessageBox.NoRole)
        for boton in (self.boton_si, self.boton_no):
            boton.setAccessibleName(boton.text())
        self.setDefaultButton(self.boton_no)
        self.setEscapeButton(self.boton_no)

    def showEvent(self, evento) -> None:  # noqa: N802
        super().showEvent(evento)
        self.boton_no.setFocus(Qt.OtherFocusReason)

    def acepto(self) -> bool:
        return self.clickedButton() is self.boton_si

    def preguntar(self) -> bool:
        self.exec()
        return self.acepto()


class _Senales(QObject):
    terminado = Signal(object)


class _Validacion(QRunnable):
    def __init__(self, validar, cuenta, senales) -> None:
        super().__init__()
        self.validar, self.cuenta, self.senales = validar, cuenta, senales

    def run(self) -> None:
        try:
            resultado = self.validar(self.cuenta)
        except Exception:  # noqa: BLE001
            resultado = ResultadoValidacion.SIN_RED
        self.senales.terminado.emit(resultado)


class CuadroCuenta(QDialog):
    """D-02: pide la clave y la región y las valida sin congelar la ventana."""

    def __init__(self, parent=None,
                 validar: Callable[[CuentaEnLinea], ResultadoValidacion] = modulo_cuenta.validar) -> None:
        super().__init__(parent)
        self.setWindowTitle(textos.NOMBRE_APP)
        self.setStyleSheet(ESTILO)
        self._validar = validar
        self.resultado: ResultadoValidacion | None = None
        self.cuenta: CuentaEnLinea | None = None

        self.explicacion = QLabel(textos.D02_EXPLICACION)
        self.explicacion.setWordWrap(True)
        self.explicacion.setAccessibleName(textos.D02_EXPLICACION)
        self.clave = QLineEdit()
        self.clave.setEchoMode(QLineEdit.Password)  # nunca se muestra completa
        self.clave.setAccessibleName(textos.D02_NOMBRE_CLAVE)
        self.region = QComboBox()
        self.region.setEditable(True)
        self.region.setInsertPolicy(QComboBox.NoInsert)
        self.region.addItems([r.strip() for r in REGIONES.read_text(encoding="utf-8").splitlines()
                              if r.strip()])
        self.region.setAccessibleName(textos.D02_NOMBRE_REGION)
        self.boton_guardar = QPushButton(textos.D02_GUARDAR)
        self.boton_guardar.setAccessibleName(textos.D02_GUARDAR)
        self.boton_guardar.setDefault(True)
        self.boton_cancelar = QPushButton(textos.D02_CANCELAR)
        self.boton_cancelar.setAccessibleName(textos.D02_CANCELAR)

        formulario = QFormLayout()
        formulario.addRow(textos.D02_ETIQUETA_CLAVE, self.clave)
        formulario.addRow(textos.D02_ETIQUETA_REGION, self.region)
        botones = QHBoxLayout()
        botones.addStretch()
        botones.addWidget(self.boton_guardar)
        botones.addWidget(self.boton_cancelar)
        capa = QVBoxLayout(self)
        capa.addWidget(self.explicacion)
        capa.addLayout(formulario)
        capa.addLayout(botones)

        self.clave.textChanged.connect(self._actualizar_boton)
        self.region.editTextChanged.connect(self._actualizar_boton)
        self.clave.returnPressed.connect(self._guardar)
        self.region.lineEdit().returnPressed.connect(self._guardar)
        self.boton_guardar.clicked.connect(self._guardar)
        self.boton_cancelar.clicked.connect(self.reject)
        self._senales = _Senales()
        self._senales.terminado.connect(self._validado)
        self.region.setCurrentIndex(0)
        self._actualizar_boton()
        self.clave.setFocus()

    def _campos_llenos(self) -> bool:
        return bool(self.clave.text().strip() and self.region.currentText().strip())

    def _actualizar_boton(self) -> None:
        if self.boton_guardar.text() != textos.D02_COMPROBANDO:
            self.boton_guardar.setEnabled(self._campos_llenos())

    def _guardar(self) -> None:
        if not self._campos_llenos() or self.boton_guardar.text() == textos.D02_COMPROBANDO:
            return
        self.cuenta = CuentaEnLinea(self.clave.text(), self.region.currentText())
        self.boton_guardar.setText(textos.D02_COMPROBANDO)
        self.boton_guardar.setEnabled(False)
        QThreadPool.globalInstance().start(_Validacion(self._validar, self.cuenta, self._senales))

    def _validado(self, resultado: ResultadoValidacion) -> None:
        self.resultado = resultado
        self.boton_guardar.setText(textos.D02_GUARDAR)
        if resultado is ResultadoValidacion.VALIDA:
            self.accept()
        else:
            self.reject()  # inválida o sin red: se cierra y la app muestra M-08 o M-09

    def reject(self) -> None:
        if self.boton_guardar.text() == textos.D02_COMPROBANDO and self.resultado is None:
            return  # mientras valida, Esc no interrumpe
        super().reject()

    def pedir(self) -> tuple[ResultadoValidacion | None, CuentaEnLinea | None]:
        self.exec()
        return self.resultado, (self.cuenta if self.resultado is not None else None)
