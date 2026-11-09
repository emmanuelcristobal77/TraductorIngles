"""Mide la latencia del motor sin internet en este equipo (research R-12, CA-002).

Funciona solo, sin importar ``src/traductor``. Por cada ``tests/fixtures/audio/en_frase_*.wav``
mide la voz a texto (faster-whisper) y la traducción (CTranslate2 + sentencepiece), suma 0.6 s
fijos por la detección del fin de la frase e imprime una tabla y el percentil 90 del total.

Sale con código 1 si el percentil 90 pasa de 3.0 s.

Uso: ``python scripts/medir_latencia.py --modelo small``
"""

from __future__ import annotations

import argparse
import time
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
AUDIOS = RAIZ / "tests" / "fixtures" / "audio"
MODELOS = RAIZ / "modelos"
FIN_DE_FRASE_S = 0.6
META_S = 3.0


def leer_wav(ruta: Path) -> np.ndarray:
    with wave.open(str(ruta), "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2
        datos = w.readframes(w.getnframes())
    return np.frombuffer(datos, dtype=np.int16).astype(np.float32) / 32768.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", choices=["small", "base"], required=True)
    args = parser.parse_args()

    import ctranslate2
    import sentencepiece as spm
    from faster_whisper import WhisperModel

    whisper = WhisperModel(str(MODELOS / f"whisper-{args.modelo}"), device="cpu",
                           compute_type="int8", cpu_threads=4)
    carpeta_opus = MODELOS / "opus-mt-en-es-ct2"
    traductor = ctranslate2.Translator(str(carpeta_opus), device="cpu", inter_threads=1,
                                       intra_threads=4)
    sp_origen = spm.SentencePieceProcessor(model_file=str(carpeta_opus / "source.spm"))
    sp_destino = spm.SentencePieceProcessor(model_file=str(carpeta_opus / "target.spm"))

    from faster_whisper.tokenizer import Tokenizer

    tokenizer = Tokenizer(whisper.hf_tokenizer, True, task="transcribe", language="en")
    prompt = list(tokenizer.sot_sequence) + [tokenizer.no_timestamps]

    def voz_a_texto(audio: np.ndarray) -> str:
        # Igual que MotorLocal: una sola pasada del codificador para detectar el idioma y
        # transcribir (research R-12). transcribe(language=None) lo pasaría dos veces.
        mel = whisper.feature_extractor(audio)[:, :3000]
        if mel.shape[1] < 3000:
            mel = np.pad(mel, ((0, 0), (0, 3000 - mel.shape[1])))
        codificado = whisper.encode(mel)
        whisper.model.detect_language(codificado)
        resultado = whisper.model.generate(codificado, [prompt], beam_size=1, return_scores=True,
                                           return_no_speech_prob=True, max_length=224)[0]
        return tokenizer.decode(resultado.sequences_ids[0]).strip()

    def traducir(texto: str) -> str:
        fichas = sp_origen.encode(texto, out_type=str) + ["</s>"]
        salida = traductor.translate_batch([fichas], beam_size=1)[0].hypotheses[0]
        return sp_destino.decode([f for f in salida if f != "</s>"])

    archivos = sorted(AUDIOS.glob("en_frase_*.wav"))
    if not archivos:
        print(f"No hay audios en {AUDIOS}")
        return 1

    # Calentamiento: la primera llamada carga cachés y no representa el uso normal.
    traducir(voz_a_texto(leer_wav(archivos[0])))

    totales = []
    print(f"Modelo Whisper: {args.modelo}")
    print(f"{'archivo':<18}{'audio s':>8}{'voz→texto':>11}{'traducción':>12}{'fin frase':>11}{'total':>8}")
    for ruta in archivos:
        audio = leer_wav(ruta)
        t0 = time.perf_counter()
        texto = voz_a_texto(audio)
        t1 = time.perf_counter()
        traducido = traducir(texto) if texto else ""
        t2 = time.perf_counter()
        total = (t1 - t0) + (t2 - t1) + FIN_DE_FRASE_S
        totales.append(total)
        print(f"{ruta.name:<18}{len(audio) / 16000:>8.1f}{t1 - t0:>11.2f}{t2 - t1:>12.2f}"
              f"{FIN_DE_FRASE_S:>11.2f}{total:>8.2f}   {traducido}")

    p90 = float(np.percentile(totales, 90))
    print(f"\nPercentil 90 del total: {p90:.2f} s (meta: ≤ {META_S:.1f} s)")
    return 0 if p90 <= META_S else 1


if __name__ == "__main__":
    raise SystemExit(main())
