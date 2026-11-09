"""Glosario es-MX como postproceso (T033, research R-06)."""

import pytest

from traductor.traduccion.glosario import Glosario

pytestmark = pytest.mark.spec("RF-007")


@pytest.fixture(scope="module")
def glosario():
    return Glosario()


@pytest.mark.parametrize("entrada, salida", [
    ("Prendí el ordenador.", "Prendí la computadora."),
    ("El coche es rojo.", "El carro es rojo."),
    ("Dos coches nuevos.", "Dos carros nuevos."),
    ("Quiero un zumo.", "Quiero un jugo."),
    ("Perdí mis gafas.", "Perdí mis lentes."),
    ("¿Vosotros venís?", "¿Ustedes venís?"),
    ("Llámame al teléfono móvil.", "Llámame al celular."),
    ("Olvidé el móvil en casa.", "Olvidé el celular en casa."),
    ("Ordenador", "Computadora"),
    ("Compré un ordenador y los ordenadores.", "Compré una computadora y las computadoras."),
    ("Busca las gafas.", "Busca los lentes."),
])
def test_pares_iniciales(glosario, entrada, salida):
    assert glosario.aplicar(entrada) == salida


@pytest.mark.parametrize("texto", [
    "Las cocheras están llenas.",
    "Esto vale la pena.",
    "Eso vale 10 pesos.",
    "Es un dispositivo móvil.",
    "Vamos a conducir una reunión.",
])
def test_no_toca_lo_que_no_debe(glosario, texto):
    assert glosario.aplicar(texto) == texto


def test_gana_la_entrada_mas_larga(glosario):
    assert glosario.aplicar("Tengo un teléfono móvil.") == "Tengo un celular."


def test_es_idempotente(glosario):
    texto = "El coche y el teléfono móvil de vosotros."
    una = glosario.aplicar(texto)
    assert glosario.aplicar(una) == una


def test_ignora_filas_mal_formadas(tmp_path):
    archivo = tmp_path / "g.tsv"
    archivo.write_text("coche\tcarro\nfila sin tabulador\n\tvacío\nzumo\tjugo\textra\n",
                       encoding="utf-8")
    g = Glosario(archivo)
    assert g.aplicar("coche y zumo") == "carro y zumo"
