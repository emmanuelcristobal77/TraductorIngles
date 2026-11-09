"""Motor sin internet con Whisper y Translator simulados (T034, contrato de motores §2)."""

import types

import numpy as np
import pytest

from traductor.motores.base import ErrorMotor, Frase, MotivoDescarte, TipoMotor
from traductor.motores.local import MotorLocal

pytestmark = pytest.mark.spec("RF-007", "RF-012", "RF-015", "CA-011")


class WhisperFalso:
    """Simula las llamadas de una sola pasada: features → encode → detect_language → generate."""

    def __init__(self, idioma="en", prob=0.95, no_speech=0.1, logprob=-0.3, error=None):
        self.idioma, self.prob, self.no_speech, self.logprob = idioma, prob, no_speech, logprob
        self.error = error
        self.codificaciones = 0
        self.generaciones = []
        self.model = self

    def feature_extractor(self, audio):
        return np.zeros((80, len(audio) // 160), np.float32)

    def encode(self, mel):
        if self.error:
            raise self.error
        assert mel.shape == (80, 3000)
        self.codificaciones += 1
        return "codificado"

    def detect_language(self, codificado):
        return [[(f"<|{self.idioma}|>", self.prob)]]

    def generate(self, codificado, prompts, **kw):
        self.generaciones.append(kw)
        return [types.SimpleNamespace(sequences_ids=[[1, 2]], scores=[self.logprob],
                                      no_speech_prob=self.no_speech)]


class TokenizerFalso:
    def decode(self, ids):
        return " Hello world."


class TraductorFalso:
    def translate_batch(self, lotes, **kw):
        return [types.SimpleNamespace(hypotheses=[["▁Hola", "▁mundo", "</s>"]]) for _ in lotes]


class SpFalso:
    def encode(self, texto, out_type=str):
        return ["▁" + p for p in texto.split()]

    def decode(self, fichas):
        return " ".join(f.lstrip("▁") for f in fichas)


def motor_con(whisper):
    motor = MotorLocal()
    motor._whisper = whisper
    motor._tokenizer = TokenizerFalso()
    motor._prompt = [1, 2, 3]
    motor._traductor = TraductorFalso()
    motor._sp_origen = motor._sp_destino = SpFalso()
    return motor


FRASE = Frase(audio=np.zeros(16000 * 3, np.float32), t_fin_habla=0.0, sesion=1)


@pytest.mark.parametrize("idioma, prob", [("es", 0.99), ("en", 0.5)])
def test_otro_idioma(idioma, prob):
    r = motor_con(WhisperFalso(idioma, prob)).traducir(FRASE)
    assert r.texto_es is None and r.motivo_descarte is MotivoDescarte.OTRO_IDIOMA


def test_sin_voz():
    r = motor_con(WhisperFalso(no_speech=0.8)).traducir(FRASE)
    assert r.texto_es is None and r.motivo_descarte is MotivoDescarte.SIN_VOZ


def test_baja_confianza():
    r = motor_con(WhisperFalso(logprob=-1.5)).traducir(FRASE)
    assert r.texto_es is None and r.motivo_descarte is MotivoDescarte.BAJA_CONFIANZA


def test_traduce_con_motor_local_en_una_sola_pasada():
    whisper = WhisperFalso()
    r = motor_con(whisper).traducir(FRASE)
    assert r.texto_es == "Hola mundo"
    assert r.motivo_descarte is MotivoDescarte.NINGUNO and r.motor is TipoMotor.LOCAL
    assert whisper.codificaciones == 1  # el codificador se usa una sola vez por frase
    assert whisper.generaciones[0]["beam_size"] == 1


def test_no_usa_la_red(bloquear_red):
    assert motor_con(WhisperFalso()).traducir(FRASE).texto_es


def test_excepcion_interna_es_error_motor():
    with pytest.raises(ErrorMotor):
        motor_con(WhisperFalso(error=RuntimeError("boom"))).traducir(FRASE)


def test_cerrar_es_idempotente():
    motor = motor_con(WhisperFalso())
    motor.cerrar()
    motor.cerrar()


def test_modelo_elegido_en_t009():
    assert MotorLocal().modelo == "base"
