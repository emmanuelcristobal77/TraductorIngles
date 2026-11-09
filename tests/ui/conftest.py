"""Fixtures de interfaz: arma la app completa con piezas falsas (sin audio, red ni atajo real)."""

from __future__ import annotations

import threading

import pytest


class User32Falso:
    """Simula RegisterHotKey/UnregisterHotKey/GetLastError."""

    def __init__(self, ocupado: bool = False):
        self.ocupado = ocupado
        self.registros = []
        self.liberaciones = []
        self.ultimo_error = 0
        self.orden = None  # lista compartida para comprobar el orden de cierre

    def RegisterHotKey(self, hwnd, ident, mods, vk):  # noqa: N802 - nombre de la API de Windows
        self.registros.append((hwnd, ident, mods, vk))
        if self.ocupado:
            self.ultimo_error = 1409
            return 0
        return 1

    def UnregisterHotKey(self, hwnd, ident):  # noqa: N802
        self.liberaciones.append((hwnd, ident))
        if self.orden is not None:
            self.orden.append("UnregisterHotKey")
        return 1

    def GetLastError(self):  # noqa: N802
        return self.ultimo_error


@pytest.fixture
def user32_falso():
    return User32Falso


@pytest.fixture
def armar_app(qtbot, canal_falso, user32_falso, appdata_temporal):
    """Devuelve una función que arma ``Aplicacion`` con piezas falsas y la arranca."""
    creadas = []
    liberar = threading.Event()

    def armar(preparar=None, ocupado=False, arrancar=True, salir=None, bloquear_carga=False):
        from traductor.app import Aplicacion

        if bloquear_carga:
            def preparar():  # noqa: F811 - simula una carga de modelos que tarda
                liberar.wait(30)

        aplicacion = Aplicacion(canal=canal_falso, preparar=preparar or (lambda: None),
                                user32=user32_falso(ocupado=ocupado),
                                salir=salir or (lambda: None))
        qtbot.addWidget(aplicacion.ventana)
        qtbot.addWidget(aplicacion.franja)
        creadas.append(aplicacion)
        if arrancar:
            aplicacion.arrancar()
        return aplicacion

    yield armar
    liberar.set()
    for aplicacion in creadas:
        aplicacion.bandeja.hide()
