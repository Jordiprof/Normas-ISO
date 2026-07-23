"""Tests del módulo privacidad: detección de PII, enmascarado de logs, checklist cloud."""

import logging

import pytest

from kit_iso.privacidad import ChecklistCloudPrivacidad, DetectorPII, EnmascaradorLogs

# ── DetectorPII ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "texto, tipo_esperado",
    [
        ("Escríbeme a juan@empresa.com", "email"),
        ("Llama al 612 345 678", "telefono_es"),
        ("Tarjeta: 4111111111111111", "tarjeta_credito"),
        ("DNI: 12345678Z", "dni_es"),
        ("NIE: X1234567A", "nie_es"),
        ("password: miSecreto123", "password_log"),
        ("IP interna 192.168.1.100", "ip_privada"),
    ],
)
def test_detector_encuentra_pii(texto, tipo_esperado):
    resultado = DetectorPII().analizar(texto)
    assert resultado["contiene_pii"] is True
    tipos = [h["tipo"] for h in resultado["hallazgos"]]
    assert tipo_esperado in tipos


def test_detector_texto_limpio():
    resultado = DetectorPII().analizar("El artículo 50 del AI Act aplica desde agosto de 2026.")
    assert resultado["contiene_pii"] is False
    assert resultado["hallazgos"] == []


def test_detector_multiples_pii():
    texto = "Contacta con ana@empresa.com o al 698765432"
    resultado = DetectorPII().analizar(texto)
    tipos = [h["tipo"] for h in resultado["hallazgos"]]
    assert "email" in tipos
    assert "telefono_es" in tipos


def test_detector_devuelve_muestra_enmascarada():
    resultado = DetectorPII().analizar("Email: usuario@dominio.com")
    hallazgo = next(h for h in resultado["hallazgos"] if h["tipo"] == "email")
    assert "@" in hallazgo["muestra"]
    assert "usuario" not in hallazgo["muestra"]  # enmascarado


def test_detector_patron_adicional():
    det = DetectorPII(patrones_adicionales={"codigo_cliente": r"CLI-\d{6}"})
    resultado = det.analizar("Cliente CLI-123456 realizó un pedido")
    tipos = [h["tipo"] for h in resultado["hallazgos"]]
    assert "codigo_cliente" in tipos


def test_detector_incluye_norma():
    resultado = DetectorPII().analizar("test")
    assert "27701" in resultado["norma"] or "GDPR" in resultado["norma"]


# ── EnmascaradorLogs ──────────────────────────────────────────────────────────


def test_enmascarador_oculta_email():
    em = EnmascaradorLogs()
    resultado = em.enmascarar("Login de usuario@ejemplo.com fallido")
    assert "usuario@ejemplo.com" not in resultado
    assert "EMAIL" in resultado.upper()


def test_enmascarador_oculta_ip_privada():
    em = EnmascaradorLogs()
    resultado = em.enmascarar("Petición desde 192.168.0.55")
    assert "192.168.0.55" not in resultado
    assert "IP" in resultado.upper()


def test_enmascarador_conserva_texto_limpio():
    em = EnmascaradorLogs()
    mensaje = "Sistema iniciado correctamente a las 08:00"
    assert em.enmascarar(mensaje) == mensaje


def test_enmascarador_multiples_pii():
    em = EnmascaradorLogs()
    msg = "Usuario a@b.com desde 10.0.0.5 — DNI 12345678Z"
    resultado = em.enmascarar(msg)
    assert "a@b.com" not in resultado
    assert "10.0.0.5" not in resultado
    assert "12345678Z" not in resultado


def test_filtro_logging_enmascara_records():
    em = EnmascaradorLogs()
    filtro = em.crear_filtro_logging()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Email secreto@secreto.com",
        args=(),
        exc_info=None,
    )
    filtro.filter(record)
    assert "secreto@secreto.com" not in record.msg


# ── ChecklistCloudPrivacidad ──────────────────────────────────────────────────


def test_27017_todo_cumplido():
    cl = ChecklistCloudPrivacidad()
    controles = {nombre: True for nombre, _ in cl._CONTROLES_27017}
    resultado = cl.evaluar_27017(controles)
    assert resultado["estado"] == "ok"
    assert resultado["puntuacion"] == 100.0


def test_27017_parcial():
    cl = ChecklistCloudPrivacidad()
    controles = {nombre: True for nombre, _ in cl._CONTROLES_27017[:3]}
    resultado = cl.evaluar_27017(controles)
    assert resultado["estado"] == "fallo"
    assert 0 < resultado["puntuacion"] < 100


def test_27018_todo_cumplido():
    cl = ChecklistCloudPrivacidad()
    controles = {nombre: True for nombre, _ in cl._CONTROLES_27018}
    resultado = cl.evaluar_27018(controles)
    assert resultado["estado"] == "ok"
    assert resultado["puntuacion"] == 100.0


def test_27018_detecta_pii_en_logs():
    cl = ChecklistCloudPrivacidad()
    resultado = cl.evaluar_27018({})
    pendientes = resultado["pendientes"]
    assert any("pii" in p.lower() or "log" in p.lower() for p in pendientes)


def test_checklist_incluye_gdpr_art17():
    cl = ChecklistCloudPrivacidad()
    resultado = cl.evaluar_27018({})
    pendientes = " ".join(resultado["pendientes"])
    assert "Art. 17" in pendientes or "borrado" in pendientes.lower()
