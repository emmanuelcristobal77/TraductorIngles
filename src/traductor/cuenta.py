"""Cuenta del modo en línea: cifrado DPAPI y validación con el servicio (research R-14).

La clave nunca se escribe en la bitácora ni sale del equipo, salvo hacia el propio servicio.
"""

from __future__ import annotations

import ctypes
import json
import re
import socket
import urllib.error
import urllib.request
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from traductor import bitacora
from traductor.ajustes import carpeta_app

TIEMPO_LIMITE_S = 5
HOST_REFERENCIA = "eastus.api.cognitive.microsoft.com"


@dataclass(frozen=True)
class CuentaEnLinea:
    clave: str = field(repr=False)  # nunca se muestra completa
    region: str

    def __post_init__(self) -> None:
        clave = self.clave.strip()
        region = re.sub(r"\s+", "", self.region).lower()
        if not clave or not region:
            raise ValueError("clave y región no pueden estar vacías")
        object.__setattr__(self, "clave", clave)
        object.__setattr__(self, "region", region)


class ResultadoValidacion(Enum):
    VALIDA = "VALIDA"
    INVALIDA = "INVALIDA"
    SIN_RED = "SIN_RED"


# --- DPAPI (alcance del usuario actual) ------------------------------------------------------
class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


_CRYPTPROTECT_UI_FORBIDDEN = 0x1


def _dpapi(datos: bytes, cifrar: bool) -> bytes:
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    buffer = ctypes.create_string_buffer(datos, len(datos))
    entrada = _Blob(len(datos), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    salida = _Blob()
    funcion = crypt32.CryptProtectData if cifrar else crypt32.CryptUnprotectData
    ok = funcion(ctypes.byref(entrada), None, None, None, None, _CRYPTPROTECT_UI_FORBIDDEN,
                 ctypes.byref(salida))
    if not ok:
        raise OSError(ctypes.get_last_error(), "DPAPI")
    try:
        return ctypes.string_at(salida.pbData, salida.cbData)
    finally:
        kernel32.LocalFree(salida.pbData)


def _ruta():
    return carpeta_app() / "cuenta_en_linea.bin"


def guardar(cuenta: CuentaEnLinea) -> None:
    datos = json.dumps({"clave": cuenta.clave, "region": cuenta.region}).encode("utf-8")
    ruta = _ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(_dpapi(datos, cifrar=True))


def cargar() -> CuentaEnLinea | None:
    try:
        datos = json.loads(_dpapi(_ruta().read_bytes(), cifrar=False).decode("utf-8"))
        return CuentaEnLinea(datos["clave"], datos["region"])
    except FileNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001 - archivo dañado o de otro usuario
        bitacora.registrar_error("cuenta", exc)
        return None


def borrar() -> None:
    try:
        _ruta().unlink()
    except FileNotFoundError:
        pass


# --- Validación ------------------------------------------------------------------------------
def _hay_red() -> bool:
    try:
        socket.getaddrinfo(HOST_REFERENCIA, 443)
        return True
    except OSError:
        return False


def validar(cuenta: CuentaEnLinea, urlopen: Callable = urllib.request.urlopen,
            hay_red: Callable[[], bool] = _hay_red) -> ResultadoValidacion:
    """Pide un token al servicio con la clave: 200 válida, 401/403 o región inexistente
    inválida, sin conexión o tiempo agotado sin red."""
    pedido = urllib.request.Request(
        f"https://{cuenta.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
        data=b"", method="POST", headers={"Ocp-Apim-Subscription-Key": cuenta.clave})
    try:
        with urlopen(pedido, timeout=TIEMPO_LIMITE_S) as respuesta:
            return (ResultadoValidacion.VALIDA if respuesta.status == 200
                    else ResultadoValidacion.INVALIDA)
    except urllib.error.HTTPError as exc:
        bitacora.registrar_error("cuenta", exc)
        return ResultadoValidacion.INVALIDA
    except urllib.error.URLError as exc:
        bitacora.registrar_error("cuenta", exc)
        if isinstance(exc.reason, socket.gaierror) and hay_red():
            return ResultadoValidacion.INVALIDA  # la región no existe, pero sí hay internet
        return ResultadoValidacion.SIN_RED
    except (TimeoutError, socket.timeout, OSError) as exc:
        bitacora.registrar_error("cuenta", exc)
        return ResultadoValidacion.SIN_RED
    except Exception as exc:  # noqa: BLE001
        bitacora.registrar_error("cuenta", exc)
        return ResultadoValidacion.SIN_RED if not hay_red() else ResultadoValidacion.INVALIDA
