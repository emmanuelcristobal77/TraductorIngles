"""Corre los pasos automatizables de la validación de uso con la app INSTALADA (quickstart, parte B).

Controla la app real como lo haría una persona: la abre, presiona sus botones, usa Ctrl+Alt+T,
el mouse y las flechas, reproduce audio en inglés por las bocinas y observa la franja de
subtítulos. No toca el modo en línea ni la red.

Pasos que cubre: arranque (CA-003, parte medible), B1, B2, B3, B4 (deja los subtítulos para que
una persona los juzgue), B5, B6 (navegador en pantalla completa), B7, B8, B11a, B12 (video), B13
y B13a. Los demás quedan a mano (ver ``PASOS_A_MANO``).

Mientras corre (unos 7 minutos):
- suena audio en inglés por las bocinas y se silencia el sonido unos segundos (B11a);
- toma el mouse y el teclado, y abre un navegador en pantalla completa;
- cierra la app si está abierta y la vuelve a abrir al final.
No toques el equipo hasta que termine.

Uso: ``python scripts/validar_instalada.py [--salida RUTA.md]``

Sale con código 1 si algún paso automatizado no cumple.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import os
import shutil
import subprocess
import tempfile
import threading
import time
import wave
import winsound
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parent.parent
AUDIOS = RAIZ / "tests" / "fixtures" / "audio"
SALIDA_POR_DEFECTO = RAIZ / "specs" / "001-traductor-subtitulos-v0" / "checklists" / "validacion-automatica.md"
EXE = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "TraductorIngles" / "TraductorIngles.exe"
BITACORA = Path(os.environ["LOCALAPPDATA"]) / "TraductorIngles" / "errores.log"

# Nombres accesibles de la app (src/traductor/textos.py).
BOTON_ACTIVAR = "Activar traducción, atajo Control Alt T"
BOTON_DESACTIVAR = "Desactivar traducción, atajo Control Alt T"
ESTADO_DESACTIVADA = "Traducción desactivada"
ESTADO_ACTIVA = "Traducción activa"
SIN_INTERNET = "Sin internet"
BOTON_MOVER = "Mover subtítulos con las flechas"
INSTRUCCION_MOVER = "Usa las flechas para mover los subtítulos. Enter o Esc para terminar."

META_ARRANQUE_S = 10.0
META_LATENCIA_S = 3.0
META_OCULTAR_S = 1.0
SIN_HABLA_S = 4.0

PASOS_A_MANO = {
    "B4": "Leer la tabla de subtítulos de este reporte (o ver un video real) y juzgar si se entienden al menos 8 de 10 frases.",
    "B9": "Necesita una llamada real con otra persona y un podcast en un reproductor de escritorio.",
    "B10": "Necesita hablar por el micrófono durante una llamada real.",
    "B11": "Necesita conectar y desconectar audífonos durante una llamada.",
    "B12 (llamada)": "La parte con la ventana de una llamada al frente necesita una llamada real.",
    "B14": "Se trata de que una persona pueda usarla solo con el teclado.",
    "B14a": "Se trata de que una persona pueda usarla solo con el mouse.",
    "B15": "Necesita apagar el wifi y desconectar el cable de red.",
    "B16 a B19": "Modo en línea: necesita la clave real, apagar el wifi y la primera vez de la instalación (el script no la gasta).",
    "Personas nuevas (CA-003)": "10 personas que nunca hayan usado la app.",
}

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.WindowFromPoint.argtypes = [wt.POINT]
user32.WindowFromPoint.restype = wt.HWND
user32.GetAncestor.restype = wt.HWND
user32.GetForegroundWindow.restype = wt.HWND

VK_CONTROL, VK_MENU, VK_RETURN, VK_LEFT, VK_F11 = 0x11, 0x12, 0x0D, 0x25, 0x7A
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
SW_MINIMIZE, SW_RESTORE = 6, 9
WM_SYSCOMMAND, SC_CLOSE = 0x0112, 0xF060
GA_ROOT = 2


# --- utilidades de Windows ---------------------------------------------------------------------
def tecla(vk: int) -> None:
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def ctrl_alt_t() -> None:
    for vk in (VK_CONTROL, VK_MENU, ord("T")):
        user32.keybd_event(vk, 0, 0, 0)
    for vk in (ord("T"), VK_MENU, VK_CONTROL):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def clic(x: int, y: int) -> None:
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def arrastrar(desde: tuple[int, int], hasta: tuple[int, int], pasos: int = 25) -> None:
    user32.SetCursorPos(*desde)
    time.sleep(0.15)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    for i in range(1, pasos + 1):
        x = desde[0] + (hasta[0] - desde[0]) * i // pasos
        y = desde[1] + (hasta[1] - desde[1]) * i // pasos
        user32.SetCursorPos(x, y)
        time.sleep(0.02)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def al_frente(hwnd: int) -> None:
    tecla(VK_MENU)  # un Alt libera el bloqueo de primer plano de Windows
    user32.ShowWindow(hwnd, SW_RESTORE) if user32.IsIconic(hwnd) else None
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.4)


def rect_ventana(hwnd: int) -> tuple[int, int, int, int]:
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def ventanas_de(pid: int) -> list[tuple[int, str, bool]]:
    res: list[tuple[int, str, bool]] = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(h, _l):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid:
            c = ctypes.create_unicode_buffer(200)
            user32.GetClassNameW(h, c, 200)
            res.append((h, c.value, bool(user32.IsWindowVisible(h))))
        return True

    user32.EnumWindows(cb, 0)
    return res


def esperar(condicion: Callable[[], bool], limite_s: float, cada_s: float = 0.03) -> float | None:
    """Devuelve los segundos que tardó la condición en cumplirse, o None si no se cumplió."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < limite_s:
        if condicion():
            return time.perf_counter() - t0
        time.sleep(cada_s)
    return None


