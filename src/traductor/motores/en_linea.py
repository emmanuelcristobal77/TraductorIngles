"""Motor en línea: Azure AI Speech Translation (RF-015a; contracts/motor-traduccion.md §3).

Solo se crea con el modo EN_LINEA, que exige el aviso aceptado y una cuenta validada. Solo envía
el audio de las frases de la sesión activa.
"""

from __future__ import annotations

import threading
from typing import Callable

import numpy as np

from traductor.cuenta import CuentaEnLinea
from traductor.motores.base import (ErrorAutenticacion, ErrorConexion, ErrorMotor,
                                    ErrorPreparacion, Frase, MotivoDescarte, ResultadoMotor,
                                    TipoMotor)

ESPERA_MAXIMA_S = 10.0  # sin respuesta en este tiempo → ErrorConexion


class MotorEnLinea:
    nombre = "EN_LINEA"
    ESPERA_POR_DEFECTO_S = 10.0

    def __init__(self, cuenta: CuentaEnLinea, sdk=None,
                 sesion_activa: Callable[[], int | None] = lambda: None) -> None:
        self.cuenta = cuenta
        self._sdk = sdk
        self._sesion_activa = sesion_activa
        self._config = None

    def preparar(self) -> None:
        try:
            if self._sdk is None:
                import azure.cognitiveservices.speech as speechsdk

                self._sdk = speechsdk
            config = self._sdk.translation.SpeechTranslationConfig(
                subscription=self.cuenta.clave, region=self.cuenta.region)
            config.speech_recognition_language = "en-US"
            config.add_target_language("es")
            self._config = config
        except Exception as exc:  # noqa: BLE001
            raise ErrorPreparacion(type(exc).__name__) from exc

    def _descarte(self, motivo: MotivoDescarte) -> ResultadoMotor:
        return ResultadoMotor(texto_es=None, motivo_descarte=motivo, motor=TipoMotor.EN_LINEA)

    def traducir(self, frase: Frase) -> ResultadoMotor:
        if frase.sesion != self._sesion_activa():
            return self._descarte(MotivoDescarte.SIN_VOZ)  # nunca se envía audio fuera de la sesión
        sdk = self._sdk
        formato = sdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16,
                                              channels=1)
        stream = sdk.audio.PushAudioInputStream(stream_format=formato)
        stream.write((np.clip(frase.audio, -1.0, 1.0) * 32767).astype("<i2").tobytes())
        stream.close()
        reconocedor = sdk.translation.TranslationRecognizer(
            translation_config=self._config, audio_config=sdk.audio.AudioConfig(stream=stream))

        caja: dict = {}

        def esperar():
            try:
                caja["resultado"] = reconocedor.recognize_once_async().get()
            except Exception as exc:  # noqa: BLE001
                caja["error"] = exc

        hilo = threading.Thread(target=esperar, daemon=True)
        hilo.start()
        hilo.join(ESPERA_MAXIMA_S)
        if hilo.is_alive():
            raise ErrorConexion("sin respuesta")
        if "error" in caja:
            raise ErrorConexion(type(caja["error"]).__name__)
        return self._interpretar(caja["resultado"])

    def _interpretar(self, resultado) -> ResultadoMotor:
        sdk = self._sdk
        if resultado.reason == sdk.ResultReason.TranslatedSpeech:
            texto = (resultado.translations.get("es") or "").strip()
            if not texto:
                return self._descarte(MotivoDescarte.SIN_VOZ)
            return ResultadoMotor(texto_es=texto, motivo_descarte=MotivoDescarte.NINGUNO,
                                  motor=TipoMotor.EN_LINEA)
        if resultado.reason == sdk.ResultReason.NoMatch:
            return self._descarte(MotivoDescarte.SIN_VOZ)
        if resultado.reason == sdk.ResultReason.Canceled:
            detalles = sdk.CancellationDetails(resultado)
            codigos = sdk.CancellationErrorCode
            if detalles.error_code in (codigos.AuthenticationFailure, codigos.Forbidden):
                raise ErrorAutenticacion(str(detalles.error_code))
            if detalles.reason == sdk.CancellationReason.Error:
                raise ErrorConexion(str(detalles.error_code))
            return self._descarte(MotivoDescarte.SIN_VOZ)
        raise ErrorMotor(str(resultado.reason))

    def cerrar(self) -> None:
        self._config = None
