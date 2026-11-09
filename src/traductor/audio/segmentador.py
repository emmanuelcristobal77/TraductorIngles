"""Corte del audio en frases con Silero VAD (research R-03).

- Ventanas de 512 muestras a 16 kHz.
- Una frase empieza cuando la probabilidad de voz pasa de 0.5.
- Termina con 0.6 s de silencio, o a la fuerza a los 7 s.
- Se descartan las frases de menos de 0.3 s.
- ``voz_detectada()`` se llama como máximo una vez cada 0.5 s mientras hay voz (RF-012).
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from traductor.audio.captura import FragmentoAudio
from traductor.motores.base import Frase

SR = 16000
VENTANA = 512
UMBRAL = 0.5
SILENCIO_FIN_S = 0.6
MAXIMO_S = 7.0
MINIMO_S = 0.3
INTERVALO_VOZ_S = 0.5


class VadSilero:
    """Silero VAD (ONNX) incluido en faster-whisper, ventana por ventana y con estado."""

    def __init__(self) -> None:
        from faster_whisper.vad import get_vad_model

        self._sesion = get_vad_model().session  # entradas: input (n, 576), h y c (1, 1, 128)
        self._contexto = np.zeros(64, np.float32)
        self._h = np.zeros((1, 1, 128), np.float32)
        self._c = np.zeros((1, 1, 128), np.float32)

    def __call__(self, ventana: np.ndarray) -> float:
        entrada = np.concatenate([self._contexto, ventana]).reshape(1, -1).astype(np.float32)
        salida, self._h, self._c = self._sesion.run(None, {"input": entrada, "h": self._h,
                                                           "c": self._c})
        self._contexto = ventana[-64:].astype(np.float32)
        return float(np.asarray(salida).reshape(-1)[-1])


class Segmentador:
    def __init__(self, sesion: int, al_frase: Callable[[Frase], None],
                 voz_detectada: Callable[[], None] | None = None,
                 vad: Callable[[np.ndarray], float] | None = None) -> None:
        self.sesion = sesion
        self._al_frase = al_frase
        self._voz_detectada = voz_detectada or (lambda: None)
        self._vad = vad or VadSilero()
        self._pendiente = np.zeros(0, np.float32)
        self._t_pendiente = 0.0  # instante del primer elemento de _pendiente
        self._frase: list[np.ndarray] = []
        self._muestras_hasta_voz = 0  # muestras de la frase hasta el final de la última voz
        self._silencio_s = 0.0
        self._t_fin_voz = 0.0
        self._ultimo_aviso_voz: float | None = None

    def procesar(self, fragmento: FragmentoAudio) -> None:
        if len(self._pendiente) == 0:
            self._t_pendiente = fragmento.t_inicio
        self._pendiente = np.concatenate([self._pendiente, fragmento.muestras.astype(np.float32)])
        while len(self._pendiente) >= VENTANA:
            ventana = self._pendiente[:VENTANA]
            t_fin_ventana = self._t_pendiente + VENTANA / SR
            self._pendiente = self._pendiente[VENTANA:]
            self._t_pendiente = t_fin_ventana
            self._ventana(ventana, self._vad(ventana) > UMBRAL, t_fin_ventana)

    def _ventana(self, ventana: np.ndarray, hay_voz: bool, t_fin: float) -> None:
        en_frase = bool(self._frase)
        if hay_voz:
            if en_frase and self._muestras_hasta_voz + VENTANA > MAXIMO_S * SR:
                self._cerrar_frase()  # corte a la fuerza: ninguna frase pasa de 7 s
            self._frase.append(ventana)
            self._muestras_hasta_voz = sum(len(v) for v in self._frase)
            self._silencio_s = 0.0
            self._t_fin_voz = t_fin
            if self._ultimo_aviso_voz is None or t_fin - self._ultimo_aviso_voz >= INTERVALO_VOZ_S:
                self._ultimo_aviso_voz = t_fin
                self._voz_detectada()
        elif en_frase:
            self._frase.append(ventana)
            self._silencio_s += VENTANA / SR
            if self._silencio_s >= SILENCIO_FIN_S - 1e-9:
                self._cerrar_frase()

    def _cerrar_frase(self) -> None:
        audio = np.concatenate(self._frase)[: self._muestras_hasta_voz]
        self._frase = []
        self._silencio_s = 0.0
        if len(audio) / SR >= MINIMO_S:
            self._al_frase(Frase(audio=audio, t_fin_habla=self._t_fin_voz, sesion=self.sesion))
