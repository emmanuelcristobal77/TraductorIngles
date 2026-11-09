"""SelectorMotor en modo SIN_INTERNET (T035, contrato de motores §4 puntos 3 y 4)."""

import numpy as np
import pytest

from traductor.motores.base import ErrorMotor, Frase
from traductor.motores.selector import SelectorMotor

pytestmark = pytest.mark.spec("RF-013", "RF-015")


def frase(n=1):
    return Frase(audio=np.zeros(8000, np.float32), t_fin_habla=float(n), sesion=1)


def test_sin_internet_nunca_llama_al_motor_en_linea(motor_falso):
    def fabrica():
        raise AssertionError("se llamó al motor en línea")

    selector = SelectorMotor(motor_falso(resultados=["uno", "dos"]), fabrica)
    assert selector.traducir(frase(1)).texto_es == "uno"
    assert selector.traducir(frase(2)).texto_es == "dos"


def test_error_del_motor_local_avisa_y_sigue(motor_falso):
    local = motor_falso(resultados=["sigue"], errores=[ErrorMotor("x"), None])
    selector = SelectorMotor(local, lambda: None)
    errores = []
    selector.error_motor.append(errores.append)
    assert selector.traducir(frase(1)) is None
    assert len(errores) == 1 and isinstance(errores[0], ErrorMotor)
    assert selector.traducir(frase(2)).texto_es == "sigue"
