"""Fixtures comunes y marcador ``spec`` (T010)."""

from __future__ import annotations

import socket
import wave
from pathlib import Path

import numpy as np
import pytest

AUDIOS = Path(__file__).parent / "fixtures" / "audio"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "spec(*ids): identificadores RF/CA de spec.md que cubre el test"
    )
    config.addinivalue_line("markers", "modelos: necesita los modelos descargados en modelos/")


@pytest.fixture(autouse=True)
def appdata_temporal(tmp_path, monkeypatch):
    """Redirige APPDATA y LOCALAPPDATA a una carpeta temporal en **todos** los tests, para que
    ninguno escriba ajustes, cuentas ni bitácora en las carpetas reales de la persona."""
    roaming = tmp_path / "Roaming"
    local = tmp_path / "Local"
    roaming.mkdir()
    local.mkdir()
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    return tmp_path


@pytest.fixture
def bloquear_red(monkeypatch):
    """Cualquier intento de abrir un socket falla la prueba."""

    def prohibido(*args, **kwargs):
        raise AssertionError("se intentó usar la red")

    monkeypatch.setattr(socket, "socket", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)


class MotorFalso:
    """Implementación de MotorTraduccion con resultados programados."""

    def __init__(self, nombre="LOCAL", resultados=None, error_preparar=None, errores=None,
                 demora_preparar=0.0):
        self.nombre = nombre
        self.resultados = list(resultados or [])
        self.error_preparar = error_preparar
        self.errores = list(errores or [])
        self.demora_preparar = demora_preparar
        self.frases = []
        self.preparado = False
        self.cerrado = 0

    def preparar(self):
        if self.demora_preparar:
            import time

            time.sleep(self.demora_preparar)
        if self.error_preparar is not None:
            raise self.error_preparar
        self.preparado = True

    def traducir(self, frase):
        self.frases.append(frase)
        if self.errores:
            error = self.errores.pop(0)
            if error is not None:
                raise error
        from traductor.motores.base import MotivoDescarte, ResultadoMotor, TipoMotor

        texto = self.resultados.pop(0) if self.resultados else "texto"
        motivo = MotivoDescarte.NINGUNO if texto else MotivoDescarte.SIN_VOZ
        return ResultadoMotor(texto_es=texto or None, motivo_descarte=motivo,
                              motor=TipoMotor(self.nombre))

    def cerrar(self):
        self.cerrado += 1


@pytest.fixture
def motor_falso():
    return MotorFalso


class CanalFalso:
    """Registra cuántas veces se inició y se detuvo el canal."""

    def __init__(self):
        self.inicios = []
        self.detenciones = 0

    def iniciar(self, sesion):
        self.inicios.append(sesion)

    def detener(self):
        self.detenciones += 1


@pytest.fixture
def canal_falso():
    return CanalFalso()


@pytest.fixture
def cargar_wav():
    def cargar(nombre: str) -> np.ndarray:
        with wave.open(str(AUDIOS / nombre), "rb") as w:
            assert w.getframerate() == 16000 and w.getnchannels() == 1
            datos = w.readframes(w.getnframes())
        return np.frombuffer(datos, dtype=np.int16).astype(np.float32) / 32768.0

    return cargar
