"""Tests del módulo de seguridad: gestión de clave, ciclo de encriptación y detector de secretos."""

import pytest
from cryptography.fernet import Fernet
from unittest.mock import MagicMock, patch

from kit_iso.seguridad import VAR_CLAVE, ToolkitSeguridad
from kit_iso.seguridad.validador import (
    ValidadorContrasenasSeguras,
    ValidadorSecurityHeaders,
    ValidadorSeguridad,
    ValidadorTLS,
)

# argon2-cffi y bcrypt son dependencias opcionales (extra "dev"). Los tests que
# hashean/verifican con ellas se saltan si no están instaladas, en vez de fallar
# por ImportError; el fallo explícito con algoritmo inválido ya lo cubre
# test_algoritmo_invalido_falla_claro (que no depende de ninguna de las dos libs).
try:
    import argon2  # noqa: F401

    _ARGON2_DISPONIBLE = True
except ImportError:
    _ARGON2_DISPONIBLE = False

try:
    import bcrypt  # noqa: F401

    _BCRYPT_DISPONIBLE = True
except ImportError:
    _BCRYPT_DISPONIBLE = False

_requiere_argon2 = pytest.mark.skipif(
    not _ARGON2_DISPONIBLE, reason="argon2-cffi no instalado — pip install argon2-cffi"
)
_requiere_bcrypt = pytest.mark.skipif(
    not _BCRYPT_DISPONIBLE, reason="bcrypt no instalado — pip install bcrypt"
)

# ── ToolkitSeguridad ─────────────────────────────────────────────────────────


def test_sin_clave_falla_explicitamente(monkeypatch):
    # Sin clave configurada, el toolkit debe fallar visible — nunca generar una implícita.
    monkeypatch.delenv(VAR_CLAVE, raising=False)
    with pytest.raises(ValueError, match=VAR_CLAVE):
        ToolkitSeguridad()


def test_ciclo_encriptar_desencriptar(monkeypatch):
    monkeypatch.setenv(VAR_CLAVE, Fernet.generate_key().decode())
    seg = ToolkitSeguridad()
    token = seg.encriptar_datos("dato sensible")
    assert token != b"dato sensible"
    assert seg.desencriptar_datos(token) == "dato sensible"


def test_clave_persistente_entre_instancias(monkeypatch):
    # Bug original: cada instancia generaba su propia clave → datos irrecuperables tras reiniciar.
    monkeypatch.setenv(VAR_CLAVE, Fernet.generate_key().decode())
    token = ToolkitSeguridad().encriptar_datos("sobrevive al reinicio")
    assert ToolkitSeguridad().desencriptar_datos(token) == "sobrevive al reinicio"


def test_clave_por_argumento_tiene_prioridad(monkeypatch):
    monkeypatch.delenv(VAR_CLAVE, raising=False)
    clave = Fernet.generate_key()
    seg = ToolkitSeguridad(clave=clave)
    assert seg.desencriptar_datos(seg.encriptar_datos("hola")) == "hola"


# ── ValidadorSeguridad ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "codigo",
    [
        "password = 'hunter2'",
        'api_key = "sk-1234567890"',
        "SECRET = 'abc'",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.xyz123",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...",
        "aws_key = 'AKIAIOSFODNN7EXAMPLE'",
        "token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcde1234'",
    ],
)
def test_validador_detecta_secretos(codigo):
    assert ValidadorSeguridad().analizar_codigo(codigo)


def test_validador_sin_falsos_positivos():
    codigo_limpio = "resultado = cargar_config('password_field')\nx = 1"
    assert ValidadorSeguridad().analizar_codigo(codigo_limpio) == []


def test_validador_detecta_alta_entropia():
    # Cadena de 32 chars con caracteres variados → alta entropía aunque no tenga nombre sospechoso.
    codigo = "valor = 'aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW'"
    hallazgos = ValidadorSeguridad().analizar_codigo(codigo)
    assert any("entropía" in h for h in hallazgos)


def test_validador_entropia_no_alerta_texto_normal():
    # Texto en prosa normal no debe disparar la alerta de entropía.
    codigo = "descripcion = 'este es un texto descriptivo normal y sencillo'"
    hallazgos = ValidadorSeguridad().analizar_codigo(codigo)
    assert not any("entropía" in h for h in hallazgos)


# ── ValidadorContrasenasSeguras ──────────────────────────────────────────────


@_requiere_argon2
def test_argon2_hash_y_verificacion():
    val = ValidadorContrasenasSeguras(algoritmo="argon2")
    hash_ = val.hashear("contraseña_secreta_123")
    assert hash_ != "contraseña_secreta_123"
    assert val.verificar("contraseña_secreta_123", hash_)


