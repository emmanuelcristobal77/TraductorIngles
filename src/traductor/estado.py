"""Estado de traducción y modo de procesamiento (data-model §1 y §2). Sin dependencias de Qt."""

from __future__ import annotations

from enum import Enum
from typing import Callable


class ValorEstado(Enum):
    DESACTIVADA = "DESACTIVADA"
    PREPARANDO = "PREPARANDO"
    ACTIVA = "ACTIVA"


class EstadoTraduccion:
    """Al abrir la app siempre vale ``DESACTIVADA`` (RF-004).

    ``sesion`` sube en 1 cada vez que la traducción se activa; los resultados de una sesión
    anterior se descartan. Tras ``preparacion_fallida()`` ya no se puede activar mientras la app
    siga abierta: ``activar()`` solo vuelve a avisar a ``al_fallar_preparacion`` (RF-005).
    """

    def __init__(self) -> None:
        self.valor = ValorEstado.DESACTIVADA
        self.sesion = 0
        self.al_cambiar: list[Callable[[EstadoTraduccion], None]] = []
        self.al_fallar_preparacion: list[Callable[[], None]] = []
        self._listo = False
        self._fallida = False

    @property
    def fallida(self) -> bool:
        return self._fallida

    def _cambiar(self, nuevo: ValorEstado) -> None:
        if nuevo is self.valor:
            return
        if nuevo is ValorEstado.ACTIVA:
            self.sesion += 1
        self.valor = nuevo
        for observador in list(self.al_cambiar):
            observador(self)

    def _avisar_falla(self) -> None:
        for observador in list(self.al_fallar_preparacion):
            observador()

    def activar(self) -> None:
        if self._fallida:
            self._avisar_falla()
            return
        if self.valor is not ValorEstado.DESACTIVADA:
            return
        self._cambiar(ValorEstado.ACTIVA if self._listo else ValorEstado.PREPARANDO)

    def desactivar(self) -> None:
        self._cambiar(ValorEstado.DESACTIVADA)

    def alternar(self) -> None:
        if self.valor is ValorEstado.DESACTIVADA:
            self.activar()
        else:
            self.desactivar()

    def modelos_listos(self) -> None:
        self._listo = True
        if self.valor is ValorEstado.PREPARANDO:
            self._cambiar(ValorEstado.ACTIVA)

    def preparacion_fallida(self) -> None:
        self._fallida = True
        self._cambiar(ValorEstado.DESACTIVADA)
        self._avisar_falla()


class ValorModo(Enum):
    SIN_INTERNET = "SIN_INTERNET"
    EN_LINEA = "EN_LINEA"


class ModoProcesamiento:
    """Al abrir la app siempre vale ``SIN_INTERNET`` (RF-015, RF-015a)."""

    def __init__(self) -> None:
        self.valor = ValorModo.SIN_INTERNET
        self.al_cambiar: list[Callable[[ModoProcesamiento], None]] = []

    def _cambiar(self, nuevo: ValorModo) -> None:
        if nuevo is self.valor:
            return
        self.valor = nuevo
        for observador in list(self.al_cambiar):
            observador(self)

    def encender_en_linea(self) -> None:
        self._cambiar(ValorModo.EN_LINEA)

    def volver_sin_internet(self) -> None:
        self._cambiar(ValorModo.SIN_INTERNET)
