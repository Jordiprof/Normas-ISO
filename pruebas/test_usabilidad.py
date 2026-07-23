"""Tests del módulo de usabilidad (antes vivían, mal nombrados, en test_seguridad.py)."""

import pytest

from kit_iso.usabilidad import HerramientasUsabilidad

hu = HerramientasUsabilidad()


def test_validar_input_valido():
    assert hu.validar_input_usuario("Entrada valida") == "Entrada valida"


def test_input_con_caracteres_prohibidos_rechazado():
    with pytest.raises(ValueError):
        hu.validar_input_usuario("Entrada; con; ataque;")


def test_input_demasiado_largo_rechazado():
    with pytest.raises(ValueError):
        hu.validar_input_usuario("a" * 101)


def test_generar_feedback():
    assert hu.generar_feedback(True) == "Operación completada con éxito."
    assert "Ocurrió un error" in hu.generar_feedback(False)
