"""Video en inglés: pausa y reanudación con el reloj real (T052, Historia 2)."""

import time

import pytest

from traductor.ui.subtitulos import FranjaSubtitulos

pytestmark = [pytest.mark.modelos, pytest.mark.spec("RF-012", "CA-005")]


def test_en_la_pausa_el_subtitulo_desaparece_y_al_reanudar_vuelve(qtbot, canal_real, cargar_wav):
    canal, fuente, subtitulos, _ = canal_real([cargar_wav("en_pausa.wav")])
    franja = FranjaSubtitulos(set_window_pos=lambda *a: 1)
    qtbot.addWidget(franja)
    canal.subtitulo.connect(lambda s: franja.mostrar(s, 1))
    canal.voz.connect(franja.marcar_voz)
    eventos = []
    canal.subtitulo.connect(lambda s: eventos.append(("mostrado", time.monotonic())))

    # Primera frase (~3 s) y su subtítulo.
    qtbot.waitUntil(lambda: len(subtitulos) == 1, timeout=10_000)
    t_mostrado = eventos[0][1]
    # En la pausa de 10 s: sin voz, la franja se vacía 4 s después de que aparece el último bloque.
    qtbot.waitUntil(lambda: not franja.isVisible(), timeout=6000)
    vacio_en = time.monotonic() - t_mostrado
    assert 3.8 <= vacio_en <= 4.6, f"se vació a los {vacio_en:.2f} s"
    assert len(subtitulos) == 1  # no sale ninguno nuevo durante la pausa
    # Al volver el habla, vuelven los subtítulos.
    qtbot.waitUntil(lambda: len(subtitulos) == 2, timeout=15_000)
    qtbot.waitUntil(franja.isVisible, timeout=1000)
