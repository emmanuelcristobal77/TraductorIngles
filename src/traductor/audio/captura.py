"""Captura de lo que suena por bocinas o audífonos con WASAPI loopback (research R-02).

- Solo el dispositivo *loopback* de la salida predeterminada, en modo compartido: nunca el
  micrófono (RF-011) y nunca modo exclusivo, así que no altera el audio (RF-010).
- Remuestrea a 16 kHz mono float32.
- Si no llegan datos (no suena nada), entrega silencio.
- Revisa la salida predeterminada cada 2 s (y cuando una lectura falla) para seguir al nuevo
  dispositivo sin reactivar nada.
- Cada 0.5 s **lee** con pycaw si la salida está silenciada o en 0; en ese caso entrega
  silencio. Si la lectura falla, supone que suena.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable

import numpy as np

from traductor import bitacora

SR = 16000
BLOQUE_S = 0.1
REVISAR_DISPOSITIVO_S = 2.0
REVISAR_VOLUMEN_S = 0.5
SILENCIO_TRAS_S = 0.1


@dataclass
class FragmentoAudio:
    """16 kHz, mono, valores entre -1.0 y 1.0."""

    muestras: np.ndarray
    t_inicio: float


def convertir(datos: bytes, formato: int, canales: int, remuestreo, pa_int16: int) -> np.ndarray:
    """Bytes intercalados del loopback → float32 mono a 16 kHz."""
    if formato == pa_int16:
        muestras = np.frombuffer(datos, dtype="<i2").astype(np.float32) / 32768.0
    else:
        muestras = np.frombuffer(datos, dtype="<f4").astype(np.float32)
    if canales > 1:
        muestras = muestras[: len(muestras) - len(muestras) % canales]
        muestras = muestras.reshape(-1, canales).mean(axis=1)
    salida = remuestreo.resample_chunk(np.ascontiguousarray(muestras, dtype=np.float32))
    return np.clip(salida, -1.0, 1.0).astype(np.float32)


class LectorVolumen:
    """Solo lee el silencio y el volumen maestro de la salida predeterminada (R-02)."""

    def __init__(self, obtener_endpoint: Callable[[], object] | None = None) -> None:
        self._obtener_endpoint = obtener_endpoint or self._endpoint_pycaw
        self._endpoint = None

    @staticmethod
    def _endpoint_pycaw():
        import comtypes
        from pycaw.pycaw import AudioUtilities

        try:
            comtypes.CoInitialize()
        except OSError:
            pass
        return AudioUtilities.GetSpeakers().EndpointVolume

    def reiniciar(self) -> None:
        self._endpoint = None

    def __call__(self) -> bool:
        if self._endpoint is None:
            self._endpoint = self._obtener_endpoint()
        return bool(self._endpoint.GetMute()) or self._endpoint.GetMasterVolumeLevelScalar() <= 0.0


class CapturaLoopback:
    def __init__(self, al_mensaje: Callable[[str], None], pyaudio_mod=None,
                 silenciado: Callable[[], bool] | None = None,
                 reloj: Callable[[], float] = time.monotonic) -> None:
        self._al_mensaje = al_mensaje
        self._mod = pyaudio_mod
        self._silenciado = silenciado if silenciado is not None else LectorVolumen()
        self._reloj = reloj
        self.cola: queue.Queue | None = None
        self._pa = None
        self._stream = None
        self._dispositivo = None
        self._formato = None
        self._remuestreo = None
        self._hilo: threading.Thread | None = None
        self._corriendo = threading.Event()
        self._t_revision_dispositivo = 0.0
        self._t_revision_volumen = -1e9
        self._esta_silenciado = False
        self._t_ultimo = 0.0
        self._m03_avisado = False

    # --- abrir y cerrar -------------------------------------------------------------------
    def _modulo(self):
        if self._mod is None:
            import pyaudiowpatch

            self._mod = pyaudiowpatch
        return self._mod

    def abrir(self) -> bool:
        """Abre el loopback de la salida predeterminada. Emite M-02 si no hay salida."""
        mod = self._modulo()
        try:
            if self._pa is None:
                self._pa = mod.PyAudio()
            dispositivo = self._pa.get_default_wasapi_loopback()
            if not dispositivo or not dispositivo.get("isLoopbackDevice"):
                raise OSError("sin loopback")
        except Exception as exc:  # noqa: BLE001
            bitacora.registrar_error("captura", exc)
            self._al_mensaje("M-02")
            return False
        import soxr

        self._formato = mod.paInt16
        tasa = int(dispositivo["defaultSampleRate"])
        canales = int(dispositivo["maxInputChannels"]) or 2
        self._stream = self._pa.open(format=self._formato, channels=canales, rate=tasa, input=True,
                                     input_device_index=dispositivo["index"],
                                     frames_per_buffer=int(tasa * BLOQUE_S))
        self._dispositivo = dispositivo
        self._remuestreo = soxr.ResampleStream(tasa, SR, 1, dtype="float32")
        ahora = self._reloj()
        self._t_revision_dispositivo = ahora
        self._t_ultimo = ahora
        return True

    def cerrar_stream(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop_stream()
            except Exception:  # noqa: BLE001
                pass
            try:
                stream.close()
            except Exception:  # noqa: BLE001
                pass

    def iniciar(self, cola: queue.Queue) -> None:
        self.cola = cola
        if not self.abrir():
            return
        self._corriendo.set()
        self._hilo = threading.Thread(target=self._bucle, name="captura", daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._corriendo.clear()
        hilo, self._hilo = self._hilo, None
        if hilo is not None and hilo is not threading.current_thread():
            hilo.join(timeout=0.5)
        self.cerrar_stream()
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:  # noqa: BLE001
                pass
            self._pa = None

    # --- lectura --------------------------------------------------------------------------
    def _bucle(self) -> None:
        while self._corriendo.is_set():
            if not self.paso():
                time.sleep(0.02)

    def _entregar(self, muestras: np.ndarray, t_fin: float) -> None:
        if self.cola is None or len(muestras) == 0:
            return
        if self._esta_silenciado:
            muestras = np.zeros_like(muestras)
        fragmento = FragmentoAudio(muestras, t_fin - len(muestras) / SR)
        try:
            self.cola.put_nowait(fragmento)
        except queue.Full:
            try:
                self.cola.get_nowait()  # se descarta lo más viejo
            except queue.Empty:
                pass
            self.cola.put_nowait(fragmento)

    def _revisar_volumen(self, ahora: float) -> None:
        if ahora - self._t_revision_volumen < REVISAR_VOLUMEN_S:
            return
        self._t_revision_volumen = ahora
        try:
            self._esta_silenciado = bool(self._silenciado())
        except Exception:  # noqa: BLE001 - si no se puede leer, se supone que suena
            self._esta_silenciado = False

    def _cambio_dispositivo(self) -> bool:
        try:
            actual = self._pa.get_default_wasapi_loopback()
        except Exception:  # noqa: BLE001
            return False
        return bool(actual) and (self._dispositivo is None
                                 or actual.get("index") != self._dispositivo.get("index")
                                 or actual.get("name") != self._dispositivo.get("name"))

    def _reabrir(self) -> bool:
        self.cerrar_stream()
        if isinstance(self._silenciado, LectorVolumen):
            self._silenciado.reiniciar()
        self._t_revision_volumen = -1e9
        return self.abrir()

    def paso(self) -> bool:
        """Una vuelta de lectura. Devuelve True si llegaron datos."""
        ahora = self._reloj()
        if ahora - self._t_revision_dispositivo >= REVISAR_DISPOSITIVO_S:
            self._t_revision_dispositivo = ahora
            if self._cambio_dispositivo():
                self._reabrir()
        self._revisar_volumen(ahora)
        if self._stream is None:
            return False
        try:
            disponibles = self._stream.get_read_available()
            datos = self._stream.read(disponibles, exception_on_overflow=False) if disponibles else b""
        except Exception as exc:  # noqa: BLE001
            bitacora.registrar_error("captura", exc)
            if self._cambio_dispositivo() and self._reabrir():
                return False
            if not self._m03_avisado:
                self._m03_avisado = True
                self._al_mensaje("M-03")
            self.cerrar_stream()
            return False
        if datos:
            canales = int(self._dispositivo["maxInputChannels"]) or 2
            muestras = convertir(datos, self._formato, canales, self._remuestreo, self._modulo().paInt16)
            self._entregar(muestras, ahora)
            self._t_ultimo = ahora
            return True
        if ahora - self._t_ultimo >= SILENCIO_TRAS_S:
            # No suena nada: WASAPI no entrega datos, así que se entrega el silencio equivalente.
            n = int(round((ahora - self._t_ultimo) * SR))
            self._entregar(np.zeros(n, np.float32), ahora)
            self._t_ultimo = ahora
        return False