def duracion_wav(ruta: Path) -> float:
    with wave.open(str(ruta), "rb") as w:
        return w.getnframes() / w.getframerate()


# --- audio -------------------------------------------------------------------------------------
class Audio:
    """Reproduce WAV por la salida predeterminada (como cualquier reproductor de escritorio)."""

    def __init__(self) -> None:
        self.fin: float | None = None
        self._hilo: threading.Thread | None = None

    def frase(self, ruta: Path) -> None:
        """Empieza a reproducir una vez; ``self.fin`` queda con la hora en que terminó."""
        self.fin = None

        def tocar():
            winsound.PlaySound(str(ruta), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            self.fin = time.perf_counter()

        self._hilo = threading.Thread(target=tocar, daemon=True)
        self._hilo.start()

    def esperar_fin(self) -> float:
        assert self._hilo is not None
        self._hilo.join()
        assert self.fin is not None
        return self.fin

    @staticmethod
    def en_bucle(ruta: Path) -> None:
        winsound.PlaySound(str(ruta), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                           | winsound.SND_NODEFAULT)

    @staticmethod
    def parar() -> None:
        winsound.PlaySound(None, 0)


def volumen():
    from pycaw.pycaw import AudioUtilities

    return AudioUtilities.GetSpeakers().EndpointVolume


def pico_salida(durante_s: float) -> float | None:
    """El pico más alto de la salida predeterminada durante un rato (para saber si sigue sonando)."""
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

        medidor = AudioUtilities.GetSpeakers()._dev.Activate(
            IAudioMeterInformation._iid_, CLSCTX_ALL, None).QueryInterface(IAudioMeterInformation)
    except Exception:  # noqa: BLE001 - sin medidor no se puede afirmar nada
        return None
    pico, fin = 0.0, time.perf_counter() + durante_s
    while time.perf_counter() < fin:
        pico = max(pico, medidor.GetPeakValue())
        time.sleep(0.05)
    return pico


# --- la app ------------------------------------------------------------------------------------
class App:
    def __init__(self) -> None:
        import comtypes.client

        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen import UIAutomationClient as U

        self.U = U
        self.uia = comtypes.client.CreateObject(U.CUIAutomation, interface=U.IUIAutomation)
        self.proceso: subprocess.Popen | None = None
        self.pid: int | None = None

    # ventanas
    def abrir(self) -> None:
        self.proceso = subprocess.Popen([str(EXE)])
        self.pid = self.proceso.pid

    def principal(self) -> int | None:
        for h, clase, visible in ventanas_de(self.pid):
            if visible and "QWindowIcon" in clase:
                return h
        return None

    @staticmethod
    def _es_franja(clase: str) -> bool:
        # La franja es una ventana Qt.Tool (clase "Qt…QWindowToolSaveBits"); los tooltips de Qt
        # también empiezan con "QWindowTool" ("…QWindowToolTipSaveBits") y no cuentan.
        return "QWindowTool" in clase and "ToolTip" not in clase

    def franja(self) -> int | None:
        """La franja de subtítulos visible, o None si no se ve."""
        for h, clase, visible in ventanas_de(self.pid):
            if visible and self._es_franja(clase):
                return h
        return None

    def franja_cualquiera(self) -> int | None:
        for h, clase, _visible in ventanas_de(self.pid):
            if self._es_franja(clase):
                return h
        return None

    # UI Automation
    def _elemento(self, nombre: str):
        U = self.U
        cond = self.uia.CreateAndCondition(
            self.uia.CreatePropertyCondition(U.UIA_ProcessIdPropertyId, self.pid),
            self.uia.CreatePropertyCondition(U.UIA_NamePropertyId, nombre))
        try:
            e = self.uia.GetRootElement().FindFirst(U.TreeScope_Descendants, cond)
        except Exception:  # noqa: BLE001 - la ventana puede estar cambiando
            return None
        return e if e else None  # comtypes devuelve un puntero nulo, no None, si no lo encuentra

    def hay(self, nombre: str) -> bool:
        return self._elemento(nombre) is not None

    def presionar(self, nombre: str) -> None:
        e = self._elemento(nombre)
        if e is None:
            raise RuntimeError(f"No encontré el botón «{nombre}»")
        e.GetCurrentPattern(self.U.UIA_InvokePatternId).QueryInterface(
            self.U.IUIAutomationInvokePattern).Invoke()

    def centro(self, nombre: str) -> tuple[int, int]:
        r = self._elemento(nombre).CurrentBoundingRectangle
        return (r.left + r.right) // 2, (r.top + r.bottom) // 2

    def texto_franja(self) -> list[str]:
        h = self.franja()
        if not h:
            return []
        U = self.U
        try:
            el = self.uia.ElementFromHandle(h)
            todos = el.FindAll(U.TreeScope_Descendants,
                               self.uia.CreatePropertyCondition(U.UIA_ControlTypePropertyId, U.UIA_TextControlTypeId))
            return [todos.GetElement(i).CurrentName for i in range(todos.Length)
                    if todos.GetElement(i).CurrentName]
        except Exception:  # noqa: BLE001
            return []

    def subtitulo(self) -> str:
        return next((t for t in self.texto_franja() if t != INSTRUCCION_MOVER), "")

    def cerrar_abiertas(self) -> None:
        """Cierra cualquier TraductorIngles abierto antes de empezar."""
        salida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq TraductorIngles.exe", "/FO", "CSV", "/NH"],
                                capture_output=True, text=True).stdout
        for linea in salida.splitlines():
            partes = [p.strip('"') for p in linea.split('","')]
            if len(partes) > 1 and partes[1].isdigit():
                pid = int(partes[1])
                for h, clase, visible in ventanas_de(pid):
                    if visible and "QWindowIcon" in clase:
                        user32.PostMessageW(h, WM_SYSCOMMAND, SC_CLOSE, 0)
                fin = time.perf_counter() + 5
                while time.perf_counter() < fin and _vive(pid):
                    time.sleep(0.1)
                if _vive(pid):
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)


