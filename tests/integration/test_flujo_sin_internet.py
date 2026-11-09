"""Flujo completo sin internet con los modelos reales (T039)."""

import numpy as np
import pytest

pytestmark = [pytest.mark.modelos,
              pytest.mark.spec("RF-006", "RF-007", "RF-012", "RF-015", "CA-001", "CA-002",
                               "CA-011")]

FRASES = [f"en_frase_{i:02d}.wav" for i in range(1, 11)]


def test_frases_en_ingles_dan_subtitulos_a_tiempo(qtbot, canal_real, cargar_wav, bloquear_red):
    _, fuente, subtitulos, latencias = canal_real([cargar_wav(n) for n in FRASES])
    qtbot.waitUntil(fuente.terminado.is_set, timeout=120_000)
    qtbot.wait(3500)  # la última frase todavía se está traduciendo
    assert len(subtitulos) >= 9, [s.texto for s in subtitulos]
    assert all(s.texto.strip() for s in subtitulos)
    for s in subtitulos:  # ya con el glosario aplicado
        assert " coche" not in s.texto and "ordenador" not in s.texto
    p90 = float(np.percentile(latencias, 90))
    assert p90 <= 3.0, f"percentil 90 = {p90:.2f} s; latencias: {[round(x, 2) for x in latencias]}"


@pytest.mark.parametrize("nombre", ["es_habla.wav", "musica.wav", "silencio.wav"])
def test_ni_otro_idioma_ni_musica_ni_silencio_dan_subtitulos(qtbot, canal_real, cargar_wav,
                                                             bloquear_red, nombre):
    _, fuente, subtitulos, _ = canal_real([cargar_wav(nombre)], tiempo_real=False)
    qtbot.waitUntil(fuente.terminado.is_set, timeout=30_000)
    qtbot.wait(6000)
    assert [s.texto for s in subtitulos] == []
