"""Motor Azure Speech Translation con el SDK simulado (T059, contrato de motores §3)."""

import types

import numpy as np
import pytest

from traductor.cuenta import CuentaEnLinea
from traductor.motores.base import ErrorAutenticacion, ErrorConexion, Frase, TipoMotor
from traductor.motores.en_linea import MotorEnLinea

pytestmark = pytest.mark.spec("RF-015a", "RF-015b", "RF-015c", "RF-004")


def sdk_falso(resultado=None, demora=None):
    """Arma un módulo azure.cognitiveservices.speech mínimo."""
    sdk = types.SimpleNamespace()
    sdk.ResultReason = types.SimpleNamespace(TranslatedSpeech="TranslatedSpeech",
                                             NoMatch="NoMatch", Canceled="Canceled")
    sdk.CancellationReason = types.SimpleNamespace(Error="Error", EndOfStream="EndOfStream")
    sdk.CancellationErrorCode = types.SimpleNamespace(
        AuthenticationFailure="AuthenticationFailure", Forbidden="Forbidden",
        ConnectionFailure="ConnectionFailure", ServiceTimeout="ServiceTimeout",
        ServiceUnavailable="ServiceUnavailable", BadRequest="BadRequest")
    sdk.registro = types.SimpleNamespace(configs=[], streams=[], formatos=[])

    class Config:
        def __init__(self, subscription, region):
            self.subscription, self.region, self.destinos = subscription, region, []
            self.speech_recognition_language = None
            sdk.registro.configs.append(self)

        def add_target_language(self, idioma):
            self.destinos.append(idioma)

    class Stream:
        def __init__(self, stream_format=None):
            self.formato, self.datos, self.cerrado = stream_format, b"", False
            sdk.registro.streams.append(self)

        def write(self, datos):
            self.datos += bytes(datos)

        def close(self):
            self.cerrado = True

    class Futuro:
        def get(self):
            if demora:
                demora.wait(30)
            return resultado

    class Reconocedor:
        def __init__(self, translation_config, audio_config):
            pass

        def recognize_once_async(self):
            return Futuro()

    sdk.translation = types.SimpleNamespace(SpeechTranslationConfig=Config,
                                            TranslationRecognizer=Reconocedor)
    sdk.audio = types.SimpleNamespace(
        AudioStreamFormat=lambda samples_per_second, bits_per_sample, channels:
            sdk.registro.formatos.append((samples_per_second, bits_per_sample, channels)) or "fmt",
        PushAudioInputStream=Stream,
        AudioConfig=lambda stream: types.SimpleNamespace(stream=stream))
    sdk.CancellationDetails = lambda r: r.detalles
    return sdk


def traducido(texto):
    return types.SimpleNamespace(reason="TranslatedSpeech", translations={"es": texto})


def cancelado(codigo):
    return types.SimpleNamespace(reason="Canceled", detalles=types.SimpleNamespace(
        reason="Error", error_code=codigo))


CUENTA = CuentaEnLinea("clave", "eastus")


def frase(sesion=1):
    return Frase(audio=np.full(16000, 0.5, np.float32), t_fin_habla=0.0, sesion=sesion)


def test_configuracion_e_idiomas():
    sdk = sdk_falso(traducido("Hola"))
    motor = MotorEnLinea(CUENTA, sdk=sdk, sesion_activa=lambda: 1)
    motor.preparar()
    config = sdk.registro.configs[0]
    assert (config.subscription, config.region) == ("clave", "eastus")
    assert config.speech_recognition_language == "en-US" and config.destinos == ["es"]
    r = motor.traducir(frase())
    assert r.texto_es == "Hola" and r.motor is TipoMotor.EN_LINEA


def test_audio_por_push_stream_16k_mono_16_bits():
    sdk = sdk_falso(traducido("Hola"))
    motor = MotorEnLinea(CUENTA, sdk=sdk, sesion_activa=lambda: 1)
    motor.preparar()
    motor.traducir(frase())
    assert sdk.registro.formatos == [(16000, 16, 1)]
    stream = sdk.registro.streams[0]
    assert len(stream.datos) == 16000 * 2 and stream.cerrado
    assert np.frombuffer(stream.datos, "<i2")[0] == int(0.5 * 32767)


def test_solo_envia_frases_de_la_sesion_activa():
    sdk = sdk_falso(traducido("Hola"))
    motor = MotorEnLinea(CUENTA, sdk=sdk, sesion_activa=lambda: 2)
    motor.preparar()
    r = motor.traducir(frase(sesion=1))
    assert r.texto_es is None and sdk.registro.streams == []


@pytest.mark.parametrize("codigo", ["ConnectionFailure", "ServiceTimeout", "ServiceUnavailable"])
def test_error_de_red_es_error_conexion(codigo):
    motor = MotorEnLinea(CUENTA, sdk=sdk_falso(cancelado(codigo)), sesion_activa=lambda: 1)
    motor.preparar()
    with pytest.raises(ErrorConexion):
        motor.traducir(frase())


def test_diez_segundos_sin_respuesta_es_error_conexion(monkeypatch):
    import threading

    from traductor.motores import en_linea

    monkeypatch.setattr(en_linea, "ESPERA_MAXIMA_S", 0.2)
    bloqueo = threading.Event()
    motor = MotorEnLinea(CUENTA, sdk=sdk_falso(traducido("x"), demora=bloqueo),
                         sesion_activa=lambda: 1)
    motor.preparar()
    with pytest.raises(ErrorConexion):
        motor.traducir(frase())
    bloqueo.set()
    assert en_linea.ESPERA_MAXIMA_S == 0.2 and MotorEnLinea.ESPERA_POR_DEFECTO_S == 10.0


@pytest.mark.parametrize("codigo", ["AuthenticationFailure", "Forbidden"])
def test_cuenta_rechazada_es_error_autenticacion(codigo):
    motor = MotorEnLinea(CUENTA, sdk=sdk_falso(cancelado(codigo)), sesion_activa=lambda: 1)
    motor.preparar()
    with pytest.raises(ErrorAutenticacion):
        motor.traducir(frase())


def test_cerrar_es_idempotente():
    motor = MotorEnLinea(CUENTA, sdk=sdk_falso(traducido("x")), sesion_activa=lambda: 1)
    motor.preparar()
    motor.cerrar()
    motor.cerrar()
