"""Tests de AnalizadorISO5055: mapeo de hallazgos bandit a CWE."""

import json
from unittest.mock import MagicMock, patch

from kit_iso.iso_5055 import _BANDIT_A_CWE, CATEGORIAS_ISO5055, AnalizadorISO5055

# ── Mapeo bandit → CWE ───────────────────────────────────────────────────────


def test_mapeo_b608_es_cwe89():
    """B608 (hardcoded SQL) debe mapear a CWE-89 (SQL Injection)."""
    assert _BANDIT_A_CWE["B608"] == "CWE-89"


def test_mapeo_b301_es_cwe502():
    """B301 (pickle.loads) debe mapear a CWE-502 (Deserialización insegura)."""
    assert _BANDIT_A_CWE["B301"] == "CWE-502"


def test_mapeo_b602_es_cwe78():
    """B602 (subprocess shell=True) debe mapear a CWE-78 (OS Command Injection)."""
    assert _BANDIT_A_CWE["B602"] == "CWE-78"


def test_categorias_seguridad_incluye_sql_injection():
    assert "CWE-89" in CATEGORIAS_ISO5055["seguridad"]


def test_categorias_fiabilidad_incluye_swallowed_exceptions():
    assert "CWE-390" in CATEGORIAS_ISO5055["fiabilidad"]


# ── AnalizadorISO5055 ────────────────────────────────────────────────────────


def _bandit_output(resultados: list[dict]) -> str:
    return json.dumps({"results": resultados})


def test_analizar_sin_hallazgos_devuelve_ok():
    an = AnalizadorISO5055()
    with patch("kit_iso.iso_5055.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=_bandit_output([]), returncode=0)
        resultado = an.analizar_directorio("src/")
    assert resultado["estado"] == "ok"
    assert resultado["hallazgos_cwe"] == []


def test_analizar_mapea_hallazgo_conocido():
    an = AnalizadorISO5055()
    hallazgo_bandit = {
        "test_id": "B608",
        "issue_text": "Possible SQL injection",
        "issue_severity": "HIGH",
        "filename": "src/app.py",
        "line_number": 42,
    }
    with patch("kit_iso.iso_5055.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=_bandit_output([hallazgo_bandit]), returncode=1)
        resultado = an.analizar_directorio("src/")

    assert resultado["estado"] == "fallo"
    assert resultado["hallazgos_cwe"][0]["cwe"] == "CWE-89"
    assert resultado["hallazgos_cwe"][0]["archivo"] == "src/app.py"
    assert resultado["hallazgos_cwe"][0]["linea"] == 42


def test_analizar_resumen_por_cwe():
    an = AnalizadorISO5055()
    hallazgos = [
        {
            "test_id": "B608",
            "issue_text": "SQL",
            "issue_severity": "H",
            "filename": "f.py",
            "line_number": 1,
        },
        {
            "test_id": "B608",
            "issue_text": "SQL",
            "issue_severity": "H",
            "filename": "g.py",
            "line_number": 2,
        },
        {
            "test_id": "B301",
            "issue_text": "Pickle",
            "issue_severity": "H",
            "filename": "h.py",
            "line_number": 3,
        },
    ]
    with patch("kit_iso.iso_5055.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=_bandit_output(hallazgos), returncode=1)
        resultado = an.analizar_directorio("src/")

    assert resultado["resumen_por_cwe"]["CWE-89"] == 2
    assert resultado["resumen_por_cwe"]["CWE-502"] == 1


def test_analizar_categoriza_por_iso5055():
    an = AnalizadorISO5055()
    hallazgos = [
        {
            "test_id": "B608",
            "issue_text": "SQL",
            "issue_severity": "H",
            "filename": "f.py",
            "line_number": 1,
        },
        {
            "test_id": "B110",
            "issue_text": "Except pass",
            "issue_severity": "L",
            "filename": "g.py",
            "line_number": 2,
        },
    ]
    with patch("kit_iso.iso_5055.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=_bandit_output(hallazgos), returncode=1)
        resultado = an.analizar_directorio("src/")

    assert resultado["resumen_por_categoria"]["seguridad"] == 1
    assert resultado["resumen_por_categoria"]["fiabilidad"] == 1


def test_analizar_test_id_desconocido_usa_fallback():
    an = AnalizadorISO5055()
    hallazgo = {
        "test_id": "B999",  # no existe en el mapa
        "issue_text": "Unknown",
        "issue_severity": "LOW",
        "filename": "x.py",
        "line_number": 1,
    }
    with patch("kit_iso.iso_5055.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=_bandit_output([hallazgo]), returncode=1)
        resultado = an.analizar_directorio("src/")

    assert "B999" in resultado["hallazgos_cwe"][0]["cwe"]


def test_analizar_bandit_no_encontrado():
    an = AnalizadorISO5055()
    with patch("kit_iso.iso_5055.subprocess.run", side_effect=FileNotFoundError):
        resultado = an.analizar_directorio("src/")
    assert resultado["estado"] == "error"
    assert "bandit" in resultado["error"].lower()


def test_analizar_json_invalido():
    an = AnalizadorISO5055()
    with patch("kit_iso.iso_5055.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="esto no es json", returncode=1)
        resultado = an.analizar_directorio("src/")
    assert resultado["estado"] == "error"
