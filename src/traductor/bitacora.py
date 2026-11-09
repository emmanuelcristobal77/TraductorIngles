"""Bitácora de errores sin contenido (research R-13; supuesto de la spec sobre diagnóstico).

Solo guarda la hora, el componente y el tipo de la excepción. Nunca ``str(exc)``, audio, texto
ni la clave del modo en línea.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path


def ruta_bitacora() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "TraductorIngles" / "errores.log"


def registrar_error(componente: str, exc: BaseException) -> None:
    try:
        ruta = ruta_bitacora()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        linea = f"{datetime.now().isoformat(timespec='seconds')}\t{componente}\t{type(exc).__name__}\n"
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:  # noqa: BLE001 - la bitácora nunca debe tumbar la app
        pass
