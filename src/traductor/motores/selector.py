"""Elige el motor y respalda sin internet (contracts/motor-traduccion.md §4)."""

from __future__ import annotations

from typing import Callable

from traductor.motores.base import (ErrorAutenticacion, ErrorConexion, ErrorMotor, Frase,
                                    MotorTraduccion, ResultadoMotor)


class SelectorMotor:
    def __init__(self, local: MotorTraduccion,
                 en_linea_factory: Callable[[], MotorTraduccion]) -> None:
        self.local = local
        self.en_linea_factory = en_linea_factory
        self.en_linea: MotorTraduccion | None = None
        # Eventos (callbacks); se llaman desde el hilo del selector.
        self.error_motor: list[Callable[[Exception], None]] = []
        self.conexion_perdida: list[Callable[[], None]] = []
        self.cuenta_rechazada: list[Callable[[], None]] = []

    def usar_en_linea(self) -> None:
        """Lanza ErrorPreparacion si no se puede; entonces el modo sigue SIN_INTERNET."""
        motor = self.en_linea_factory()
        motor.preparar()
        self.en_linea = motor

    def usar_local(self) -> None:
        motor, self.en_linea = self.en_linea, None
        if motor is not None:
            motor.cerrar()

    def _respaldo(self, eventos: list[Callable[[], None]]) -> None:
        self.usar_local()  # el motor local siempre está cargado: la vuelta es inmediata
        for observador in list(eventos):
            observador()

    def traducir(self, frase: Frase) -> ResultadoMotor | None:
        """Traduce con el motor del modo actual. Devuelve None si el motor falló."""
        en_linea = self.en_linea
        if en_linea is not None:
            try:
                return en_linea.traducir(frase)
            except ErrorConexion:
                self._respaldo(self.conexion_perdida)  # y se traduce la misma frase sin internet
            except ErrorAutenticacion:
                self._respaldo(self.cuenta_rechazada)
            except ErrorMotor as exc:
                for observador in list(self.error_motor):
                    observador(exc)
                return None
        try:
            return self.local.traducir(frase)
        except ErrorMotor as exc:
            for observador in list(self.error_motor):
                observador(exc)
            return None
