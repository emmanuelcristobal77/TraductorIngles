"""Regreso automático sin internet visto en la interfaz (T062)."""

import numpy as np
import pytest

from traductor import cuenta, textos
from traductor.ajustes import Ajustes
from traductor.audio.captura import FragmentoAudio
from traductor.canal import Canal
from traductor.cuenta import CuentaEnLinea
from traductor.estado import ValorEstado, ValorModo
from traductor.motores.base import ErrorAutenticacion, ErrorConexion, Frase
from traductor.motores.selector import SelectorMotor
from traductor.traduccion.glosario import Glosario

pytestmark = pytest.mark.spec("RF-015b", "RF-015c", "CA-013")


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


@pytest.fixture
def app_en_linea_activa(armar_app, motor_falso, appdata_temporal, qtbot):
    def armar(error):
        capturas = []
        local = motor_falso(resultados=["sin internet 1", "sin internet 2"])
        remoto = motor_falso(nombre="EN_LINEA", errores=[error("x")])
        selector = SelectorMotor(local, lambda: remoto)
        canal = Canal(selector, Glosario(),
                      lambda al_mensaje: capturas.append(CapturaFalsa(al_mensaje)) or capturas[-1],
                      SegmentadorFalso)
        Ajustes(aviso_en_linea_aceptado=True).guardar()
        cuenta.guardar(CuentaEnLinea("clave", "eastus"))
        app = armar_app(canal=canal, selector=selector)
        qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
        app.ventana.casilla_modo.click()
        assert app.modo.valor is ValorModo.EN_LINEA
        app.estado.activar()
        recibidos = []
        canal.subtitulo.connect(recibidos.append)
        capturas[-1].cola.put(FragmentoAudio(np.zeros(1600, np.float32), 0.0))
        return app, capturas, recibidos

    yield armar


def test_conexion_perdida_muestra_m07_y_sigue_traduciendo(qtbot, app_en_linea_activa):
    app, capturas, recibidos = app_en_linea_activa(ErrorConexion)
    qtbot.waitUntil(lambda: app.modo.valor is ValorModo.SIN_INTERNET, timeout=3000)
    assert app.ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-07"]
    assert app.ventana.etiqueta_modo.text() == textos.UI03_SIN_INTERNET
    assert not app.ventana.casilla_modo.isChecked()
    qtbot.waitUntil(lambda: len(recibidos) == 1, timeout=3000)  # la misma frase, sin internet
    capturas[-1].cola.put(FragmentoAudio(np.zeros(1600, np.float32), 1.0))
    qtbot.waitUntil(lambda: len(recibidos) == 2, timeout=3000)
    assert app.estado.valor is ValorEstado.ACTIVA  # sin reactivar nada
    assert cuenta.cargar() is not None


def test_cuenta_rechazada_muestra_m08_y_borra_la_cuenta(qtbot, app_en_linea_activa):
    app, _, recibidos = app_en_linea_activa(ErrorAutenticacion)
    qtbot.waitUntil(lambda: app.modo.valor is ValorModo.SIN_INTERNET, timeout=3000)
    assert app.ventana.etiqueta_mensaje.text() == textos.MENSAJES["M-08"]
    assert cuenta.cargar() is None
    qtbot.waitUntil(lambda: len(recibidos) == 1, timeout=3000)
