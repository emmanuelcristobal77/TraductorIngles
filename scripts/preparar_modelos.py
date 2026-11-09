"""Descarga y convierte los modelos que usa TraductorIngles (solo desarrollo, research R-04 y R-05).

Es idempotente: si una carpeta de destino ya existe, no la vuelve a generar.

- Whisper multilingüe ``small`` y ``base`` en formato CTranslate2 (``Systran/faster-whisper-*``).
  Se guardan tal cual y se cuantizan a ``int8`` al cargarlos (``compute_type="int8"``).
- ``Helsinki-NLP/opus-mt-en-es`` convertido a CTranslate2 con ``--quantization int8``, junto con
  ``source.spm`` y ``target.spm``.

Uso: ``python scripts/preparar_modelos.py`` (necesita internet y ``requirements-dev.txt``).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / "modelos"
OPUS = "Helsinki-NLP/opus-mt-en-es"


def _listo(carpeta: Path) -> bool:
    return carpeta.is_dir() and any(carpeta.iterdir())


def descargar_whisper(tamano: str) -> None:
    destino = MODELOS / f"whisper-{tamano}"
    if _listo(destino):
        print(f"[ya existe] {destino.name}")
        return
    from faster_whisper.utils import download_model

    print(f"[descargando] Whisper {tamano}…")
    download_model(tamano, output_dir=str(destino))
    print(f"[listo] {destino.name}")


def convertir_opus() -> None:
    destino = MODELOS / "opus-mt-en-es-ct2"
    if not _listo(destino):
        print("[convirtiendo] OPUS-MT en-es a CTranslate2 int8…")
        convertidor = Path(sys.executable).with_name("ct2-transformers-converter.exe")
        comando = [str(convertidor) if convertidor.exists() else "ct2-transformers-converter",
                   "--model", OPUS, "--output_dir", str(destino), "--quantization", "int8"]
        subprocess.run(comando, check=True)
    else:
        print(f"[ya existe] {destino.name}")

    from huggingface_hub import hf_hub_download

    for nombre in ("source.spm", "target.spm"):
        if not (destino / nombre).exists():
            shutil.copy(hf_hub_download(OPUS, nombre), destino / nombre)
    print(f"[listo] {destino.name}")


def main() -> int:
    MODELOS.mkdir(exist_ok=True)
    descargar_whisper("small")
    descargar_whisper("base")
    convertir_opus()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
