"""Modo en línea: UI-03, UI-04, D-01 y D-02 con mouse y teclado (T061)."""

import threading

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLineEdit

from traductor import cuenta, textos
from traductor.ajustes import Ajustes
from traductor.cuenta import CuentaEnLinea, ResultadoValidacion
from traductor.estado import ValorModo
from traductor.motores.selector import SelectorMotor
from traductor.ui.dialogos import AvisoEnLinea, CuadroCuenta

pytestmark = pytest.mark.spec("RF-015a", "RF-015c", "RF-014", "CA-010", "CA-012", "CA-016")


@pytest.fixture
def app_en_linea(armar_app, motor_falso):
    def armar(aviso=None, cuentas=None):
        """aviso: lista de respuestas de D-01; cuentas: lista de (resultado, cuenta) de D-02."""
        selector = SelectorMotor(motor_falso(), lambda: motor_falso(nombre="EN_LINEA"))
        aplicacion = armar_app(selector=selector)
        aplicacion.llamadas = {"aviso": 0, "cuenta": 0}
        respuestas_aviso = list(aviso or [])
        respuestas_cuenta = list(cuentas or [])

        def pedir_aviso():
            aplicacion.llamadas["aviso"] += 1
            return respuestas_aviso.pop(0)

        def pedir_cuenta():
            aplicacion.llamadas["cuenta"] += 1
            return respuestas_cuenta.pop(0)

        aplicacion.pedir_aviso = pedir_aviso
        aplicacion.pedir_cuenta = pedir_cuenta
        return aplicacion

    return armar


VALIDA = (ResultadoValidacion.VALIDA, CuentaEnLinea("clave", "eastus"))


def ui04_apagado(app):
    casilla = app.ventana.casilla_modo
    return (not casilla.isChecked() and casilla.accessibleName() == textos.UI04_NOMBRE_APAGADO
            and app.ventana.etiqueta_modo.text() == textos.UI03_SIN_INTERNET
            and app.modo.valor is ValorModo.SIN_INTERNET)


def test_al_abrir_dice_sin_internet(app_en_linea):
    app = app_en_linea()
    assert ui04_apagado(app)
    assert app.ventana.casilla_modo.text() == textos.UI04_TEXTO


def _siguiente_con_tab(w):
    w = w.nextInFocusChain()
    while not (w.focusPolicy() & Qt.TabFocus):
        w = w.nextInFocusChain()
    return w


def test_orden_de_tabulacion(app_en_linea):
    v = app_en_linea().ventana
    assert _siguiente_con_tab(v.boton_traduccion) is v.casilla_modo
    assert _siguiente_con_tab(v.casilla_modo) is v.boton_mover


