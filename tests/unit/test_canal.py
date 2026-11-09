"""Canal captura → segmentador → selector → glosario con piezas falsas (T036)."""

import queue
import threading
import time

import numpy as np
import pytest

from traductor.canal import Canal, poner_descartando_viejo
from traductor.motores.base import ErrorMotor, Frase
from traductor.motores.selector import SelectorMotor
from traductor.traduccion.glosario import Glosario

pytestmark = pytest.mark.spec("CA-004", "RF-013")


class CapturaFalsa:
    def __init__(self, al_mensaje):
        self.al_mensaje = al_mensaje
        self.cola = None
        self.detenida = False

    def iniciar(self, cola):
        self.cola = cola

    def detener(self):
        self.detenida = True


class SegmentadorFalso:
    """Convierte cada fragmento en una frase de inmediato."""

    def __init__(self, sesion, al_frase, voz_detectada):
        self.sesion, self.al_frase, self.voz_detectada = sesion, al_frase, voz_detectada

    def procesar(self, fragmento):
        self.voz_detectada()
        self.al_frase(Frase(fragmento.muestras, fragmento.t_inicio, self.sesion))


def armar(qtbot, motor):
    capturas = []

    def fabrica_captura(al_mensaje):
        capturas.append(CapturaFalsa(al_mensaje))
        return capturas[-1]

    canal = Canal(SelectorMotor(motor, lambda: None), Glosario(), fabrica_captura,
                  SegmentadorFalso)
    recibidos, mensajes, voces = [], [], []
    canal.subtitulo.connect(recibidos.append)
    canal.mensaje.connect(mensajes.append)
    canal.voz.connect(lambda: voces.append(1))
    return canal, capturas, recibidos, mensajes, voces


def fragmento(t=0.0):
    from traductor.audio.captura import FragmentoAudio

    return FragmentoAudio(np.zeros(1600, np.float32), t)


def test_cola_llena_descarta_lo_mas_viejo():
    cola = queue.Queue(maxsize=2)
    for i in range(4):
        poner_descartando_viejo(cola, i)
    assert [cola.get_nowait(), cola.get_nowait()] == [2, 3]


def test_flujo_y_sesion(qtbot, motor_falso):
    canal, capturas, recibidos, _, voces = armar(qtbot, motor_falso(resultados=["Me gusta el coche"]))
    canal.iniciar(5)
    capturas[-1].cola.put(fragmento())
    qtbot.waitUntil(lambda: bool(recibidos), timeout=2000)
    assert recibidos[0].texto == "Me gusta el carro" and recibidos[0].sesion == 5
    assert voces
    canal.detener()


def test_resultado_de_sesion_anterior_no_se_muestra(qtbot, motor_falso):
    liberar = threading.Event()

    class MotorLento(motor_falso):
        def traducir(self, frase):
            liberar.wait(2)
            return super().traducir(frase)

    canal, capturas, recibidos, _, _ = armar(qtbot, MotorLento(resultados=["viejo", "nuevo"]))
    canal.iniciar(1)
    capturas[-1].cola.put(fragmento())
    time.sleep(0.1)
    canal.detener()
    canal.iniciar(2)
    liberar.set()
    qtbot.wait(300)
    assert all(s.sesion == 2 for s in recibidos)
    canal.detener()


def test_detener_regresa_en_menos_de_1_s_aunque_el_motor_este_ocupado(qtbot, motor_falso):
    liberar = threading.Event()

    class MotorOcupado(motor_falso):
        def traducir(self, frase):
            liberar.wait(5)
            return super().traducir(frase)

    canal, capturas, _, _, _ = armar(qtbot, MotorOcupado())
    canal.iniciar(1)
    for i in range(5):
        capturas[-1].cola.put(fragmento(i))
    time.sleep(0.1)
    inicio = time.monotonic()
    canal.detener()
    assert time.monotonic() - inicio < 1.0
    assert capturas[-1].detenida
    assert canal.cola_audio.empty() and canal.cola_frases.empty()
    liberar.set()


def test_error_del_motor_emite_m04_sin_cambiar_nada(qtbot, motor_falso):
    canal, capturas, recibidos, mensajes, _ = armar(
        qtbot, motor_falso(resultados=["después"], errores=[ErrorMotor("x"), None]))
    canal.iniciar(1)
    capturas[-1].cola.put(fragmento(0))
    qtbot.waitUntil(lambda: bool(mensajes), timeout=2000)
    assert mensajes == ["M-04"]
    capturas[-1].cola.put(fragmento(1))
    qtbot.waitUntil(lambda: bool(recibidos), timeout=2000)
    assert recibidos[0].texto == "después"
    canal.detener()


def test_mensajes_de_la_captura_llegan(qtbot, motor_falso):
    canal, capturas, _, mensajes, _ = armar(qtbot, motor_falso())
    canal.iniciar(1)
    capturas[-1].al_mensaje("M-03")
    qtbot.waitUntil(lambda: bool(mensajes), timeout=2000)
    assert mensajes == ["M-03"]
    canal.detener()
