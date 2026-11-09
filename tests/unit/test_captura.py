"""Captura WASAPI loopback con pyaudiowpatch y pycaw simulados (T031)."""

import queue
import types

import numpy as np
import pytest

from traductor.audio.captura import CapturaLoopback, FragmentoAudio, LectorVolumen, convertir

pytestmark = pytest.mark.spec("RF-004", "RF-006", "RF-010", "RF-011", "CA-008", "CA-009")

PA_INT16, PA_FLOAT32 = 8, 1


class StreamFalso:
    def __init__(self, dispositivo, formato):
        self.dispositivo = dispositivo
        self.formato = formato
        self.disponibles = []  # bloques de bytes que "llegan"
        self.cerrado = False
        self.falla = False

    def get_read_available(self):
        if self.falla:
            raise OSError("se desconectó")
        return 0 if not self.disponibles else len(self.disponibles[0]) // self._bytes_por_cuadro()

    def _bytes_por_cuadro(self):
        return self.dispositivo["maxInputChannels"] * (2 if self.formato == PA_INT16 else 4)

    def read(self, n, exception_on_overflow=True):
        if self.falla:
            raise OSError("se desconectó")
        return self.disponibles.pop(0)

    def stop_stream(self):
        pass

    def close(self):
        self.cerrado = True


class PyAudioFalso:
    def __init__(self, mod):
        self.mod = mod
        self.aperturas = []

    def get_default_wasapi_loopback(self):
        if self.mod.dispositivo is None:
            raise OSError("sin salida")
        return self.mod.dispositivo

    def get_default_input_device_info(self):  # micrófono: nunca se debe usar
        raise AssertionError("se pidió el micrófono")

    def open(self, **kw):
        self.aperturas.append(kw)
        stream = StreamFalso(self.mod.dispositivo, kw["format"])
        self.mod.streams.append(stream)
        return stream

    def terminate(self):
        pass


def modulo_pyaudio(dispositivo):
    mod = types.SimpleNamespace(paInt16=PA_INT16, paFloat32=PA_FLOAT32, dispositivo=dispositivo,
                                streams=[], instancias=[])

    def crear():
        pa = PyAudioFalso(mod)
        mod.instancias.append(pa)
        return pa

    mod.PyAudio = crear
    return mod


BOCINAS = {"index": 7, "name": "Bocinas [Loopback]", "maxInputChannels": 2,
           "defaultSampleRate": 48000.0, "isLoopbackDevice": True}
AUDIFONOS = {"index": 9, "name": "Audífonos [Loopback]", "maxInputChannels": 2,
             "defaultSampleRate": 48000.0, "isLoopbackDevice": True}


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def estereo_int16(segundos, tasa=48000, amplitud=0.5):
    n = int(segundos * tasa)
    onda = (amplitud * np.sin(2 * np.pi * 440 * np.arange(n) / tasa) * 32767).astype("<i2")
    return np.column_stack([onda, onda]).tobytes()


@pytest.fixture
def armar():
    def armar_captura(dispositivo=BOCINAS, volumen=lambda: False):
        mod = modulo_pyaudio(dict(dispositivo) if dispositivo else None)
        mensajes = []
        reloj = Reloj()
        cap = CapturaLoopback(al_mensaje=mensajes.append, pyaudio_mod=mod,
                              silenciado=volumen, reloj=reloj)
        return cap, mod, mensajes, reloj

    return armar_captura


def test_solo_abre_el_loopback_compartido(armar):
    cap, mod, _, _ = armar()
    cap.iniciar(queue.Queue())
    cap.detener()
    (kw,), = [pa.aperturas for pa in mod.instancias]
    assert kw["input"] is True
    assert kw["input_device_index"] == BOCINAS["index"]
    assert kw["channels"] == 2 and kw["rate"] == 48000
    assert "output" not in kw
    assert "input_host_api_specific_stream_info" not in kw  # nunca modo exclusivo


def test_nada_se_abre_antes_de_iniciar_y_detener_cierra(armar):
    cap, mod, _, _ = armar()
    assert mod.instancias == []
    cap.abrir()
    cap.cerrar_stream()
    assert mod.streams[0].cerrado


@pytest.mark.parametrize("formato", [PA_INT16, PA_FLOAT32])
def test_convertir_a_16k_mono_float32(formato):
    tasa, n = 48000, 48000
    onda = 0.8 * np.sin(2 * np.pi * 300 * np.arange(n) / tasa)
    if formato == PA_INT16:
        datos = np.column_stack([onda, onda]).astype(np.float32)
        datos = (datos * 32767).astype("<i2").tobytes()
    else:
        datos = np.column_stack([onda, onda]).astype("<f4").tobytes()
    import soxr

    salida = convertir(datos, formato, 2, soxr.ResampleStream(tasa, 16000, 1, dtype="float32"),
                       pa_int16=PA_INT16)
    assert salida.dtype == np.float32
    # El remuestreo en streaming retiene unos 20 ms en su filtro; salen con el siguiente bloque.
    assert 16000 - 800 <= len(salida) <= 16000
    assert salida.min() >= -1.0 and salida.max() <= 1.0
    assert np.abs(salida).max() > 0.5


