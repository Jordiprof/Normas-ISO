"""Tests de la CLI y la lógica de auditoría consolidada."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kit_iso import __version__
from kit_iso._auditoria import _sin_docstrings, ejecutar_auditoria, generar_markdown

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def directorio_limpio(tmp_path):
    """Directorio con un archivo Python sin problemas."""
    (tmp_path / "modulo.py").write_text(
        "def suma(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )
    # SECURITY.md para que el control CRA no falle
    (tmp_path / "SECURITY.md").write_text("# Seguridad\n", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def resultado_fijo():
    """Dict de resultados con un control OK y uno fallido, para probar generar_markdown."""
    return {
        "version_kit": "1.0.0",
        "timestamp": "2026-07-15T10:00:00+00:00",
        "directorio": "/proyecto/src",
        "resumen": {"total_controles": 2, "pasados": 1, "fallidos": 1, "advertencias": 0},
        "controles": [
            {
                "norma": "ISO 27001 A.8.12",
                "control": "Secretos hardcodeados",
                "estado": "ok",
                "hallazgos": [],
            },
            {
                "norma": "CRA Art. 14",
                "control": "Artefactos de divulgación",
                "estado": "fallo",
                "hallazgos": ["Falta: SECURITY.md"],
            },
        ],
    }


# ── generar_markdown ──────────────────────────────────────────────────────────


def test_markdown_contiene_cabecera_version(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "kit-iso v1.0.0" in md


def test_markdown_contiene_tabla_resumen(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "| Norma |" in md
    assert "ISO 27001 A.8.12" in md
    assert "CRA Art. 14" in md


def test_markdown_icono_ok(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "✅" in md


def test_markdown_icono_fallo(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "❌" in md


def test_markdown_hallazgo_visible(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "Falta: SECURITY.md" in md


def test_markdown_sin_hallazgos_mensaje(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "Sin hallazgos" in md


def test_markdown_resumen_ratio(resultado_fijo):
    md = generar_markdown(resultado_fijo)
    assert "1/2 controles pasados" in md


def test_markdown_error_en_control():
    resultado = {
        "version_kit": "1.0.0",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "directorio": "/x",
        "resumen": {"total_controles": 1, "pasados": 0, "fallidos": 1, "advertencias": 0},
        "controles": [
            {
                "norma": "TEST",
                "control": "Control roto",
                "estado": "error",
                "hallazgos": [],
                "error": "ModuleNotFoundError: módulo ausente",
            }
        ],
    }
    md = generar_markdown(resultado)
    assert "Error al ejecutar el control" in md
    assert "ModuleNotFoundError" in md


def test_markdown_nota_visible():
    resultado = {
        "version_kit": "1.0.0",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "directorio": "/x",
        "resumen": {"total_controles": 1, "pasados": 1, "fallidos": 0, "advertencias": 0},
        "controles": [
            {
                "norma": "WCAG 2.1",
                "control": "Accesibilidad HTML",
                "estado": "ok",
                "hallazgos": [],
                "nota": "No se encontraron archivos .html.",
            }
        ],
    }
    md = generar_markdown(resultado)
    assert "No se encontraron archivos .html." in md


# ── ejecutar_auditoria ────────────────────────────────────────────────────────


def test_resultado_tiene_keys_obligatorias(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio)
    assert "version_kit" in r
    assert "timestamp" in r
    assert "directorio" in r
    assert "resumen" in r
    assert "controles" in r


def test_version_kit_coincide(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio)
    assert r["version_kit"] == __version__


def test_directorio_resuelto_a_absoluta(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio)
    assert Path(r["directorio"]).is_absolute()


def test_resumen_suma_correcta(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio)
    res = r["resumen"]
    assert res["pasados"] + res["fallidos"] + res["advertencias"] == res["total_controles"]


def test_hay_seis_controles(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio)
    assert r["resumen"]["total_controles"] == 6


def test_cada_control_tiene_keys_minimas(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio)
    for c in r["controles"]:
        assert "norma" in c
        assert "control" in c
        assert "estado" in c
        assert "hallazgos" in c
        assert c["estado"] in ("ok", "fallo", "error", "advertencia")


def test_umbral_complejidad_personalizable(directorio_limpio):
    r = ejecutar_auditoria(directorio_limpio, umbral_complejidad=5)
    ctrl = next(c for c in r["controles"] if "complejidad" in c["control"].lower())
    assert "5" in ctrl["control"]


def test_directorio_vacio_ok(tmp_path):
    r = ejecutar_auditoria(tmp_path)
    # sin archivos Python no puede haber secretos, CWE ni PII
    secretos = next(c for c in r["controles"] if "Secreto" in c["control"])
    assert secretos["estado"] == "ok"


# ── Exclusiones y docstrings ──────────────────────────────────────────────────


def test_excluir_salta_archivos(tmp_path):
    """Un archivo con secretos dentro de un glob excluido no genera hallazgos."""
    demo = tmp_path / "demo"
    demo.mkdir()
    (demo / "config.py").write_text('password = "supersecreta123"\n', encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("# Seguridad\n", encoding="utf-8")

    con_exclusion = ejecutar_auditoria(tmp_path, excluir=["demo/*"])
    secretos = next(c for c in con_exclusion["controles"] if "Secreto" in c["control"])
    assert secretos["estado"] == "ok"

    sin_exclusion = ejecutar_auditoria(tmp_path)
    secretos = next(c for c in sin_exclusion["controles"] if "Secreto" in c["control"])
    assert secretos["estado"] == "fallo"


def test_pii_ignora_docstrings(tmp_path):
    """Emails en docstrings no cuentan como PII; en código sí."""
    (tmp_path / "doc.py").write_text(
        'def f():\n    """Ejemplo: contacta con juan@empresa.com"""\n    return 1\n',
        encoding="utf-8",
    )
    r = ejecutar_auditoria(tmp_path)
    pii = next(c for c in r["controles"] if "PII" in c["control"])
    assert pii["estado"] == "ok"

    (tmp_path / "codigo.py").write_text(
        'ADMIN = "juan@empresa.com"\n',
        encoding="utf-8",
    )
    r = ejecutar_auditoria(tmp_path)
    pii = next(c for c in r["controles"] if "PII" in c["control"])
    assert pii["estado"] == "fallo"


def test_sin_docstrings_preserva_posiciones():
    codigo = '"""docstring con juan@e.com"""\nx = 1\n'
    limpio = _sin_docstrings(codigo)
    assert len(limpio) == len(codigo)
    assert "juan@e.com" not in limpio
    assert "x = 1" in limpio


def test_sin_docstrings_codigo_invalido_intacto():
    codigo = "def roto(:\n"
    assert _sin_docstrings(codigo) == codigo


# ── CLI via subprocess ────────────────────────────────────────────────────────


def _run(*args, **kwargs):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-m", "kit_iso.cli", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        **kwargs,
    )


def test_cli_version():
    result = _run("--version")
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_cli_auditar_markdown(directorio_limpio):
    result = _run("auditar", str(directorio_limpio))
    assert "Informe de Auditoría" in result.stdout


def test_cli_auditar_json_valido(directorio_limpio):
    result = _run("auditar", str(directorio_limpio), "--formato", "json")
    data = json.loads(result.stdout)
    assert "controles" in data
    assert "resumen" in data


def test_cli_auditar_salida_archivo(directorio_limpio, tmp_path):
    informe = tmp_path / "informe.md"
    result = _run("auditar", str(directorio_limpio), "--salida", str(informe))
    assert informe.exists()
    assert "Informe de Auditoría" in informe.read_text(encoding="utf-8")
    assert "guardado en" in result.stdout


def test_cli_directorio_inexistente():
    result = _run("auditar", "/ruta/que/no/existe/jamas")
    assert result.returncode == 2
    assert "no existe" in result.stderr


def test_cli_exit_code_ok_con_security_md(tmp_path):
    """Sin fallos → exit 0."""
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("# Seguridad\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n', encoding="utf-8")
    result = _run("auditar", str(tmp_path), "--formato", "json")
    data = json.loads(result.stdout)
    if data["resumen"]["fallidos"] == 0:
        assert result.returncode == 0


def test_cli_umbral_complejidad_flag(directorio_limpio):
    result = _run("auditar", str(directorio_limpio), "--umbral-complejidad", "3", "--formato", "json")
    data = json.loads(result.stdout)
    ctrl = next(c for c in data["controles"] if "complejidad" in c["control"].lower())
    assert "3" in ctrl["control"]


def test_cli_sin_subcomando_falla():
    result = _run()
    assert result.returncode != 0


def test_cli_excluir_flag(tmp_path):
    demo = tmp_path / "demo"
    demo.mkdir()
    (demo / "config.py").write_text('api_key = "abc123"\n', encoding="utf-8")
    result = _run("auditar", str(tmp_path), "--excluir", "demo/*", "--formato", "json")
    data = json.loads(result.stdout)
    secretos = next(c for c in data["controles"] if "Secreto" in c["control"])
    assert secretos["estado"] == "ok"
