"""Protocolo de los motores de traducción y sus datos (contracts/motor-traduccion.md §1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Frase:
    """Entre 0.3 s y 7 s de duración (research R-03)."""

    audio: np.ndarray  # float32, 16 kHz, mono
    t_fin_habla: float  # instante monotónico; desde aquí se cuentan los 3 s de CA-002
    sesion: int


class MotivoDescarte(Enum):
    NINGUNO = "NINGUNO"
    OTRO_IDIOMA = "OTRO_IDIOMA"
    SIN_VOZ = "SIN_VOZ"
    BAJA_CONFIANZA = "BAJA_CONFIANZA"


class TipoMotor(Enum):
    LOCAL = "LOCAL"
    EN_LINEA = "EN_LINEA"


@dataclass(frozen=True)
class ResultadoMotor:
    texto_es: str | None
    motivo_descarte: MotivoDescarte
    motor: TipoMotor


class ErrorPreparacion(Exception):
    """No se pudieron cargar los modelos o abrir la conexión."""


class ErrorConexion(Exception):
    """Solo EN_LINEA: error de red, desconexión o 10 s sin respuesta."""


class ErrorAutenticacion(Exception):
    """Solo EN_LINEA: el servicio rechazó la clave o la región."""


class ErrorMotor(Exception):
    """Falla interna al traducir una frase."""


class MotorTraduccion(Protocol):
    nombre: str  # "LOCAL" o "EN_LINEA"

    def preparar(self) -> None:
        """Carga modelos o abre la conexión. Lanza ErrorPreparacion si no se puede."""

    def traducir(self, frase: Frase) -> ResultadoMotor:
        """Audio en inglés → texto en español (sin el glosario). ``texto_es=None`` si se descarta."""

    def cerrar(self) -> None:
        """Libera los recursos. Se puede llamar más de una vez."""
