"""Flujo captura → segmentador → selector → glosario → Subtitulo (data-model, "Flujo de datos").

Cada flecha entre hilos es una ``queue.Queue`` con tamaño límite; si se llena, se descarta lo
más viejo para mantener la latencia y mostrar siempre lo más reciente. Los resultados se
entregan al hilo de Qt con señales. Solo separa responsabilidades; no agrega comportamiento.
"""

from __future__ import annotations

import queue
import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal

from traductor import bitacora
from traductor.motores.selector import SelectorMotor
from traductor.traduccion.glosario import Glosario
from traductor.ui.subtitulos import Subtitulo

TAM_COLA_AUDIO = 100  # ~10 s de fragmentos de 0.1 s
TAM_COLA_FRASES = 3


def poner_descartando_viejo(cola: queue.Queue, elemento) -> None:
    while True:
        try:
            cola.put_nowait(elemento)
            return
        except queue.Full:
            try:
                cola.get_nowait()
            except queue.Empty:
                pass


def _vaciar(cola: queue.Queue) -> None:
    while True:
        try:
            cola.get_nowait()
        except queue.Empty:
            return


class Canal(QObject):
    subtitulo = Signal(object)  # Subtitulo
    voz = Signal()
    mensaje = Signal(str)

    def __init__(self, selector: SelectorMotor, glosario: Glosario,
                 fabrica_captura: Callable[[Callable[[str], None]], object],
                 fabrica_segmentador: Callable[..., object]) -> None:
        super().__init__()
        self.selector = selector
        self.glosario = glosario
        self.fabrica_captura = fabrica_captura
        self.fabrica_segmentador = fabrica_segmentador
        self.cola_audio: queue.Queue = queue.Queue(maxsize=TAM_COLA_AUDIO)
        self.cola_frases: queue.Queue = queue.Queue(maxsize=TAM_COLA_FRASES)
        self._sesion: int | None = None
        self._parar: threading.Event | None = None
        self._captura = None
        self._hilos: list[threading.Thread] = []
        selector.error_motor.append(self._error_motor)

    def _publicar(self, id_mensaje: str) -> None:
        self.mensaje.emit(id_mensaje)

    def _error_motor(self, exc: Exception) -> None:
        bitacora.registrar_error("motor", exc)
        self._publicar("M-04")

    def iniciar(self, sesion: int) -> None:
        self.detener()
        self._sesion = sesion
        parar = threading.Event()
        self._parar = parar
        segmentador = self.fabrica_segmentador(
            sesion=sesion,
            al_frase=lambda frase: poner_descartando_viejo(self.cola_frases, frase),
            voz_detectada=self.voz.emit)
        self._hilos = [
            threading.Thread(target=self._bucle_segmentador, args=(parar, segmentador),
                             name="segmentador", daemon=True),
            threading.Thread(target=self._bucle_selector, args=(parar, sesion),
                             name="selector", daemon=True),
        ]
        for hilo in self._hilos:
            hilo.start()
        self._captura = self.fabrica_captura(self._publicar)
        self._captura.iniciar(self.cola_audio)

    def _bucle_segmentador(self, parar: threading.Event, segmentador) -> None:
        while not parar.is_set():
            try:
                fragmento = self.cola_audio.get(timeout=0.1)
            except queue.Empty:
                continue
            if parar.is_set():
                return
            try:
                segmentador.procesar(fragmento)
            except Exception as exc:  # noqa: BLE001
                bitacora.registrar_error("segmentador", exc)

    def _bucle_selector(self, parar: threading.Event, sesion: int) -> None:
        while not parar.is_set():
            try:
                frase = self.cola_frases.get(timeout=0.1)
            except queue.Empty:
                continue
            if parar.is_set() or frase.sesion != sesion:
                continue
            resultado = self.selector.traducir(frase)
            if parar.is_set() or self._sesion != sesion:
                return  # la traducción se desactivó a mitad de la frase: se descarta
            if resultado is not None and resultado.texto_es:
                texto = self.glosario.aplicar(resultado.texto_es)
                self.subtitulo.emit(Subtitulo(texto=texto, sesion=sesion, mostrado_en=0.0))

    def detener(self) -> None:
        """Cierra la captura y vacía las colas; regresa en menos de 1 s (CA-004)."""
        self._sesion = None
        if self._parar is not None:
            self._parar.set()
        captura, self._captura = self._captura, None
        if captura is not None:
            try:
                captura.detener()
            except Exception as exc:  # noqa: BLE001
                bitacora.registrar_error("captura", exc)
        _vaciar(self.cola_audio)
        _vaciar(self.cola_frases)
        for hilo in self._hilos:
            hilo.join(timeout=0.2)  # el selector puede seguir a mitad de una frase; su resultado se ignora
        self._hilos = []
        _vaciar(self.cola_audio)
        _vaciar(self.cola_frases)
