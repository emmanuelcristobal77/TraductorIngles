"""El texto del motor llega a la franja ya con el glosario (T048)."""

import numpy as np
import pytest

from traductor.audio.captura import FragmentoAudio
from traductor.canal import Canal
from traductor.motores.base import Frase
from traductor.motores.selector import SelectorMotor
from traductor.traduccion.glosario import Glosario
from traductor.ui.subtitulos import FranjaSubtitulos

pytestmark = pytest.mark.spec("RF-008")


class CapturaFalsa:
    def __init__(self, al_mensaje):
        self.cola = None

    def iniciar(self, cola):
        self.cola = cola

    def detener(self):
        pass


class SegmentadorFalso:
    def __init__(self, sesion, al_frase, voz_detectada):
        self.sesion, self.al_frase = sesion, al_frase

    def procesar(self, fragmento):
        self.al_frase(Frase(fragmento.muestras, fragmento.t_inicio, self.sesion))


def test_resultado_llega_a_la_franja_con_el_glosario(qtbot, motor_falso):
    capturas = []
    canal = Canal(SelectorMotor(motor_falso(resultados=["Me gusta el coche"]), lambda: None),
                  Glosario(), lambda al_mensaje: capturas.append(CapturaFalsa(al_mensaje)) or capturas[-1],
                  SegmentadorFalso)
    franja = FranjaSubtitulos()
    qtbot.addWidget(franja)
    canal.subtitulo.connect(lambda s: franja.mostrar(s, 3))
    canal.iniciar(3)
    capturas[-1].cola.put(FragmentoAudio(np.zeros(1600, np.float32), 0.0))
    qtbot.waitUntil(lambda: franja.texto_visible() == "Me gusta el carro", timeout=2000)
    canal.detener()
