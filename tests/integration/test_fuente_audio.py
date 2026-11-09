"""Audio largo y continuo, como un podcast (T055, Historia 3)."""

import numpy as np
import pytest

pytestmark = [pytest.mark.modelos, pytest.mark.spec("CA-005", "RF-006")]


def test_habla_continua_da_varios_subtitulos_a_tiempo(qtbot, canal_real, cargar_wav):
    audio = cargar_wav("en_continuo.wav")
    assert len(audio) / 16000 > 7.0
    _, fuente, subtitulos, latencias = canal_real([audio])
    qtbot.waitUntil(fuente.terminado.is_set, timeout=60_000)
    qtbot.wait(3500)
    assert len(subtitulos) >= 2, [s.texto for s in subtitulos]  # gracias al corte a los 7 s
    p90 = float(np.percentile(latencias, 90))
    assert p90 <= 3.0, f"percentil 90 = {p90:.2f} s; latencias: {[round(x, 2) for x in latencias]}"
