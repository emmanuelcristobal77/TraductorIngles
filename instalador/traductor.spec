# PyInstaller (onedir) para TraductorIngles. Uso, desde la raíz del repositorio:
#   pyinstaller instalador\traductor.spec
# Genera dist\TraductorIngles\TraductorIngles.exe con todo lo necesario, incluidos los modelos.
# No incluye ningún dato de la persona: ni ajustes, ni cuenta del modo en línea, ni claves.

import os

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

RAIZ = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(RAIZ, "src")
MODELOS = os.path.join(RAIZ, "modelos")
MODELO_WHISPER = "whisper-base"  # elegido en T009 (research R-12)

datos = [
    (os.path.join(SRC, "traductor", "recursos"), os.path.join("traductor", "recursos")),
    (os.path.join(MODELOS, MODELO_WHISPER), os.path.join("modelos", MODELO_WHISPER)),
    (os.path.join(MODELOS, "opus-mt-en-es-ct2"), os.path.join("modelos", "opus-mt-en-es-ct2")),
]
datos += collect_data_files("faster_whisper")  # Silero VAD (assets/*.onnx)

binarios = []
for paquete in ("ctranslate2", "pyaudiowpatch", "azure.cognitiveservices.speech", "onnxruntime"):
    binarios += collect_dynamic_libs(paquete)

a = Analysis(
    [os.path.join(SRC, "traductor", "__main__.py")],
    pathex=[SRC],
    binaries=binarios,
    datas=datos,
    hiddenimports=["comtypes", "comtypes.stream", "pycaw.pycaw", "pyaudiowpatch",
                   "azure.cognitiveservices.speech"],
    excludes=["torch", "transformers", "pytest", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TraductorIngles",
    icon=os.path.join(SRC, "traductor", "recursos", "icono.ico"),
    console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="TraductorIngles")
