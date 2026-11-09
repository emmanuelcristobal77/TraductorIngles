"""Arranque, cableado, carga de modelos en segundo plano y cierre ordenado (RF-004a)."""

from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import QObject, QThreadPool, Signal
from PySide6.QtWidgets import QApplication

from traductor import bitacora
from traductor.estado import EstadoTraduccion, ValorEstado
from traductor.motores.base import ErrorPreparacion


class Controlador(QObject):
    """Une el estado con el canal, los mensajes y el cierre de la app."""

    _preparado = Signal()
    _fallo = Signal()

    def __init__(self, estado: EstadoTraduccion, fabrica_canal, preparar: Callable[[], None] | None = None,
                 salir: Callable[[], None] | None = None) -> None:
        super().__init__()
        self.estado = estado
        self.canal = fabrica_canal
        self.preparar = preparar or (lambda: None)
        self.salir = salir or QApplication.quit
        self.al_mensaje: list[Callable[[str], None]] = []
        self.al_cerrar: list[Callable[[], None]] = []  # pasos tras desactivar, en orden
        self.motores: list = []
        self._canal_iniciado = False
        self._cerrando = False
        estado.al_cambiar.append(self._estado_cambio)
        estado.al_fallar_preparacion.append(lambda: self.publicar_mensaje("M-05"))
        self._preparado.connect(self.estado.modelos_listos)
        self._fallo.connect(self.estado.preparacion_fallida)

    # --- estado ---------------------------------------------------------------------------
    def _estado_cambio(self, estado: EstadoTraduccion) -> None:
        if estado.valor is ValorEstado.ACTIVA:
            self.canal.iniciar(estado.sesion)
            self._canal_iniciado = True
        elif estado.valor is ValorEstado.DESACTIVADA and self._canal_iniciado:
            self.canal.detener()
            self._canal_iniciado = False

    # --- mensajes -------------------------------------------------------------------------
    def publicar_mensaje(self, id_mensaje: str) -> None:
        """Muestra un mensaje del catálogo. Un error del motor no cambia el estado (RF-013)."""
        for observador in list(self.al_mensaje):
            observador(id_mensaje)

    # --- carga en segundo plano -----------------------------------------------------------
    def iniciar_carga(self) -> None:
        QThreadPool.globalInstance().start(self._cargar)

    def _cargar(self) -> None:
        try:
            self.preparar()
        except ErrorPreparacion as exc:
            bitacora.registrar_error("preparacion", exc)
            self._fallo.emit()
        except Exception as exc:  # noqa: BLE001 - cualquier falla al cargar cuenta como preparación fallida
            bitacora.registrar_error("preparacion", exc)
            self._fallo.emit()
        else:
            self._preparado.emit()

    # --- cierre (data-model §10) ----------------------------------------------------------
    def cerrar_app(self) -> None:
        if self._cerrando:
            return
        self._cerrando = True
        self.estado.desactivar()
        for paso in list(self.al_cerrar):
            try:
                paso()
            except Exception as exc:  # noqa: BLE001
                bitacora.registrar_error("cierre", exc)
        for motor in self.motores:
            try:
                motor.cerrar()
            except Exception as exc:  # noqa: BLE001
                bitacora.registrar_error("cierre", exc)
        self.salir()


class _PuenteSelector(QObject):
    """Lleva los eventos del selector (hilo de traducción) al hilo de Qt."""

    conexion_perdida = Signal()
    cuenta_rechazada = Signal()


