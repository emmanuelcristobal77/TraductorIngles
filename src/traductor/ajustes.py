"""Ajustes guardados en ``%APPDATA%\\TraductorIngles\\ajustes.json`` (research R-13).

Un solo dato: ``aviso_en_linea_aceptado``. Si el archivo no existe o está dañado, se usan los
valores por defecto sin mostrar ningún error.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from traductor import bitacora


def carpeta_app() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "TraductorIngles"


@dataclass
class Ajustes:
    aviso_en_linea_aceptado: bool = False

    @staticmethod
    def ruta() -> Path:
        return carpeta_app() / "ajustes.json"

    @classmethod
    def cargar(cls) -> "Ajustes":
        try:
            datos = json.loads(cls.ruta().read_text(encoding="utf-8"))
            valor = datos.get("aviso_en_linea_aceptado", False) if isinstance(datos, dict) else False
            return cls(aviso_en_linea_aceptado=valor if isinstance(valor, bool) else False)
        except Exception:  # noqa: BLE001 - no existe o está dañado: valores por defecto
            return cls()

    def guardar(self) -> None:
        ruta = self.ruta()
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            temporal = ruta.with_suffix(".tmp")
            temporal.write_text(json.dumps({"aviso_en_linea_aceptado": self.aviso_en_linea_aceptado}),
                                encoding="utf-8")
            os.replace(temporal, ruta)  # escritura atómica
        except Exception as exc:  # noqa: BLE001
            bitacora.registrar_error("ajustes", exc)
