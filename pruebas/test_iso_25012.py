"""Tests de ValidadorCalidadDatos: completitud, exactitud y consistencia (ISO 25012)."""

import pytest

from kit_iso.iso_25012 import ValidadorCalidadDatos


@pytest.fixture
def val():
    return ValidadorCalidadDatos()


# ── Completitud ───────────────────────────────────────────────────────────────


def test_completitud_ok(val):
    registros = [
        {"nombre": "Ana", "email": "ana@e.com"},
        {"nombre": "Bob", "email": "bob@e.com"},
    ]
    r = val.validar_completitud(registros, ["nombre", "email"])
    assert r["estado"] == "ok"
    assert r["registros_incompletos"] == 0
    assert r["porcentaje_completitud"] == 100.0


def test_completitud_falla_campo_ausente(val):
    registros = [{"nombre": "Ana"}, {"nombre": "Bob", "email": "b@e.com"}]
    r = val.validar_completitud(registros, ["nombre", "email"])
    assert r["estado"] == "fallo"
    assert r["registros_incompletos"] == 1
    assert r["detalle"][0]["campos_faltantes"] == ["email"]


def test_completitud_falla_campo_vacio(val):
    registros = [{"nombre": "", "email": "a@b.com"}]
    r = val.validar_completitud(registros, ["nombre", "email"])
    assert r["estado"] == "fallo"
    assert "nombre" in r["detalle"][0]["campos_faltantes"]


def test_completitud_lista_vacia(val):
    r = val.validar_completitud([], ["campo"])
    assert r["estado"] == "ok"
    assert r["porcentaje_completitud"] == 100.0


def test_completitud_porcentaje_correcto(val):
    registros = [{"a": "x"}, {"a": None}, {"a": "y"}, {"a": None}]
    r = val.validar_completitud(registros, ["a"])
    assert r["porcentaje_completitud"] == 50.0


# ── Exactitud ─────────────────────────────────────────────────────────────────


def test_exactitud_ok(val):
    registros = [{"edad": 30, "email": "a@b.com"}, {"edad": 25, "email": "c@d.es"}]
    esquema = {
        "edad": {"tipo": int, "min": 0, "max": 150},
        "email": {"tipo": str, "patron": r"^[^@]+@[^@]+\.[^@]+$"},
    }
    r = val.validar_exactitud(registros, esquema)
    assert r["estado"] == "ok"
    assert r["registros_con_errores"] == 0


def test_exactitud_falla_tipo_incorrecto(val):
    registros = [{"edad": "treinta"}]
    r = val.validar_exactitud(registros, {"edad": {"tipo": int}})
    assert r["estado"] == "fallo"
    assert "tipo" in r["detalle"][0]["error"]


def test_exactitud_falla_fuera_de_rango(val):
    registros = [{"edad": 200}]
    r = val.validar_exactitud(registros, {"edad": {"tipo": int, "min": 0, "max": 150}})
    assert r["estado"] == "fallo"
    assert "150" in r["detalle"][0]["error"]


def test_exactitud_falla_patron_email(val):
    registros = [{"email": "no-es-email"}]
    r = val.validar_exactitud(registros, {"email": {"tipo": str, "patron": r"^[^@]+@[^@]+$"}})
    assert r["estado"] == "fallo"


def test_exactitud_campo_none_ignorado(val):
    registros = [{"edad": None}]
    r = val.validar_exactitud(registros, {"edad": {"tipo": int, "min": 0}})
    assert r["estado"] == "ok"


def test_exactitud_porcentaje_correcto(val):
    registros = [{"v": 5}, {"v": -1}, {"v": 10}, {"v": -5}]
    r = val.validar_exactitud(registros, {"v": {"tipo": int, "min": 0}})
    assert r["porcentaje_exactitud"] == 50.0


# ── Consistencia ──────────────────────────────────────────────────────────────


def test_consistencia_ok(val):
    registros = [
        {"inicio": "2026-01-01", "fin": "2026-06-01"},
        {"inicio": "2025-01-01", "fin": "2025-12-31"},
    ]
    reglas = [
        {
            "descripcion": "fin >= inicio",
            "fn": lambda r: r.get("fin", "") >= r.get("inicio", ""),
        }
    ]
    r = val.validar_consistencia(registros, reglas)
    assert r["estado"] == "ok"
    assert r["registros_con_violaciones"] == 0


def test_consistencia_falla_regla_negocio(val):
    registros = [
        {"activo": True, "precio": 0},
        {"activo": True, "precio": 10},
    ]
    reglas = [
        {
            "descripcion": "precio > 0 si activo",
            "fn": lambda r: not r.get("activo") or r.get("precio", 0) > 0,
        }
    ]
    r = val.validar_consistencia(registros, reglas)
    assert r["estado"] == "fallo"
    assert r["registros_con_violaciones"] == 1
    assert "precio > 0" in r["detalle"][0]["regla"]


def test_consistencia_excepcion_en_fn_reportada(val):
    registros = [{"campo": None}]
    reglas = [
        {
            "descripcion": "acceso a atributo que no existe",
            "fn": lambda r: r["campo"].startswith("x"),  # AttributeError
        }
    ]
    r = val.validar_consistencia(registros, reglas)
    assert r["estado"] == "fallo"
    assert "error_evaluacion" in r["detalle"][0]


def test_consistencia_lista_vacia(val):
    r = val.validar_consistencia([], [])
    assert r["estado"] == "ok"
    assert r["porcentaje_consistencia"] == 100.0


def test_consistencia_multiple_reglas(val):
    registros = [
        {"edad": 15, "categoria": "adulto"},  # viola 1a regla
        {"edad": 30, "categoria": "adulto"},  # ok
    ]
    reglas = [
        {
            "descripcion": "adulto >= 18",
            "fn": lambda r: r.get("categoria") != "adulto" or r.get("edad", 0) >= 18,
        }
    ]
    r = val.validar_consistencia(registros, reglas)
    assert r["registros_con_violaciones"] == 1
    assert r["porcentaje_consistencia"] == 50.0