def _vive(pid: int) -> bool:
    h = kernel32.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    codigo = wt.DWORD()
    kernel32.GetExitCodeProcess(h, ctypes.byref(codigo))
    kernel32.CloseHandle(h)
    return codigo.value == 259  # STILL_ACTIVE


class Navegador:
    """Una ventana nueva del navegador en pantalla completa, con perfil propio y temporal."""

    def __init__(self) -> None:
        candidatos = [Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
                      Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
                      Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
                      Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe"]
        self.exe = next((c for c in candidatos if c.exists()), None)
        self.perfil = tempfile.mkdtemp(prefix="traductor-validacion-")
        self.proceso: subprocess.Popen | None = None
        self.titulo = "ValidacionTraductor"

    @property
    def nombre(self) -> str:
        return self.exe.stem if self.exe else "ninguno"

    def abrir(self) -> int | None:
        if not self.exe:
            return None
        pagina = (f"data:text/html,<title>{self.titulo}</title>"
                  "<body style='margin:0;background:%23203040'></body>")
        self.proceso = subprocess.Popen([str(self.exe), f"--user-data-dir={self.perfil}", "--no-first-run",
                                         "--no-default-browser-check", "--start-fullscreen", "--new-window", pagina])
        hwnd = None

        def encontrada():
            nonlocal hwnd
            hwnd = _ventana_con_titulo(self.titulo)
            return hwnd is not None

        esperar(encontrada, 20, 0.2)
        if hwnd:
            al_frente(hwnd)
            time.sleep(1.5)
        return hwnd

    def cerrar(self) -> None:
        if self.proceso:
            subprocess.run(["taskkill", "/PID", str(self.proceso.pid), "/T", "/F"], capture_output=True)
            self.proceso = None
        time.sleep(1)
        shutil.rmtree(self.perfil, ignore_errors=True)


def _ventana_con_titulo(prefijo: str) -> int | None:
    res = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(h, _l):
        t = ctypes.create_unicode_buffer(200)
        user32.GetWindowTextW(h, t, 200)
        if t.value.startswith(prefijo) and user32.IsWindowVisible(h):
            res.append(h)
        return True

    user32.EnumWindows(cb, 0)
    return res[0] if res else None


def captura(ruta: Path) -> None:
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication([])
    app.primaryScreen().grabWindow(0).save(str(ruta))


# --- reporte -----------------------------------------------------------------------------------
@dataclass
class Resultado:
    paso: str
    criterio: str
    cumple: bool | None  # None: lo juzga una persona
    observacion: str


@dataclass
class Reporte:
    resultados: list[Resultado] = field(default_factory=list)
    subtitulos: list[tuple[str, str, str, str]] = field(default_factory=list)
    capturas: list[Path] = field(default_factory=list)

    def anotar(self, paso: str, criterio: str, cumple: bool | None, observacion: str) -> None:
        self.resultados.append(Resultado(paso, criterio, cumple, observacion))
        marca = {True: "CUMPLE", False: "NO CUMPLE", None: "A JUICIO"}[cumple]
        print(f"[{marca}] {paso}: {observacion}", flush=True)


def _fila(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " ")


def escribir_reporte(rep: Reporte, ruta: Path, inicio: datetime) -> None:
    lineas = [
        "# Validación automática con la app instalada",
        "",
        "Generado por `scripts/validar_instalada.py`. Cubre la parte mecánica de los pasos del",
        "[quickstart](../quickstart.md) (parte B); lo que necesita a una persona está al final.",
        "",
        f"**Fecha**: {inicio:%Y-%m-%d %H:%M} | **Ejecutable**: `{EXE}`",
        "",
        "## Resultados",
        "",
        "| Paso | Criterio | Resultado | Observación |",
        "|---|---|---|---|",
    ]
    for r in rep.resultados:
        res = {True: "Cumple", False: "**No cumple**", None: "A juicio de una persona"}[r.cumple]
        lineas.append(f"| {r.paso} | {r.criterio} | {res} | {_fila(r.observacion)} |")
    lineas += ["", "## Subtítulos de las 10 frases (para juzgar B4)", "",
               "Juzga si el subtítulo transmite el sentido de la frase en inglés. Meta: 8 de 10.", "",
               "| Frase | En inglés | Subtítulo | Latencia |", "|---|---|---|---|"]
    for archivo, ingles, sub, lat in rep.subtitulos:
        lineas.append(f"| {archivo} | {_fila(ingles)} | {_fila(sub) or '(ninguno)'} | {lat} |")
    if rep.capturas:
        lineas += ["", "## Capturas", ""] + [f"- `{c}`" for c in rep.capturas]
    lineas += ["", "## Quedan a mano", "", "| Paso | Por qué |", "|---|---|"]
    lineas += [f"| {p} | {m} |" for p, m in PASOS_A_MANO.items()]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


# --- pasos -------------------------------------------------------------------------------------
def leer_frases() -> list[tuple[Path, str]]:
    filas = (AUDIOS / "en_frases.tsv").read_text(encoding="utf-8").splitlines()[1:]
    return [(AUDIOS / f.split("\t")[0], f.split("\t")[2]) for f in filas if f.strip()]


def esperar_franja_oculta(app: App, limite_s: float = 15) -> bool:
    return esperar(lambda: app.franja() is None, limite_s) is not None


def medir_frase(app: App, audio: Audio, ruta: Path) -> tuple[float | None, str]:
    """Reproduce una frase; devuelve la latencia desde que termina hasta que sale el subtítulo."""
    esperar_franja_oculta(app)
    audio.frase(ruta)
    t_visible = None
    textos: list[str] = []
    limite = time.perf_counter() + duracion_wav(ruta) + 10
    while time.perf_counter() < limite:
        if app.franja():
            if t_visible is None:
                t_visible = time.perf_counter()
            t = app.subtitulo()
            if t and t not in textos:
                textos.append(t)
        elif t_visible is not None and audio.fin is not None:
            break
        time.sleep(0.03)
    fin = audio.esperar_fin()
    if t_visible is None:
        return None, ""
    return max(0.0, t_visible - fin), " / ".join(textos)


def paso_arranque_y_b1(app: App, rep: Reporte) -> bool:
    app.cerrar_abiertas()
    t0 = time.perf_counter()
    app.abrir()
    lista = esperar(lambda: app.hay(BOTON_ACTIVAR), 60, 0.05)
    if lista is None:
        rep.anotar("Arranque", "CA-003", False, "La app no mostró «Activar traducción» en 60 s.")
        return False
    dt = time.perf_counter() - t0
    rep.anotar("Arranque", "CA-003 (parte medible)", dt < META_ARRANQUE_S,
               f"Lista para activar en {dt:.1f} s (meta < {META_ARRANQUE_S:.0f} s; no es arranque en frío).")
    ok = app.hay(ESTADO_DESACTIVADA) and app.hay(SIN_INTERNET)
    rep.anotar("B1", "RF-001, CA-012", ok,
               "Dice «Traducción desactivada» y «Sin internet»." if ok
               else "No aparecen «Traducción desactivada» y «Sin internet».")
    return True


def paso_b2(app: App, rep: Reporte) -> None:
    Audio.en_bucle(AUDIOS / "en_continuo.wav")
    vistos: list[str] = []
    fin = time.perf_counter() + 60
    while time.perf_counter() < fin:
        h = app.franja()
        if h:
            vistos.append(f"{h:#x} {rect_ventana(h)} «{app.subtitulo()}»")
        time.sleep(0.1)
    Audio.parar()
    rep.anotar("B2", "CA-007", not vistos,
               "60 s de habla en inglés sin activar: no apareció ningún subtítulo." if not vistos
               else f"Apareció la franja sin activar la traducción ({len(vistos)} lecturas; primera: {vistos[0]}).")


def paso_b3(app: App, rep: Reporte) -> bool:
    app.presionar(BOTON_ACTIVAR)
    dt = esperar(lambda: app.hay(ESTADO_ACTIVA) and app.hay(BOTON_DESACTIVAR), 60, 0.1)
    rep.anotar("B3", "RF-002, RF-005", dt is not None,
               f"Botón «Desactivar traducción» y estado «Traducción activa» a los {dt:.1f} s." if dt is not None
               else "No pasó a «Traducción activa» en 60 s.")
    return dt is not None


def paso_b4_b5(app: App, audio: Audio, rep: Reporte) -> None:
    latencias = []
    for ruta, ingles in leer_frases():
        lat, texto = medir_frase(app, audio, ruta)
        latencias.append(lat)
        rep.subtitulos.append((ruta.name, ingles, texto, "sin subtítulo" if lat is None else f"{lat:.1f} s"))
        print(f"    {ruta.name}: {'-' if lat is None else f'{lat:.1f} s'}  {texto}", flush=True)
    con_sub = sum(1 for x in latencias if x is not None)
    a_tiempo = sum(1 for x in latencias if x is not None and x <= META_LATENCIA_S)
    rep.anotar("B4", "CA-001", None,
               f"Salieron subtítulos en {con_sub} de 10 frases; la tabla de abajo es para juzgar si se entienden 8 de 10.")
    rep.anotar("B5", "CA-002", a_tiempo >= 9,
               f"{a_tiempo} de 10 subtítulos salieron en {META_LATENCIA_S:.0f} s o menos tras el fin de la frase "
               f"(meta: 9 de 10). Latencias: " + ", ".join("-" if x is None else f"{x:.1f}" for x in latencias) + ".")


def paso_b6(app: App, rep: Reporte, carpeta: Path) -> None:
    nav = Navegador()
    try:
        hwnd = nav.abrir()
        if not hwnd:
            rep.anotar("B6", "CA-006", False, "No pude abrir Chrome ni Edge en pantalla completa.")
            return
        Audio.en_bucle(AUDIOS / "en_continuo.wav")
        visible = esperar(lambda: app.franja() is not None, 20) is not None
        franja = app.franja()
        encima = False
        if visible and franja:
            l, t, r, b = rect_ventana(franja)
            arriba = user32.GetAncestor(user32.WindowFromPoint(wt.POINT((l + r) // 2, (t + b) // 2)), GA_ROOT)
            encima = arriba == franja
            ruta = carpeta / "b6_pantalla_completa.png"
            captura(ruta)
            rep.capturas.append(ruta)
        nl, nt, nr, nb = rect_ventana(hwnd)
        sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        completa = nl <= 0 and nt <= 0 and nr >= sw and nb >= sh
        rep.anotar("B6", "CA-006", visible and encima and completa,
                   f"{nav.nombre} en pantalla completa ({'sí' if completa else 'no'}); franja visible "
                   f"({'sí' if visible else 'no'}) y encima del navegador ({'sí' if encima else 'no'}). "
                   "Con apps de la Microsoft Store no aplica (fuera de alcance).")
    finally:
        Audio.parar()
        nav.cerrar()


def paso_b7(app: App, audio: Audio, rep: Reporte) -> None:
    esperar_franja_oculta(app)
    ruta = AUDIOS / "en_pausa.wav"
    d1 = duracion_wav(AUDIOS / "en_frase_01.wav")
    t0 = time.perf_counter()
    audio.frase(ruta)
    eventos = []  # (segundos desde el inicio, visible)
    previo = False
    while audio.fin is None or time.perf_counter() - audio.fin < 6:
        ahora = app.franja() is not None
        if ahora != previo:
            eventos.append((time.perf_counter() - t0, ahora))
            previo = ahora
        time.sleep(0.03)
    audio.esperar_fin()
    pausa_ini, pausa_fin = d1, d1 + 10.0
    antes = any(v for s, v in eventos if s < pausa_ini + META_LATENCIA_S)
    ocultos = [s for s, v in eventos if not v and pausa_ini <= s < pausa_fin]
    nuevos_en_pausa = [s for s, v in eventos if v and ocultos and ocultos[0] < s < pausa_fin]
    despues = any(v for s, v in eventos if s >= pausa_fin)
    ok = antes and bool(ocultos) and not nuevos_en_pausa and despues
    desc = ", ".join(f"{s:.1f} s {'aparece' if v else 'desaparece'}" for s, v in eventos)
    rep.anotar("B7", "Historia 2", ok,
               f"Frase, 10 s de pausa (de {pausa_ini:.1f} a {pausa_fin:.1f} s) y otra frase. Eventos: {desc}. "
               f"En la pausa el subtítulo se va tras {SIN_HABLA_S:.0f} s sin habla y no salen nuevos.")


def paso_b8(app: App, rep: Reporte) -> None:
    principal = app.principal()
    Audio.en_bucle(AUDIOS / "en_continuo.wav")
    try:
        if esperar(lambda: app.franja() is not None, 20) is None:
            rep.anotar("B8", "RF-009", False, "No apareció la franja para arrastrarla.")
            return
        franja = app.franja()
        l, t, r, b = rect_ventana(franja)
        sh = user32.GetSystemMetrics(1)
        desde = ((l + r) // 2, (t + b) // 2)
        hasta = (desde[0], (b - t) // 2 + 20)
        arrastrar(desde, hasta)
        time.sleep(1.5)
        l2, t2, _, _ = rect_ventana(franja)
        arrastre_ok = t2 < sh // 4 and abs(l2 - l) <= 5
    finally:
        Audio.parar()
    # Modo de mover con el teclado (después de presionar el botón, como una persona).
    al_frente(principal)
    clic(*app.centro(BOTON_MOVER))
    resaltada = esperar(lambda: INSTRUCCION_MOVER in app.texto_franja(), 3) is not None
    l3, t3, _, _ = rect_ventana(app.franja_cualquiera())
    for _ in range(5):
        tecla(VK_LEFT)
        time.sleep(0.15)
    tecla(VK_RETURN)
    time.sleep(1.5)
    l4, t4, _, _ = rect_ventana(app.franja_cualquiera())
    termino = INSTRUCCION_MOVER not in app.texto_franja()
    flechas_ok = l4 < l3 - 50 and abs(t4 - t3) <= 5
    rep.anotar("B8", "RF-009", arrastre_ok and resaltada and flechas_ok and termino,
               f"Arrastre con el mouse: de y={t} a y={t2} ({'se quedó' if arrastre_ok else 'no se quedó'} arriba). "
               f"Mover subtítulos: instrucción visible ({'sí' if resaltada else 'no'}); 5 flechas a la izquierda "
               f"la movieron de x={l3} a x={l4}; Enter terminó el modo ({'sí' if termino else 'no'}).")


def paso_b11a(app: App, rep: Reporte) -> None:
    ep = volumen()
    lineas_antes = _lineas_bitacora()
    Audio.en_bucle(AUDIOS / "en_continuo.wav")
    try:
        sonando = esperar(lambda: app.franja() is not None, 20) is not None
        ep.SetMute(1, None)
        t_mute = time.perf_counter()
        oculto = esperar(lambda: app.franja() is None, SIN_HABLA_S + 4)
        nuevos = 0
        while time.perf_counter() - t_mute < 12:
            if app.franja():
                nuevos += 1
            time.sleep(0.1)
        sigue_activa = app.hay(ESTADO_ACTIVA)
    finally:
        ep.SetMute(0, None)
    regreso = esperar(lambda: app.franja() is not None, 15)
    Audio.parar()
    errores = _lineas_bitacora() - lineas_antes
    ok = sonando and oculto is not None and nuevos == 0 and sigue_activa and regreso is not None and errores == 0
    rep.anotar("B11a", "Caso límite (salida en silencio)", ok,
               f"Con el sonido de Windows en silencio, el subtítulo se fue a los "
               f"{'-' if oculto is None else f'{oculto:.1f}'} s y no salieron nuevos en 12 s; la traducción siguió "
               f"activa ({'sí' if sigue_activa else 'no'}) y la bitácora no registró errores ({errores} nuevos). "
               f"Al quitar el silencio volvieron a los {'-' if regreso is None else f'{regreso:.1f}'} s.")


def paso_b13(app: App, rep: Reporte) -> None:
    ep = volumen()
    vol_antes, mute_antes = ep.GetMasterVolumeLevelScalar(), ep.GetMute()
    Audio.en_bucle(AUDIOS / "en_continuo.wav")
    try:
        esperar(lambda: app.franja() is not None, 20)
        app.presionar(BOTON_DESACTIVAR)
        dt = esperar(lambda: app.franja() is None, 5, 0.01)
        time.sleep(0.5)
        pico = pico_salida(1.0)
    finally:
        Audio.parar()
    igual = abs(ep.GetMasterVolumeLevelScalar() - vol_antes) < 0.01 and ep.GetMute() == mute_antes
    suena = pico is None or pico > 0.001
    ok = dt is not None and dt < META_OCULTAR_S and igual and suena
    rep.anotar("B13", "CA-004, CA-008", ok,
               f"Al presionar «Desactivar traducción» la franja se fue en "
               f"{'-' if dt is None else f'{dt * 1000:.0f} ms'} (meta < 1 s). El volumen y el silencio de Windows no "
               f"cambiaron ({'sí' if igual else 'no'}); el audio siguió sonando "
               f"({'pico ' + f'{pico:.2f}' if pico is not None else 'sin medidor'}).")


def paso_b12(app: App, audio: Audio, rep: Reporte) -> None:
    if not app.hay(ESTADO_DESACTIVADA):
        app.presionar(BOTON_DESACTIVAR)
        esperar(lambda: app.hay(ESTADO_DESACTIVADA), 5)
    nav = Navegador()
    try:
        hwnd = nav.abrir()
        if not hwnd:
            rep.anotar("B12 (video)", "CA-014", False, "No pude abrir Chrome ni Edge en pantalla completa.")
            return
        frente = user32.GetForegroundWindow()
        ctrl_alt_t()
        activa = esperar(lambda: app.hay(ESTADO_ACTIVA), 60, 0.1) is not None
        latencias = []
        for ruta, _ in leer_frases()[:3]:
            lat, _texto = medir_frase(app, audio, ruta)
            latencias.append(lat)
            if lat is not None and lat <= META_LATENCIA_S:
                break
        al_salir = None
        Audio.en_bucle(AUDIOS / "en_continuo.wav")
        if esperar(lambda: app.franja() is not None, 20) is not None:
            ctrl_alt_t()
            al_salir = esperar(lambda: app.franja() is None, 5, 0.01)
        Audio.parar()
        mismo_frente = user32.GetForegroundWindow() == frente == hwnd
        primera = next((x for x in latencias if x is not None and x <= META_LATENCIA_S), None)
        ok = activa and primera is not None and al_salir is not None and al_salir < META_OCULTAR_S and mismo_frente
        rep.anotar("B12 (video)", "CA-014", ok,
                   f"Con {nav.nombre} en pantalla completa al frente: Ctrl+Alt+T activó la traducción "
                   f"({'sí' if activa else 'no'}); latencias de las frases: "
                   + ", ".join("-" if x is None else f"{x:.1f} s" for x in latencias)
                   + f". Ctrl+Alt+T otra vez: la franja se fue en "
                   f"{'-' if al_salir is None else f'{al_salir * 1000:.0f} ms'}. El navegador siguió al frente "
                   f"({'sí' if mismo_frente else 'no'}).")
    finally:
        Audio.parar()
        nav.cerrar()


def paso_b13a(app: App, rep: Reporte) -> None:
    if not app.hay(ESTADO_ACTIVA):
        app.presionar(BOTON_ACTIVAR)
        esperar(lambda: app.hay(ESTADO_ACTIVA), 60, 0.1)
    principal = app.principal()
    user32.ShowWindow(principal, SW_MINIMIZE)
    time.sleep(1)
    Audio.en_bucle(AUDIOS / "en_continuo.wav")
    try:
        sigue = esperar(lambda: app.franja() is not None, 20) is not None
        user32.ShowWindow(principal, SW_RESTORE)
        time.sleep(1)
        esperar(lambda: app.franja() is not None, 10)
        user32.PostMessageW(principal, WM_SYSCOMMAND, SC_CLOSE, 0)  # lo mismo que la X
        t0 = time.perf_counter()
        franja_fuera = None
        while time.perf_counter() - t0 < 10 and _vive(app.pid):
            if franja_fuera is None and app.franja() is None:
                franja_fuera = time.perf_counter() - t0
            time.sleep(0.01)
        proceso_fuera = None if _vive(app.pid) else time.perf_counter() - t0
        if franja_fuera is None:
            franja_fuera = proceso_fuera
    finally:
        Audio.parar()
    ok = (sigue and franja_fuera is not None and franja_fuera < META_OCULTAR_S
          and proceso_fuera is not None and proceso_fuera < META_OCULTAR_S)
    rep.anotar("B13a", "CA-015", ok,
               f"Minimizada, los subtítulos siguieron saliendo ({'sí' if sigue else 'no'}). Al cerrar con la X: "
               f"la franja se fue en {'-' if franja_fuera is None else f'{franja_fuera * 1000:.0f} ms'} y la app "
               f"(con su ícono) terminó en {'-' if proceso_fuera is None else f'{proceso_fuera * 1000:.0f} ms'} "
               "(meta < 1 s).")


def _lineas_bitacora() -> int:
    try:
        return len(BITACORA.read_text(encoding="utf-8").splitlines())
    except OSError:
        return 0


def preparar_volumen() -> str | None:
    ep = volumen()
    if ep.GetMute():
        return "El sonido de Windows está en silencio. Quita el silencio y vuelve a correr el script."
    if ep.GetMasterVolumeLevelScalar() < 0.1:
        return "El volumen de Windows está casi en cero. Súbelo (al menos 20 %) y vuelve a correr el script."
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO)
    args = parser.parse_args()

    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # coordenadas físicas en todas las llamadas
    if not EXE.exists():
        print(f"No encontré la app instalada en {EXE}.")
        return 2
    problema = preparar_volumen()
    if problema:
        print(problema)
        return 2

    inicio = datetime.now()
    carpeta = Path(tempfile.gettempdir()) / f"TraductorIngles-validacion-{inicio:%Y%m%d-%H%M%S}"
    carpeta.mkdir(parents=True, exist_ok=True)
    rep = Reporte()
    app = App()
    audio = Audio()
    print("Validando la app instalada. No uses el mouse ni el teclado hasta que termine.", flush=True)
    try:
        if paso_arranque_y_b1(app, rep):
            paso_b2(app, rep)
            if paso_b3(app, rep):
                paso_b4_b5(app, audio, rep)
                paso_b6(app, rep, carpeta)
                paso_b7(app, audio, rep)
                paso_b8(app, rep)
                paso_b11a(app, rep)
                paso_b13(app, rep)
                paso_b12(app, audio, rep)
                paso_b13a(app, rep)
    except Exception as exc:  # noqa: BLE001 - el reporte se escribe aunque un paso truene
        rep.anotar("Script", "-", False, f"El script se detuvo: {type(exc).__name__}: {exc}")
        raise
    finally:
        Audio.parar()
        try:
            volumen().SetMute(0, None)
        except Exception:  # noqa: BLE001
            pass
        escribir_reporte(rep, args.salida, inicio)
        print(f"\nReporte: {args.salida}", flush=True)
        if app.pid is None or not _vive(app.pid):
            subprocess.Popen([str(EXE)])  # la deja abierta, como estaba al empezar
    return 0 if all(r.cumple is not False for r in rep.resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