@pytest.mark.parametrize("como", ["mouse", "teclado"])
def test_flujo_completo_con_mouse_o_teclado(qtbot, app_en_linea, appdata_temporal, como):
    app = app_en_linea(aviso=[False, True], cuentas=[(None, None), VALIDA])
    casilla = app.ventana.casilla_modo

    def tocar():
        if como == "mouse":  # clic sobre la casilla misma (el indicador)
            qtbot.mouseClick(casilla, Qt.LeftButton, pos=QPoint(8, casilla.height() // 2))
        else:
            casilla.setFocus()
            qtbot.keyClick(casilla, Qt.Key_Space)

    tocar()  # D-01: "No" → sigue sin internet y el aviso volverá a salir
    assert app.llamadas == {"aviso": 1, "cuenta": 0} and ui04_apagado(app)
    assert Ajustes.cargar().aviso_en_linea_aceptado is False

    tocar()  # D-01: "Sí" → guarda el aviso y abre D-02; cancelar → sin internet, sin mensaje
    assert app.llamadas == {"aviso": 2, "cuenta": 1} and ui04_apagado(app)
    assert Ajustes.cargar().aviso_en_linea_aceptado is True
    assert app.ventana.etiqueta_mensaje.text() == ""

    tocar()  # ya no sale D-01, pero sí D-02 otra vez; cuenta válida → en línea
    assert app.llamadas == {"aviso": 2, "cuenta": 2}
    assert app.modo.valor is ValorModo.EN_LINEA
    assert casilla.isChecked() and casilla.accessibleName() == textos.UI04_NOMBRE_ENCENDIDO
    assert app.ventana.etiqueta_modo.text() == textos.UI03_EN_LINEA
    assert app.ventana.etiqueta_modo.styleSheet() != ""
    assert cuenta.cargar() == VALIDA[1]

    tocar()  # apagar con una sola acción
    assert ui04_apagado(app)

    tocar()  # con la cuenta guardada ya no sale ni D-01 ni D-02
    assert app.llamadas == {"aviso": 2, "cuenta": 2} and app.modo.valor is ValorModo.EN_LINEA


@pytest.mark.parametrize("resultado, mensaje", [(ResultadoValidacion.INVALIDA, "M-08"),
                                                (ResultadoValidacion.SIN_RED, "M-09")])
def test_cuenta_invalida_o_sin_red(qtbot, app_en_linea, appdata_temporal, resultado, mensaje):
    Ajustes(aviso_en_linea_aceptado=True).guardar()
    app = app_en_linea(cuentas=[(resultado, CuentaEnLinea("mala", "eastus")), VALIDA])
    app.ventana.casilla_modo.click()
    assert ui04_apagado(app)
    assert app.ventana.etiqueta_mensaje.text() == textos.MENSAJES[mensaje]
    assert cuenta.cargar() is None  # no se guarda
    app.ventana.casilla_modo.click()
    assert app.llamadas["aviso"] == 0 and app.llamadas["cuenta"] == 2


def test_al_reiniciar_empieza_sin_internet(app_en_linea, appdata_temporal):
    Ajustes(aviso_en_linea_aceptado=True).guardar()
    cuenta.guardar(VALIDA[1])
    app = app_en_linea()
    assert ui04_apagado(app)


# --- Los cuadros, con mouse y teclado ----------------------------------------------------------
def test_d01_foco_en_no_y_esc(qtbot):
    aviso = AvisoEnLinea()
    qtbot.addWidget(aviso)
    assert aviso.text() == textos.MENSAJES["M-01"]
    assert [b.text() for b in aviso.buttons()].count(textos.D01_SI) == 1
    resultado = {}
    aviso.finished.connect(lambda _: resultado.setdefault("si", aviso.acepto()))
    aviso.open()
    qtbot.waitUntil(lambda: aviso.boton_no.hasFocus(), timeout=2000)
    qtbot.keyClick(aviso, Qt.Key_Escape)
    qtbot.waitUntil(lambda: "si" in resultado, timeout=2000)
    assert resultado["si"] is False


@pytest.mark.parametrize("como", ["mouse", "teclado"])
def test_d01_si(qtbot, como):
    aviso = AvisoEnLinea()
    qtbot.addWidget(aviso)
    aviso.open()
    qtbot.waitUntil(lambda: aviso.boton_no.hasFocus(), timeout=2000)
    if como == "mouse":
        qtbot.mouseClick(aviso.boton_si, Qt.LeftButton)
    else:
        qtbot.keyClick(aviso.boton_no, Qt.Key_Tab, Qt.ShiftModifier)
        qtbot.waitUntil(lambda: aviso.boton_si.hasFocus(), timeout=2000)
        qtbot.keyClick(aviso.boton_si, Qt.Key_Return)
    qtbot.waitUntil(lambda: not aviso.isVisible(), timeout=2000)
    assert aviso.acepto() is True


def _cuadro(qtbot, resultado=ResultadoValidacion.VALIDA, bloqueo=None):
    def validar(c):
        if bloqueo:
            bloqueo.wait(5)
        return resultado

    cuadro = CuadroCuenta(validar=validar)
    qtbot.addWidget(cuadro)
    return cuadro


def test_d02_campos_y_nombres(qtbot):
    cuadro = _cuadro(qtbot)
    assert cuadro.clave.echoMode() == QLineEdit.Password
    assert cuadro.clave.accessibleName() == textos.D02_NOMBRE_CLAVE
    assert cuadro.region.accessibleName() == textos.D02_NOMBRE_REGION
    assert cuadro.region.isEditable() and cuadro.region.findText("southcentralus") >= 0
    assert cuadro.explicacion.text() == textos.D02_EXPLICACION
    assert not cuadro.boton_guardar.isEnabled()
    cuadro.clave.setText("abc")
    cuadro.region.setEditText("")
    assert not cuadro.boton_guardar.isEnabled()
    cuadro.region.setEditText("eastus")
    assert cuadro.boton_guardar.isEnabled()


@pytest.mark.parametrize("como", ["mouse", "teclado"])
def test_d02_comprobando_y_valida(qtbot, como):
    bloqueo = threading.Event()
    cuadro = _cuadro(qtbot, bloqueo=bloqueo)
    cuadro.open()
    if como == "mouse":
        qtbot.mouseClick(cuadro.clave, Qt.LeftButton)
        qtbot.keyClicks(cuadro.clave, "clave")
        cuadro.region.setEditText("eastus")
        qtbot.mouseClick(cuadro.boton_guardar, Qt.LeftButton)
    else:
        cuadro.clave.setFocus()
        qtbot.keyClicks(cuadro.clave, "clave")
        qtbot.keyClick(cuadro.clave, Qt.Key_Tab)
        qtbot.keyClick(cuadro.region.lineEdit(), Qt.Key_A, Qt.ControlModifier)
        qtbot.keyClicks(cuadro.region.lineEdit(), "eastus")
        qtbot.keyClick(cuadro.region.lineEdit(), Qt.Key_Return)
    assert cuadro.boton_guardar.text() == textos.D02_COMPROBANDO
    assert not cuadro.boton_guardar.isEnabled()
    bloqueo.set()
    qtbot.waitUntil(lambda: cuadro.resultado is not None, timeout=5000)
    assert cuadro.resultado is ResultadoValidacion.VALIDA
    assert cuadro.cuenta == CuentaEnLinea("clave", "eastus")


def test_d02_cancelar_y_esc(qtbot):
    for accion in ("cancelar", "esc"):
        cuadro = _cuadro(qtbot)
        cuadro.open()
        if accion == "cancelar":
            cuadro.boton_cancelar.click()
        else:
            qtbot.keyClick(cuadro, Qt.Key_Escape)
        qtbot.waitUntil(lambda: not cuadro.isVisible(), timeout=2000)
        assert cuadro.resultado is None