def test_paso_entrega_fragmentos_de_16k(armar):
    cap, mod, _, reloj = armar()
    cola = queue.Queue()
    cap.cola = cola
    cap.abrir()
    mod.streams[0].disponibles.append(estereo_int16(0.1))
    cap.paso()
    fragmento = cola.get_nowait()
    assert isinstance(fragmento, FragmentoAudio)
    assert fragmento.muestras.dtype == np.float32
    assert np.abs(fragmento.muestras).max() > 0.1


def test_sin_datos_se_entrega_silencio(armar):
    cap, mod, mensajes, reloj = armar()
    cola = queue.Queue()
    cap.cola = cola
    cap.abrir()
    reloj.t += 0.2
    cap.paso()
    fragmento = cola.get_nowait()
    assert len(fragmento.muestras) == pytest.approx(0.2 * 16000, abs=2)
    assert not fragmento.muestras.any()
    assert mensajes == []


def test_cambio_de_dispositivo_reabre_el_loopback(armar):
    cap, mod, mensajes, reloj = armar()
    cap.cola = queue.Queue()
    cap.abrir()
    mod.dispositivo = dict(AUDIFONOS)
    reloj.t += 1.0
    cap.paso()
    assert len(mod.streams) == 1  # aún no toca revisar
    reloj.t += 1.1
    cap.paso()
    assert len(mod.streams) == 2 and mod.streams[0].cerrado
    assert mod.instancias[-1].aperturas[-1]["input_device_index"] == AUDIFONOS["index"]
    assert mensajes == []


def test_sin_dispositivo_emite_m02(armar):
    cap, mod, mensajes, _ = armar(dispositivo=None)
    cap.iniciar(queue.Queue())
    cap.detener()
    assert mensajes == ["M-02"]


def test_lectura_que_falla_emite_m03(armar):
    cap, mod, mensajes, reloj = armar()
    cap.cola = queue.Queue()
    cap.abrir()
    mod.streams[0].falla = True
    mod.dispositivo = None  # al revisar, ya no hay a qué reabrir... pero se reporta la lectura
    mod.dispositivo = dict(BOCINAS)
    cap.paso()
    mod.streams[-1].falla = True
    cap.paso()
    assert "M-03" in mensajes


def test_salida_silenciada_entrega_silencio(armar):
    estado = {"silencio": True}
    cap, mod, mensajes, reloj = armar(volumen=lambda: estado["silencio"])
    cola = queue.Queue()
    cap.cola = cola
    cap.abrir()
    mod.streams[0].disponibles.append(estereo_int16(0.1))
    cap.paso()
    assert not cola.get_nowait().muestras.any()

    estado["silencio"] = False
    reloj.t += 0.6  # se vuelve a leer el volumen cada 0.5 s
    mod.streams[0].disponibles.append(estereo_int16(0.1))
    cap.paso()
    fragmentos = [cola.get_nowait() for _ in range(cola.qsize())]
    assert any(f.muestras.any() for f in fragmentos)
    assert mensajes == []


def test_si_leer_el_volumen_falla_el_audio_sale_normal(armar):
    def falla():
        raise OSError("COM")

    cap, mod, mensajes, _ = armar(volumen=falla)
    cola = queue.Queue()
    cap.cola = cola
    cap.abrir()
    mod.streams[0].disponibles.append(estereo_int16(0.1))
    cap.paso()
    assert cola.get_nowait().muestras.any()
    assert mensajes == []


class EndpointEspia:
    def __init__(self, silenciado, nivel):
        self.llamadas = []
        self._silenciado = silenciado
        self._nivel = nivel

    def GetMute(self):  # noqa: N802
        self.llamadas.append("GetMute")
        return self._silenciado

    def GetMasterVolumeLevelScalar(self):  # noqa: N802
        self.llamadas.append("GetMasterVolumeLevelScalar")
        return self._nivel

    def __getattr__(self, nombre):
        raise AssertionError(f"se llamó a {nombre}: la app no debe cambiar el volumen")


@pytest.mark.parametrize("silenciado, nivel, esperado", [
    (1, 0.8, True), (0, 0.0, True), (0, 0.5, False),
])
def test_lector_de_volumen_solo_lee(silenciado, nivel, esperado):
    espia = EndpointEspia(silenciado, nivel)
    lector = LectorVolumen(obtener_endpoint=lambda: espia)
    assert lector() is esperado
    assert set(espia.llamadas) <= {"GetMute", "GetMasterVolumeLevelScalar"}
