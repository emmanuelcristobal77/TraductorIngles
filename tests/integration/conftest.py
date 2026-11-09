"""Canal real (segmentador, motor local y glosario) alimentado con WAV en lugar de la captura."""

from __future__ import annotations

import threading
import time

import numpy as np
import pytest

from traductor.audio.captura import FragmentoAudio

BLOQUE = 1600  # 0.1 s


class FuenteWav:
    """Sustituye a CapturaLoopback: entrega los WAV al ritmo real, como si sonaran."""

    def __init__(self, audios, silencio_entre_s=1.5, tiempo_real=True):
        self.audios = audios
        self.silencio = np.zeros(int(16000 * silencio_entre_s), np.float32)
        self.tiempo_real = tiempo_real
        self.terminado = threading.Event()
        self._parar = threading.Event()

    def iniciar(self, cola):
        def correr():
            for audio in self.audios:
                for trozo in (audio, self.silencio):
                    for i in range(0, len(trozo), BLOQUE):
                        if self._parar.is_set():
                            return
                        cola.put(FragmentoAudio(trozo[i:i + BLOQUE], time.monotonic()))
                        if self.tiempo_real:
                            time.sleep(BLOQUE / 16000)
            self.terminado.set()

        threading.Thread(target=correr, daemon=True).start()

    def detener(self):
        self._parar.set()


@pytest.fixture(scope="session")
def motor_local_real():
    from traductor.motores.local import MotorLocal, carpeta_modelos

    if not (carpeta_modelos() / "opus-mt-en-es-ct2").exists():
        pytest.skip("faltan los modelos: corre scripts/preparar_modelos.py")
    motor = MotorLocal()
    motor.preparar()
    yield motor
    motor.cerrar()


@pytest.fixture
def canal_real(qtbot, motor_local_real):
    """Devuelve (canal, subtitulos, latencias) para una lista de audios."""
    from traductor.audio.segmentador import Segmentador
    from traductor.canal import Canal
    from traductor.motores.selector import SelectorMotor
    from traductor.traduccion.glosario import Glosario

    canales = []

    def armar(audios, tiempo_real=True):
        fuente = FuenteWav(audios, tiempo_real=tiempo_real)
        selector = SelectorMotor(motor_local_real, lambda: None)
        fines = {}
        original = selector.traducir

        def traducir(frase):
            resultado = original(frase)
            if resultado is not None and resultado.texto_es:
                fines[glosario.aplicar(resultado.texto_es)] = frase.t_fin_habla
            return resultado

        selector.traducir = traducir
        glosario = Glosario()
        canal = Canal(selector, glosario, lambda al_mensaje: fuente, Segmentador)
        subtitulos, latencias = [], []

        def recibir(subtitulo):
            subtitulos.append(subtitulo)
            latencias.append(time.monotonic() - fines[subtitulo.texto])

        canal.subtitulo.connect(recibir)
        canales.append(canal)
        canal.iniciar(1)
        return canal, fuente, subtitulos, latencias

    yield armar
    for canal in canales:
        canal.detener()