@_requiere_argon2
def test_argon2_contrasena_incorrecta_devuelve_false():
    val = ValidadorContrasenasSeguras(algoritmo="argon2")
    hash_ = val.hashear("correcta")
    assert not val.verificar("incorrecta", hash_)


@_requiere_bcrypt
def test_bcrypt_hash_y_verificacion():
    val = ValidadorContrasenasSeguras(algoritmo="bcrypt")
    hash_ = val.hashear("contraseña_bcrypt_456")
    assert val.verificar("contraseña_bcrypt_456", hash_)


@_requiere_bcrypt
def test_bcrypt_contrasena_incorrecta_devuelve_false():
    val = ValidadorContrasenasSeguras(algoritmo="bcrypt")
    hash_ = val.hashear("correcta")
    assert not val.verificar("incorrecta", hash_)


@_requiere_argon2
def test_argon2_hashes_son_distintos_para_misma_clave():
    # El salt aleatorio garantiza que dos hashes del mismo input difieran.
    val = ValidadorContrasenasSeguras()
    h1 = val.hashear("misma")
    h2 = val.hashear("misma")
    assert h1 != h2


def test_algoritmo_invalido_falla_claro():
    with pytest.raises(ValueError, match="algoritmo"):
        ValidadorContrasenasSeguras(algoritmo="md5")


# ── ValidadorSecurityHeaders ─────────────────────────────────────────────────

_HEADERS_COMPLETOS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def test_headers_correctos_estado_ok():
    resultado = ValidadorSecurityHeaders().validar_headers(_HEADERS_COMPLETOS)
    assert resultado["estado"] == "ok"
    assert not resultado["ausentes"]
    assert not resultado["debiles"]


def test_headers_ausentes_detectados():
    resultado = ValidadorSecurityHeaders().validar_headers({})
    assert resultado["estado"] == "fallo"
    assert len(resultado["ausentes"]) == 5


def test_hsts_max_age_insuficiente():
    headers = {**_HEADERS_COMPLETOS, "Strict-Transport-Security": "max-age=3600"}
    resultado = ValidadorSecurityHeaders().validar_headers(headers)
    assert resultado["estado"] == "fallo"
    assert any("max-age" in d for d in resultado["debiles"])


def test_x_frame_options_invalido():
    headers = {**_HEADERS_COMPLETOS, "X-Frame-Options": "ALLOWALL"}
    resultado = ValidadorSecurityHeaders().validar_headers(headers)
    assert resultado["estado"] == "fallo"
    assert any("DENY" in d for d in resultado["debiles"])


def test_referrer_policy_unsafe_url():
    headers = {**_HEADERS_COMPLETOS, "Referrer-Policy": "unsafe-url"}
    resultado = ValidadorSecurityHeaders().validar_headers(headers)
    assert resultado["estado"] == "fallo"
    assert any("unsafe-url" in d for d in resultado["debiles"])


# ── ValidadorTLS ─────────────────────────────────────────────────────────────


def test_tls_valido_devuelve_ok():
    mock_cert = {
        "subject": [[("commonName", "example.com")]],
        "notAfter": "Dec 31 23:59:59 2025 GMT",
    }
    mock_tls = MagicMock()
    mock_tls.getpeercert.return_value = mock_cert
    mock_tls.version.return_value = "TLSv1.3"
    mock_tls.__enter__ = lambda s: mock_tls
    mock_tls.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("kit_iso.seguridad.validador.socket.create_connection", return_value=mock_conn):
        with patch("kit_iso.seguridad.validador.ssl.create_default_context") as mock_ctx:
            mock_ctx.return_value.wrap_socket.return_value = mock_tls
            resultado = ValidadorTLS().verificar_tls("example.com")

    assert resultado["estado"] == "ok"
    assert resultado["version"] == "TLSv1.3"


def test_tls_certificado_invalido():
    import ssl

    with patch("kit_iso.seguridad.validador.socket.create_connection") as mock_conn:
        with patch("kit_iso.seguridad.validador.ssl.create_default_context") as mock_ctx:
            mock_ctx.return_value.wrap_socket.side_effect = ssl.SSLCertVerificationError(
                "certificate verify failed"
            )
            mock_conn.return_value.__enter__ = lambda s: mock_conn.return_value
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            resultado = ValidadorTLS().verificar_tls("badssl.example.com")

    assert resultado["estado"] == "fallo"
    assert "Certificado inválido" in resultado["error"]
