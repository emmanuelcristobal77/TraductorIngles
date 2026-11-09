"""Segmentador con probabilidades de voz simuladas en ventanas de 512 muestras (T032)."""

import numpy as np
import pytest

from traductor.audio.captura import FragmentoAudio
from traductor.audio.segmentador import Segmentador, VENTANA

pytestmark = pytest.mark.spec("RF-012")

SR = 16000
S_POR_VENTANA = VENTANA / SR  # 0.032 s


class VadGuionado:
    """Devuelve una probabilidad por ventana, en el orden programado."""

    def __init__(self, probabilidades):
        self.probabilidades = list(probabilidades)

    def __call__(self, ventana):
        assert len(ventana) == VENTANA
        return self.probabilidades.pop(0) if self.probabilidades else 0.0


def ventanas(segundos):
    return int(round(segundos / S_POR_VENTANA))


def correr(probabilidades, sesion=1, t0=100.0):
    frases, voces = [], []
    seg = Segmentador(sesion=sesion, al_frase=frases.append,
                      voz_detectada=lambda: voces.append(True), vad=VadGuionado(probabilidades))
    total = len(probabilidades) * VENTANA
    audio = np.zeros(total, np.float32)
    # Se entrega en fragmentos de tamaño irregular, como llega de la captura.
    pos, n = 0, 0
    for tam in (700, 1300, 512, 3000) * (total // 5512 + 1):
        if pos >= total:
            break
        trozo = audio[pos:pos + tam]
        seg.procesar(FragmentoAudio(trozo, t0 + pos / SR))
        pos += len(trozo)
        n += 1
    return frases, voces


def test_frase_empieza_con_mas_de_05_y_termina_con_06_s_de_silencio():
    voz = ventanas(1.0)
    frases, _ = correr([0.2] * 5 + [0.9] * voz + [0.1] * ventanas(0.6) + [0.1] * 5)
    assert len(frases) == 1
    frase = frases[0]
    duracion_voz = voz * S_POR_VENTANA
    assert duracion_voz <= len(frase.audio) / SR <= duracion_voz + 0.7
    assert frase.t_fin_habla == pytest.approx(100.0 + (5 + voz) * S_POR_VENTANA, abs=1e-6)


def test_exactamente_05_no_cuenta_como_voz():
    frases, voces = correr([0.5] * ventanas(2.0) + [0.0] * ventanas(1.0))
    assert frases == [] and voces == []


def test_sin_el_silencio_completo_la_frase_no_termina():
    frases, _ = correr([0.9] * ventanas(1.0) + [0.1] * (ventanas(0.6) - 2))
    assert frases == []


def test_se_corta_a_la_fuerza_a_los_7_s():
    frases, _ = correr([0.9] * ventanas(10.0) + [0.0] * ventanas(1.0))
    assert len(frases) == 2
    assert len(frases[0].audio) / SR == pytest.approx(7.0, abs=0.05)
    assert all(len(f.audio) / SR <= 7.0 + 1e-6 for f in frases)


def test_descarta_frases_de_menos_de_03_s():
    frases, _ = correr([0.9] * ventanas(0.25) + [0.0] * ventanas(1.0))
    assert frases == []


def test_silencio_y_ruido_no_producen_frases():
    frases, voces = correr([0.0] * ventanas(3.0) + [0.3, 0.45, 0.2] * ventanas(1.0))
    assert frases == [] and voces == []


def test_cada_frase_lleva_su_sesion():
    frases, _ = correr([0.9] * ventanas(1.0) + [0.0] * ventanas(1.0), sesion=7)
    assert frases[0].sesion == 7


def test_voz_detectada_como_maximo_cada_05_s():
    frases, voces = correr([0.9] * ventanas(2.0) + [0.0] * ventanas(1.0))
    assert 4 <= len(voces) <= 5  # 2 s de voz → una vez cada 0.5 s