class Aplicacion:
    """Arma la app completa. Las piezas externas se pueden reemplazar en los tests."""

    def __init__(self, canal=None, preparar: Callable[[], None] | None = None, user32=None,
                 salir: Callable[[], None] | None = None, selector=None) -> None:
        from traductor.ui.atajo import AtajoGlobal
        from traductor.ui.bandeja import Bandeja
        from traductor.ui.ventana import VentanaPrincipal

        from traductor.ui.subtitulos import FranjaSubtitulos

        motores = []
        if canal is None:
            canal, motor_local = self._canal_real()
            motores.append(motor_local)
            preparar = preparar or motor_local.preparar
        self.canal = canal
        self.estado = EstadoTraduccion()
        self.control = Controlador(self.estado, canal, preparar=preparar, salir=salir)
        self.control.motores.extend(motores)
        self.ventana = VentanaPrincipal()
        self.bandeja = Bandeja()
        self.franja = FranjaSubtitulos()
        self.atajo = AtajoGlobal(lambda: int(self.ventana.winId()), user32=user32)

        # Subtítulos, voz y errores del canal (en el hilo de Qt).
        if hasattr(canal, "subtitulo"):
            canal.subtitulo.connect(lambda s: self.franja.mostrar(s, self.estado.sesion))
            canal.voz.connect(self.franja.marcar_voz)
            canal.mensaje.connect(self.control.publicar_mensaje)
        self.estado.al_cambiar.append(self._ocultar_franja_si_desactivada)
        self.ventana.mover_solicitado.connect(self.franja.entrar_modo_mover)
        self.franja.modo_mover_terminado.connect(self.ventana.enfocar_mover)

        # Modo en línea (data-model §2). Al abrir siempre empieza sin internet.
        from traductor.ajustes import Ajustes
        from traductor.estado import ModoProcesamiento

        self.modo = ModoProcesamiento()
        self.ajustes = Ajustes.cargar()
        self.selector = selector or getattr(canal, "selector", None)
        self._cuenta_activa = None
        self.pedir_aviso = self._pedir_aviso
        self.pedir_cuenta = self._pedir_cuenta
        self.modo.al_cambiar.append(lambda m: self.ventana.mostrar_modo(m.valor))
        self.ventana.modo_solicitado.connect(self._modo_solicitado)
        self._puente = _PuenteSelector()
        self._puente.conexion_perdida.connect(self._conexion_perdida)
        self._puente.cuenta_rechazada.connect(self._cuenta_rechazada)
        if self.selector is not None:
            if self.selector.en_linea_factory is None:
                self.selector.en_linea_factory = self._crear_motor_en_linea
            self.selector.conexion_perdida.append(self._puente.conexion_perdida.emit)
            self.selector.cuenta_rechazada.append(self._puente.cuenta_rechazada.emit)

        # UI-01, opción 1 del menú y Ctrl+Alt+T alternan el estado.
        self.ventana.alternar_solicitado.connect(self.estado.alternar)
        self.bandeja.alternar_solicitado.connect(self.estado.alternar)
        self.atajo.presionado.connect(self.estado.alternar)

        self.estado.al_cambiar.append(self.ventana.actualizar_estado)
        self.estado.al_cambiar.append(self.bandeja.actualizar_estado)
        self.control.al_mensaje.append(self._mostrar_mensaje)

        self.bandeja.abrir_solicitado.connect(self.ventana.mostrar_y_traer)
        self.bandeja.salir_solicitado.connect(self.control.cerrar_app)
        self.ventana.cerrar_solicitado.connect(self.control.cerrar_app)
        # Orden de data-model §10, después de pasar a DESACTIVADA.
        self.control.al_cerrar.extend([self.franja.ocultar_ya, self.bandeja.hide,
                                       self.atajo.liberar])

    @staticmethod
    def _canal_real():
        from traductor.audio.captura import CapturaLoopback
        from traductor.audio.segmentador import Segmentador
        from traductor.canal import Canal
        from traductor.motores.local import MotorLocal
        from traductor.motores.selector import SelectorMotor
        from traductor.traduccion.glosario import Glosario

        motor_local = MotorLocal()
        selector = SelectorMotor(motor_local, en_linea_factory=None)  # la pone Aplicacion
        canal = Canal(selector, Glosario(), lambda al_mensaje: CapturaLoopback(al_mensaje),
                      Segmentador)
        return canal, motor_local

    # --- modo en línea ---------------------------------------------------------------------
    def _pedir_aviso(self) -> bool:
        from traductor.ui.dialogos import AvisoEnLinea

        return AvisoEnLinea(self.ventana).preguntar()

    def _pedir_cuenta(self):
        from traductor.ui.dialogos import CuadroCuenta

        return CuadroCuenta(self.ventana).pedir()

    def _sesion_activa(self) -> int | None:
        return self.estado.sesion if self.estado.valor is ValorEstado.ACTIVA else None

    def _crear_motor_en_linea(self):
        from traductor.motores.en_linea import MotorEnLinea

        return MotorEnLinea(self._cuenta_activa, sesion_activa=self._sesion_activa)

    def _quedar_sin_internet(self, id_mensaje: str | None = None) -> None:
        if self.selector is not None:
            self.selector.usar_local()
        self.modo.volver_sin_internet()
        self.ventana.mostrar_modo(self.modo.valor)  # UI-04 vuelve a apagado en cualquier caso
        if id_mensaje:
            self.control.publicar_mensaje(id_mensaje)

    def _modo_solicitado(self, encender: bool) -> None:
        from traductor import cuenta
        from traductor.cuenta import ResultadoValidacion
        from traductor.motores.base import ErrorPreparacion

        if not encender:
            self._quedar_sin_internet()
            return
        if not self.ajustes.aviso_en_linea_aceptado:
            if not self.pedir_aviso():
                self._quedar_sin_internet()  # el aviso volverá a salir la siguiente vez
                return
            self.ajustes.aviso_en_linea_aceptado = True
            self.ajustes.guardar()
        guardada = cuenta.cargar()
        if guardada is None:
            resultado, nueva = self.pedir_cuenta()
            if resultado is None:
                self._quedar_sin_internet()  # cancelar: sin mensaje
                return
            if resultado is ResultadoValidacion.INVALIDA:
                self._quedar_sin_internet("M-08")
                return
            if resultado is ResultadoValidacion.SIN_RED:
                self._quedar_sin_internet("M-09")
                return
            cuenta.guardar(nueva)  # solo se guarda después de que el servicio la acepta
            guardada = nueva
        self._cuenta_activa = guardada
        if self.selector is None:
            self._quedar_sin_internet()
            return
        try:
            self.selector.usar_en_linea()
        except ErrorPreparacion as exc:
            bitacora.registrar_error("en_linea", exc)
            self._quedar_sin_internet("M-08")
            return
        self.modo.encender_en_linea()

    def _conexion_perdida(self) -> None:
        self._quedar_sin_internet("M-07")  # la traducción sigue sin internet (RF-015b)

    def _cuenta_rechazada(self) -> None:
        from traductor import cuenta

        cuenta.borrar()  # se volverá a pedir la siguiente vez (RF-015c)
        self._quedar_sin_internet("M-08")

    def _ocultar_franja_si_desactivada(self, estado: EstadoTraduccion) -> None:
        if estado.valor is ValorEstado.DESACTIVADA:
            self.franja.ocultar_ya()

    def _mostrar_mensaje(self, id_mensaje: str) -> None:
        self.ventana.mostrar_mensaje(id_mensaje)
        if id_mensaje == "M-05":
            self.bandeja.avisar("M-05")  # se ve aunque la ventana esté minimizada (RF-005)

    def arrancar(self) -> None:
        self.ventana.show()
        self.bandeja.show()
        if not self.atajo.registrar():
            self.control.publicar_mensaje("M-06")
        self.control.iniciar_carga()


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # el cierre lo hace Controlador.cerrar_app (RF-004a)
    aplicacion = Aplicacion()
    aplicacion.arrancar()
    return app.exec()
