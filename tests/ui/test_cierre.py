"""Cerrar la ventana cierra la app; minimizar no detiene nada (T024)."""

import ctypes
import time

import pytest

from traductor.estado import ValorEstado

pytestmark = pytest.mark.spec("RF-004a", "CA-015")

WM_CLOSE = 0x0010


def _app_activa(qtbot, armar_app, canal_falso, motor_falso):
    orden = []
    app = armar_app(salir=lambda: orden.append("quit"))
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.estado.activar()
    assert canal_falso.inicios == [1]

    app.estado.al_cambiar.insert(0, lambda e: orden.append(e.valor.name))
    detener_original = canal_falso.detener

    def detener():
        orden.append("canal.detener")
        detener_original()

    canal_falso.detener = detener
    ocultar_original = app.bandeja.hide
    app.bandeja.hide = lambda: (orden.append("ocultar icono"), ocultar_original())
    app.control.al_cerrar[app.control.al_cerrar.index(ocultar_original)] = app.bandeja.hide
    app.atajo.user32.orden = orden
    motor = motor_falso()
    motor_cerrar = motor.cerrar
    motor.cerrar = lambda: (orden.append("motor.cerrar"), motor_cerrar())
    app.control.motores.append(motor)
    return app, orden


ESPERADO = ["DESACTIVADA", "canal.detener", "ocultar icono", "UnregisterHotKey", "motor.cerrar",
            "quit"]


def test_cerrar_con_la_x_sigue_el_orden(qtbot, armar_app, canal_falso, motor_falso):
    app, orden = _app_activa(qtbot, armar_app, canal_falso, motor_falso)
    inicio = time.monotonic()
    app.ventana.close()
    assert time.monotonic() - inicio < 1.0
    assert orden == ESPERADO
    assert app.estado.valor is ValorEstado.DESACTIVADA
    assert not app.bandeja.isVisible()


def test_alt_f4_cierra_igual(qtbot, armar_app, canal_falso, motor_falso):
    app, orden = _app_activa(qtbot, armar_app, canal_falso, motor_falso)
    hwnd = int(app.ventana.winId())
    ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)  # lo que hace Windows con Alt+F4
    qtbot.waitUntil(lambda: "quit" in orden, timeout=1000)
    assert orden == ESPERADO


def test_minimizar_no_cambia_nada(qtbot, armar_app, canal_falso):
    app = armar_app()
    qtbot.waitUntil(lambda: app.estado._listo, timeout=3000)
    app.estado.activar()
    app.ventana.showMinimized()
    qtbot.wait(50)
    assert app.estado.valor is ValorEstado.ACTIVA
    assert canal_falso.detenciones == 0
    assert app.bandeja.isVisible()
