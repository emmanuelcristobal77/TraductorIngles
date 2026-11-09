"""Respaldo sin internet del SelectorMotor (T060, contrato de motores §4 puntos 1 y 2)."""

import numpy as np
import pytest

from traductor.estado import EstadoTraduccion, ValorEstado
from traductor.motores.base import ErrorAutenticacion, ErrorConexion, ErrorPreparacion, Frase
from traductor.motores.selector import SelectorMotor

pytestmark = pytest.mark.spec("RF-015b", "RF-015c", "CA-013")


def frase():
    return Frase(audio=np.zeros(8000, np.float32), t_fin_habla=0.0, sesion=1)


@pytest.mark.parametrize("error, evento", [(ErrorConexion, "conexion_perdida"),
                                           (ErrorAutenticacion, "cuenta_rechazada")])
def test_respaldo_con_la_misma_frase(motor_falso, error, evento):
    local = motor_falso(resultados=["local"])
    en_linea = motor_falso(nombre="EN_LINEA", errores=[error("x")])
    selector = SelectorMotor(local, lambda: en_linea)
    selector.usar_en_linea()
    estado = EstadoTraduccion()
    estado.modelos_listos()
    estado.activar()
    eventos = {"conexion_perdida": [], "cuenta_rechazada": []}
    selector.conexion_perdida.append(lambda: eventos["conexion_perdida"].append(1))
    selector.cuenta_rechazada.append(lambda: eventos["cuenta_rechazada"].append(1))

    f = frase()
    r = selector.traducir(f)
    assert r.texto_es == "local"
    assert local.frases == [f]  # la misma frase, para no perderla
    assert en_linea.cerrado == 1 and selector.en_linea is None
    assert eventos[evento] == [1] and sum(map(len, eventos.values())) == 1
    assert estado.valor is ValorEstado.ACTIVA


def test_en_linea_traduce_mientras_funciona(motor_falso):
    local = motor_falso()
    en_linea = motor_falso(nombre="EN_LINEA", resultados=["remoto"])
    selector = SelectorMotor(local, lambda: en_linea)
    selector.usar_en_linea()
    assert selector.traducir(frase()).texto_es == "remoto"
    assert local.frases == []


def test_error_al_preparar_deja_sin_internet(motor_falso):
    en_linea = motor_falso(nombre="EN_LINEA", error_preparar=ErrorPreparacion("x"))
    selector = SelectorMotor(motor_falso(), lambda: en_linea)
    with pytest.raises(ErrorPreparacion):
        selector.usar_en_linea()
    assert selector.en_linea is None


def test_el_motor_local_nunca_se_cierra(motor_falso):
    local = motor_falso()
    en_linea = motor_falso(nombre="EN_LINEA", errores=[ErrorConexion("x")])
    selector = SelectorMotor(local, lambda: en_linea)
    selector.usar_en_linea()
    selector.traducir(frase())
    selector.usar_local()
    assert local.cerrado == 0
