"""La app no escucha nada hasta que la persona activa la traducción (T025)."""

import winreg

import pytest

from traductor.app import Controlador
from traductor.estado import EstadoTraduccion

pytestmark = pytest.mark.spec("RF-004", "CA-007")


def test_sin_activar_no_inicia_el_canal(qtbot, canal_falso):
    estado = EstadoTraduccion()
    control = Controlador(estado, canal_falso)
    control.iniciar_carga()
    qtbot.waitUntil(lambda: estado._listo, timeout=3000)
    # 60 s simulados sin activar: no hay ningún temporizador que inicie el canal por su cuenta.
    for _ in range(60):
        qtbot.wait(1)
    assert canal_falso.inicios == []


def test_activar_inicia_con_la_sesion_y_desactivar_detiene(qtbot, canal_falso):
    estado = EstadoTraduccion()
    estado.modelos_listos()
    Controlador(estado, canal_falso)
    estado.activar()
    assert canal_falso.inicios == [1]
    estado.desactivar()
    assert canal_falso.detenciones == 1
    estado.activar()
    assert canal_falso.inicios == [1, 2]


def test_main_no_registra_arranque_automatico(qtbot, monkeypatch, appdata_temporal):
    escrituras = []
    for nombre in ("SetValueEx", "SetValue", "CreateKey", "CreateKeyEx"):
        original = getattr(winreg, nombre)
        monkeypatch.setattr(winreg, nombre,
                            lambda *a, _n=nombre, _o=original: escrituras.append((_n, a)))

    from traductor import app as modulo_app

    aplicacion = modulo_app.Aplicacion(preparar=lambda: None, salir=lambda: None)
    qtbot.addWidget(aplicacion.ventana)
    qtbot.addWidget(aplicacion.franja)
    aplicacion.arrancar()
    aplicacion.control.cerrar_app()
    assert escrituras == []
    inicio = appdata_temporal / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    assert not inicio.exists()
