"""Elige el motor y respalda sin internet (contracts/motor-traduccion.md §4)."""

from __future__ import annotations

from typing import Callable

from traductor.motores.base import ErrorMotor, Frase, MotorTraduccion, ResultadoMotor


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

    def usar_local(self) -> None:
        motor, self.en_linea = self.en_linea, None
        if motor is not None:
            motor.cerrar()

    def traducir(self, frase: Frase) -> ResultadoMotor | None:
        """Traduce con el motor del modo actual. Devuelve None si el motor local falló."""
        try:
            return self.local.traducir(frase)
        except ErrorMotor as exc:
            for observador in list(self.error_motor):
                observador(exc)
            return None
