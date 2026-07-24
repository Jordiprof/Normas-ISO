"""Tests de HerramientasCalidad: rendimiento, complejidad ciclomática y cobertura."""

import time
from unittest.mock import MagicMock, patch

import pytest

from kit_iso.calidad import HerramientasCalidad

# radon es una dependencia opcional (extra "dev"). Los tests que ejercitan la
# medición real de complejidad se saltan sin ella en vez de fallar por
# ImportError; el fallo explícito sin radon ya lo cubre
# test_complejidad_sin_radon_falla_claro (que no necesita radon instalado).
try:
    import radon  # noqa: F401

    _RADON_DISPONIBLE = True
except ImportError:
    _RADON_DISPONIBLE = False

_requiere_radon = pytest.mark.skipif(
    not _RADON_DISPONIBLE, reason="radon no instalado — pip install radon"
)


@pytest.fixture
def hc():
    return HerramientasCalidad(umbral_complejidad=5, umbral_cobertura=80.0)


# ── medir_performance ────────────────────────────────────────────────────────


def test_performance_devuelve_resultado_y_duracion(hc):
    resultado, duracion = hc.medir_performance(sum, range(1000))
    assert resultado == 499500
    assert duracion >= 0


def test_performance_mide_tiempo_real(hc):
    def esperar():
        time.sleep(0.05)
        return "ok"

    _, duracion = hc.medir_performance(esperar)
    assert duracion >= 0.04


# ── medir_complejidad ────────────────────────────────────────────────────────

_FUNCION_SIMPLE = """\
def sumar(a, b):
    return a + b
"""

_FUNCION_COMPLEJA = """\
def analizar(datos, opciones):
    resultado = []
    for item in datos:
        if opciones.get("filtrar") and item < 0:
            continue
        if opciones.get("duplicar"):
            resultado.append(item * 2)
        elif opciones.get("triplicar"):
            resultado.append(item * 3)
        else:
            if item % 2 == 0:
                resultado.append(item)
            elif item % 3 == 0:
                resultado.append(item + 1)
            else:
                resultado.append(item - 1)
    return resultado
"""


@_requiere_radon
def test_complejidad_funcion_simple_ok(hc):
    resultado = hc.medir_complejidad(_FUNCION_SIMPLE)
    assert resultado["estado"] == "ok"
    assert not resultado["sobre_umbral"]
    assert len(resultado["bloques"]) == 1
    assert resultado["bloques"][0]["nombre"] == "sumar"
    assert resultado["bloques"][0]["complejidad"] == 1


@_requiere_radon
def test_complejidad_funcion_compleja_falla(hc):
    resultado = hc.medir_complejidad(_FUNCION_COMPLEJA)
    assert resultado["estado"] == "fallo"
    assert resultado["sobre_umbral"]
    assert "analizar" in resultado["sobre_umbral"][0]


@_requiere_radon
def test_complejidad_umbral_configurable():
    hc_alto = HerramientasCalidad(umbral_complejidad=20)
    resultado = hc_alto.medir_complejidad(_FUNCION_COMPLEJA)
    # Con umbral 20, la función compleja debería pasar.
    assert resultado["estado"] == "ok"


def test_complejidad_sin_radon_falla_claro(hc):
    import kit_iso.calidad as mod_calidad

    original = mod_calidad._radon_disponible
    try:
        mod_calidad._radon_disponible = False
        with pytest.raises(ImportError, match="radon"):
            hc.medir_complejidad(_FUNCION_SIMPLE)
    finally:
        mod_calidad._radon_disponible = original


@_requiere_radon
def test_complejidad_devuelve_rango_mccabe(hc):
    resultado = hc.medir_complejidad(_FUNCION_SIMPLE)
    bloque = resultado["bloques"][0]
    assert bloque["rango"] in ("A", "B", "C", "D", "E", "F")


# ── medir_cobertura ──────────────────────────────────────────────────────────


def test_cobertura_ok_cuando_sobre_umbral(hc):
    mock_cov = MagicMock()
    mock_cov.report.return_value = 90.0

    with (
        patch("kit_iso.calidad.coverage_lib.Coverage", return_value=mock_cov),
        patch("kit_iso.calidad.pytest.main", return_value=0),
    ):
        resultado = hc.medir_cobertura("src/kit_iso", "pruebas/")

    assert resultado["estado"] == "ok"
    assert resultado["cobertura"] == 90.0
    assert resultado["tests_exitosos"] is True


def test_cobertura_falla_cuando_bajo_umbral(hc):
    mock_cov = MagicMock()
    mock_cov.report.return_value = 60.0

    with (
        patch("kit_iso.calidad.coverage_lib.Coverage", return_value=mock_cov),
        patch("kit_iso.calidad.pytest.main", return_value=0),
    ):
        resultado = hc.medir_cobertura("src/kit_iso", "pruebas/")

    assert resultado["estado"] == "fallo"
    assert resultado["cobertura"] == 60.0


def test_cobertura_falla_cuando_tests_fallan(hc):
    mock_cov = MagicMock()
    mock_cov.report.return_value = 85.0

    with (
        patch("kit_iso.calidad.coverage_lib.Coverage", return_value=mock_cov),
        patch("kit_iso.calidad.pytest.main", return_value=1),
    ):
        resultado = hc.medir_cobertura("src/kit_iso", "pruebas/")

    assert resultado["tests_exitosos"] is False


def test_cobertura_sin_coverage_lib_falla_claro(hc):
    import kit_iso.calidad as mod_calidad

    original = mod_calidad._coverage_disponible
    try:
        mod_calidad._coverage_disponible = False
        with pytest.raises(ImportError, match="coverage"):
            hc.medir_cobertura("src/kit_iso", "pruebas/")
    finally:
        mod_calidad._coverage_disponible = original
