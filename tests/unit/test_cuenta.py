"""Cuenta del modo en línea: DPAPI real y validación simulada (T058, research R-14)."""

import os
import socket
import urllib.error
from pathlib import Path

import pytest

from traductor import bitacora, cuenta
from traductor.cuenta import CuentaEnLinea, ResultadoValidacion

pytestmark = pytest.mark.spec("RF-015a", "RF-015c")

CLAVE = "clave-secreta-0123456789abcdef"


def _archivo() -> Path:
    return Path(os.environ["APPDATA"]) / "TraductorIngles" / "cuenta_en_linea.bin"


def test_guardar_y_cargar_con_dpapi(appdata_temporal):
    cuenta.guardar(CuentaEnLinea(CLAVE, "southcentralus"))
    assert cuenta.cargar() == CuentaEnLinea(CLAVE, "southcentralus")


def test_el_archivo_no_tiene_la_clave_en_texto_plano(appdata_temporal):
    cuenta.guardar(CuentaEnLinea(CLAVE, "eastus"))
    datos = _archivo().read_bytes()
    assert CLAVE.encode() not in datos and CLAVE.encode("utf-16-le") not in datos


def test_region_normalizada_y_campos_vacios(appdata_temporal):
    assert CuentaEnLinea(" k ", " South Central US ").region == "southcentralus"
    with pytest.raises(ValueError):
        CuentaEnLinea("", "eastus")
    with pytest.raises(ValueError):
        CuentaEnLinea("k", "  ")


def test_cargar_sin_archivo_o_danado_da_none(appdata_temporal):
    assert cuenta.cargar() is None
    _archivo().parent.mkdir(parents=True, exist_ok=True)
    _archivo().write_bytes(b"basura")
    assert cuenta.cargar() is None


class Respuesta:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_validacion_hace_el_post_correcto():
    pedidos = []

    def urlopen(req, timeout):
        pedidos.append((req, timeout))
        return Respuesta()

    assert cuenta.validar(CuentaEnLinea(CLAVE, "eastus"), urlopen=urlopen) is ResultadoValidacion.VALIDA
    req, timeout = pedidos[0]
    assert req.full_url == "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    assert req.get_method() == "POST"
    assert req.get_header("Ocp-apim-subscription-key") == CLAVE
    assert timeout == 5


@pytest.mark.parametrize("codigo", [401, 403])
def test_401_o_403_es_invalida(codigo):
    def urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, codigo, "x", {}, None)

    assert cuenta.validar(CuentaEnLinea(CLAVE, "eastus"), urlopen=urlopen) is ResultadoValidacion.INVALIDA


def _dns_falla(req, timeout):
    raise urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))


def test_region_inexistente_es_invalida():
    r = cuenta.validar(CuentaEnLinea(CLAVE, "marte"), urlopen=_dns_falla, hay_red=lambda: True)
    assert r is ResultadoValidacion.INVALIDA


@pytest.mark.parametrize("error", [urllib.error.URLError("sin red"), TimeoutError("lento"),
                                   socket.timeout("lento")])
def test_sin_red_o_tiempo_agotado(error):
    def urlopen(req, timeout):
        raise error

    r = cuenta.validar(CuentaEnLinea(CLAVE, "eastus"), urlopen=urlopen, hay_red=lambda: False)
    assert r is ResultadoValidacion.SIN_RED


def test_dns_falla_y_no_hay_red_es_sin_red():
    r = cuenta.validar(CuentaEnLinea(CLAVE, "eastus"), urlopen=_dns_falla, hay_red=lambda: False)
    assert r is ResultadoValidacion.SIN_RED


def test_borrar(appdata_temporal):
    cuenta.guardar(CuentaEnLinea(CLAVE, "eastus"))
    cuenta.borrar()
    assert not _archivo().exists() and cuenta.cargar() is None
    cuenta.borrar()  # sin archivo no falla


def test_la_clave_nunca_va_a_la_bitacora(appdata_temporal):
    def urlopen(req, timeout):
        raise RuntimeError(f"falla con {CLAVE}")

    cuenta.validar(CuentaEnLinea(CLAVE, "eastus"), urlopen=urlopen, hay_red=lambda: True)
    log = bitacora.ruta_bitacora()
    assert not log.exists() or CLAVE not in log.read_text(encoding="utf-8")
