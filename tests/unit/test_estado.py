"""EstadoTraduccion y ModoProcesamiento (T013, data-model §1 y §2)."""

import pytest

from traductor.estado import EstadoTraduccion, ModoProcesamiento, ValorEstado, ValorModo

pytestmark = pytest.mark.spec("RF-004", "RF-002", "RF-003", "RF-005", "RF-015")


def test_empieza_desactivada_con_sesion_cero():
    estado = EstadoTraduccion()
    assert estado.valor is ValorEstado.DESACTIVADA
    assert estado.sesion == 0


def test_activar_con_modelos_listos_va_a_activa_y_sube_la_sesion():
    estado = EstadoTraduccion()
    estado.modelos_listos()
    estado.activar()
    assert estado.valor is ValorEstado.ACTIVA
    assert estado.sesion == 1


def test_activar_sin_modelos_pasa_por_preparando():
    estado = EstadoTraduccion()
    estado.activar()
    assert estado.valor is ValorEstado.PREPARANDO
    estado.modelos_listos()
    assert estado.valor is ValorEstado.ACTIVA
    assert estado.sesion == 1


@pytest.mark.parametrize("listo", [False, True])
def test_desactivar_desde_preparando_o_activa(listo):
    estado = EstadoTraduccion()
    if listo:
        estado.modelos_listos()
    estado.activar()
    estado.desactivar()
    assert estado.valor is ValorEstado.DESACTIVADA


def test_alternar():
    estado = EstadoTraduccion()
    estado.modelos_listos()
    estado.alternar()
    assert estado.valor is ValorEstado.ACTIVA
    estado.alternar()
    assert estado.valor is ValorEstado.DESACTIVADA
    estado.alternar()
    assert estado.sesion == 2


def test_cada_activacion_sube_la_sesion():
    estado = EstadoTraduccion()
    estado.modelos_listos()
    for esperado in (1, 2, 3):
        estado.activar()
        assert estado.sesion == esperado
        estado.desactivar()


def test_observadores_reciben_cada_cambio():
    estado = EstadoTraduccion()
    vistos = []
    estado.al_cambiar.append(lambda e: vistos.append(e.valor))
    estado.activar()
    estado.modelos_listos()
    estado.desactivar()
    assert vistos == [ValorEstado.PREPARANDO, ValorEstado.ACTIVA, ValorEstado.DESACTIVADA]


def test_preparacion_fallida_vuelve_a_desactivada_y_bloquea_activar():
    estado = EstadoTraduccion()
    avisos = []
    estado.al_fallar_preparacion.append(lambda: avisos.append("M-05"))
    estado.activar()
    estado.preparacion_fallida()
    assert estado.valor is ValorEstado.DESACTIVADA
    assert avisos == ["M-05"]

    estado.activar()
    assert estado.valor is ValorEstado.DESACTIVADA
    assert avisos == ["M-05", "M-05"]
    estado.alternar()
    assert estado.valor is ValorEstado.DESACTIVADA
    assert len(avisos) == 3


def test_modo_empieza_sin_internet_y_cambia():
    modo = ModoProcesamiento()
    vistos = []
    modo.al_cambiar.append(lambda m: vistos.append(m.valor))
    assert modo.valor is ValorModo.SIN_INTERNET
    modo.encender_en_linea()
    assert modo.valor is ValorModo.EN_LINEA
    modo.volver_sin_internet()
    assert modo.valor is ValorModo.SIN_INTERNET
    assert vistos == [ValorModo.EN_LINEA, ValorModo.SIN_INTERNET]


def test_error_del_motor_no_cambia_el_estado(qapp, canal_falso):
    from traductor.app import Controlador

    estado = EstadoTraduccion()
    estado.modelos_listos()
    control = Controlador(estado, canal_falso)
    mensajes = []
    control.al_mensaje.append(mensajes.append)
    estado.activar()
    control.publicar_mensaje("M-04")
    assert estado.valor is ValorEstado.ACTIVA
    assert mensajes == ["M-04"]
