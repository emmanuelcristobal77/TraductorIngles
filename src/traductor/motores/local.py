"""Motor sin internet: faster-whisper + OPUS-MT en-es sobre CTranslate2 (research R-04, R-05).

No abre ningún socket (RF-015). Garantías y descartes: contracts/motor-traduccion.md §2.
"""

from __future__ import annotations

import sys
from pathlib import Path

from traductor.motores.base import (ErrorMotor, ErrorPreparacion, Frase, MotivoDescarte,
                                    ResultadoMotor, TipoMotor)

# Modelo elegido con la medición de T009 (research R-12, "Resultado de la medición").
MODELO_WHISPER = "base"
MUESTRAS_MEL = 3000  # 30 s: el codificador de Whisper siempre recibe esta longitud
HILOS = 4
PROB_IDIOMA_MIN = 0.6
NO_SPEECH_MAX = 0.6
LOGPROB_MIN = -1.0


def carpeta_modelos() -> Path:
    """En la carpeta de la app empaquetada (``_internal`` de PyInstaller, junto al ejecutable);
    en la raíz del repositorio durante el desarrollo."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None) or Path(sys.executable).resolve().parent
        return Path(base) / "modelos"
    return Path(__file__).resolve().parents[3] / "modelos"


class MotorLocal:
    nombre = "LOCAL"

    def __init__(self, modelo: str = MODELO_WHISPER, carpeta: Path | None = None) -> None:
        self.modelo = modelo
        self.carpeta = carpeta or carpeta_modelos()
        self._whisper = None
        self._tokenizer = None
        self._prompt: list[int] = []
        self._traductor = None
        self._sp_origen = None
        self._sp_destino = None

    def preparar(self) -> None:
        try:
            import ctranslate2
            import sentencepiece as spm
            from faster_whisper import WhisperModel
            from faster_whisper.tokenizer import Tokenizer

            self._whisper = WhisperModel(str(self.carpeta / f"whisper-{self.modelo}"), device="cpu",
                                         compute_type="int8", cpu_threads=HILOS,
                                         local_files_only=True)
            self._tokenizer = Tokenizer(self._whisper.hf_tokenizer, True, task="transcribe",
                                        language="en")
            self._prompt = list(self._tokenizer.sot_sequence) + [self._tokenizer.no_timestamps]
            opus = self.carpeta / "opus-mt-en-es-ct2"
            self._traductor = ctranslate2.Translator(str(opus), device="cpu", inter_threads=1,
                                                     intra_threads=HILOS)
            self._sp_origen = spm.SentencePieceProcessor(model_file=str(opus / "source.spm"))
            self._sp_destino = spm.SentencePieceProcessor(model_file=str(opus / "target.spm"))
        except Exception as exc:  # noqa: BLE001
            raise ErrorPreparacion(type(exc).__name__) from exc

    def _descarte(self, motivo: MotivoDescarte) -> ResultadoMotor:
        return ResultadoMotor(texto_es=None, motivo_descarte=motivo, motor=TipoMotor.LOCAL)

    def traducir(self, frase: Frase) -> ResultadoMotor:
        try:
            # Una sola pasada del codificador para detectar el idioma y transcribir (R-12):
            # transcribe(language=None) lo pasaría dos veces y no cumpliría CA-002.
            mel = self._whisper.feature_extractor(frase.audio)[:, :MUESTRAS_MEL]
            if mel.shape[1] < MUESTRAS_MEL:
                import numpy as np

                mel = np.pad(mel, ((0, 0), (0, MUESTRAS_MEL - mel.shape[1])))
            codificado = self._whisper.encode(mel)
            idioma, prob_idioma = self._whisper.model.detect_language(codificado)[0][0]
            if idioma.strip("<|>") != "en" or prob_idioma < PROB_IDIOMA_MIN:
                return self._descarte(MotivoDescarte.OTRO_IDIOMA)
            resultado = self._whisper.model.generate(
                codificado, [self._prompt], beam_size=1, return_scores=True,
                return_no_speech_prob=True, max_length=224, suppress_blank=True)[0]
            if resultado.no_speech_prob > NO_SPEECH_MAX:
                return self._descarte(MotivoDescarte.SIN_VOZ)
            if resultado.scores[0] < LOGPROB_MIN:  # promedio por ficha (length_penalty = 1)
                return self._descarte(MotivoDescarte.BAJA_CONFIANZA)
            texto_en = self._tokenizer.decode(resultado.sequences_ids[0]).strip()
            if not texto_en:
                return self._descarte(MotivoDescarte.SIN_VOZ)
            fichas = self._sp_origen.encode(texto_en, out_type=str) + ["</s>"]
            salida = self._traductor.translate_batch([fichas], beam_size=1)[0].hypotheses[0]
            texto_es = self._sp_destino.decode([f for f in salida if f != "</s>"]).strip()
        except Exception as exc:  # noqa: BLE001
            raise ErrorMotor(type(exc).__name__) from exc
        if not texto_es:
            return self._descarte(MotivoDescarte.SIN_VOZ)
        return ResultadoMotor(texto_es=texto_es, motivo_descarte=MotivoDescarte.NINGUNO,
                              motor=TipoMotor.LOCAL)

    def cerrar(self) -> None:
        self._whisper = None
        self._traductor = None
