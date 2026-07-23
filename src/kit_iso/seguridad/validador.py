"""ValidadorSeguridad — detección de secretos e inseguridades (ISO 27001)."""

import math
import re
import ssl
import socket


class ValidadorSeguridad:
    """Detecta secretos expuestos en código fuente (ISO 27001 A.8.12).

    Incluye patrones de credenciales hardcodeadas, tokens, claves PEM y
    detección de cadenas de alta entropía (posibles tokens sin nombre revelador).
    """

    PATRONES_CRITICOS = [
        (r'password\s*=\s*[\'"].+[\'"]', "contraseña hardcodeada"),
        (r'api_key\s*=\s*[\'"].+[\'"]', "api_key hardcodeada"),
        (r'secret\s*=\s*[\'"].+[\'"]', "secret hardcodeado"),
        (r"Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", "JWT/Bearer token"),
        (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "clave privada PEM"),
        (r"AKIA[0-9A-Z]{16}", "clave AWS IAM"),
        (r"ghp_[A-Za-z0-9]{36}", "token GitHub Personal"),
        (r"xox[bpoa]-[0-9A-Za-z\-]+", "token Slack"),
    ]

    def __init__(self, umbral_entropia: float = 4.5, longitud_min_entropia: int = 20):
        self.umbral_entropia = umbral_entropia
        self.longitud_min_entropia = longitud_min_entropia

    def analizar_codigo(self, contenido_codigo: str) -> list[str]:
        """Devuelve hallazgos de secretos detectados (lista vacía = limpio)."""
        hallazgos = []
        for patron, descripcion in self.PATRONES_CRITICOS:
            if re.search(patron, contenido_codigo, re.IGNORECASE):
                hallazgos.append(f"RIESGO ISO 27001: {descripcion} (patrón: {patron})")

        # Cadenas de alta entropía: posibles tokens/claves sin nombre revelador.
        patron_cadena = r'[\'"][A-Za-z0-9+/=_\-]{' + str(self.longitud_min_entropia) + r',}[\'"]'
        for match in re.finditer(patron_cadena, contenido_codigo):
            valor = match.group().strip("'\"")
            entropia = self._entropia_shannon(valor)
            if entropia >= self.umbral_entropia:
                hallazgos.append(
                    f"RIESGO ISO 27001: cadena de alta entropía "
                    f"({entropia:.2f} bits/char): '{valor[:20]}...'"
                )

        return hallazgos

    @staticmethod
    def _entropia_shannon(s: str) -> float:
        if not s:
            return 0.0
        freq = [s.count(c) / len(s) for c in set(s)]
        return -sum(p * math.log2(p) for p in freq)


class ValidadorContrasenasSeguras:
    """Hashing seguro de contraseñas con argon2 o bcrypt (ISO 27001 A.9.4).

    Ejemplo::

        val = ValidadorContrasenasSeguras()  # argon2 por defecto
        hash_ = val.hashear("mi_contraseña_segura")
        assert val.verificar("mi_contraseña_segura", hash_)

    Requiere: ``pip install argon2-cffi`` (argon2) o ``pip install bcrypt`` (bcrypt).
    """

    def __init__(self, algoritmo: str = "argon2"):
        if algoritmo not in ("argon2", "bcrypt"):
            raise ValueError("algoritmo debe ser 'argon2' o 'bcrypt'")
        self.algoritmo = algoritmo

    def hashear(self, contrasena: str) -> str:
        """Devuelve el hash seguro de la contraseña."""
        if self.algoritmo == "argon2":
            try:
                from argon2 import PasswordHasher
            except ImportError as e:
                raise ImportError("argon2-cffi no está instalado: pip install argon2-cffi") from e
            return PasswordHasher().hash(contrasena)
        else:
            try:
                import bcrypt
            except ImportError as e:
                raise ImportError("bcrypt no está instalado: pip install bcrypt") from e
            return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

    def verificar(self, contrasena: str, hash_almacenado: str) -> bool:
        """True si la contraseña coincide con el hash almacenado."""
        if self.algoritmo == "argon2":
            try:
                from argon2 import PasswordHasher
                from argon2.exceptions import VerifyMismatchError
            except ImportError as e:
                raise ImportError("argon2-cffi no está instalado: pip install argon2-cffi") from e
            try:
                PasswordHasher().verify(hash_almacenado, contrasena)
                return True
            except VerifyMismatchError:
                return False
        else:
            try:
                import bcrypt
            except ImportError as e:
                raise ImportError("bcrypt no está instalado: pip install bcrypt") from e
            return bcrypt.checkpw(contrasena.encode(), hash_almacenado.encode())


class ValidadorSecurityHeaders:
    """Valida cabeceras de seguridad HTTP en respuestas (ISO 27001 A.14.1).

    Ejemplo::

        val = ValidadorSecurityHeaders()
        resultado = val.validar_headers(dict(response.headers))
        if resultado["estado"] == "fallo":
            print(resultado["ausentes"], resultado["debiles"])
    """

    HEADERS_REQUERIDOS = {
        "Strict-Transport-Security": "HSTS: max-age >= 31536000 (1 año)",
        "X-Content-Type-Options": "Debe ser 'nosniff'",
        "X-Frame-Options": "Debe ser 'DENY' o 'SAMEORIGIN'",
        "Content-Security-Policy": "CSP debe estar definida",
        "Referrer-Policy": "Debe limitar la fuga de referrer (no 'unsafe-url')",
    }

    def validar_headers(self, headers: dict[str, str]) -> dict:
        """Valida las cabeceras de seguridad de una respuesta HTTP.

        Returns:
            {
                "estado": "ok" | "fallo",
                "norma": "ISO 27001 A.14.1",
                "ausentes": [...],
                "debiles": [...],
                "correctos": [...]
            }
        """
        headers_norm = {k.lower(): v for k, v in headers.items()}
        ausentes = []
        debiles = []
        correctos = []

        for header, descripcion in self.HEADERS_REQUERIDOS.items():
            valor = headers_norm.get(header.lower())
            if valor is None:
                ausentes.append(f"Ausente: {header} — {descripcion}")
            else:
                problema = self._verificar_valor(header, valor)
                if problema:
                    debiles.append(f"Débil: {header}: '{valor}' — {problema}")
                else:
                    correctos.append(header)

        return {
            "estado": "ok" if not ausentes and not debiles else "fallo",
            "norma": "ISO 27001 A.14.1",
            "ausentes": ausentes,
            "debiles": debiles,
            "correctos": correctos,
        }

    def _verificar_valor(self, header: str, valor: str) -> str | None:
        """Devuelve descripción del problema o None si el valor es aceptable."""
        h = header.lower()
        if h == "strict-transport-security":
            m = re.search(r"max-age=(\d+)", valor, re.IGNORECASE)
            if not m or int(m.group(1)) < 31536000:
                return "max-age debe ser >= 31536000 (1 año)"
        elif h == "x-content-type-options" and valor.lower().strip() != "nosniff":
            return "debe ser exactamente 'nosniff'"
        elif h == "x-frame-options" and valor.upper().strip() not in ("DENY", "SAMEORIGIN"):
            return "debe ser 'DENY' o 'SAMEORIGIN'"
        elif h == "referrer-policy" and valor.lower().strip() == "unsafe-url":
            return "'unsafe-url' expone la URL completa — usa 'strict-origin-when-cross-origin' o más restrictivo"
        return None


class ValidadorTLS:
    """Verifica que un host sirva TLS válido y actual (ISO 27001 A.10.1).

    Ejemplo::

        val = ValidadorTLS()
        resultado = val.verificar_tls("example.com")
        # {"estado": "ok", "host": "example.com", "expira": "...", "version": "TLSv1.3"}
    """

    def verificar_tls(self, host: str, puerto: int = 443, timeout: int = 10) -> dict:
        """Verifica el certificado TLS y la versión de protocolo del host."""
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, puerto), timeout=timeout) as conn:
                with ctx.wrap_socket(conn, server_hostname=host) as tls:
                    cert = tls.getpeercert()
                    subject = dict(x[0] for x in cert.get("subject", []))
                    version = tls.version()
                    resultado = {
                        "estado": "ok",
                        "host": host,
                        "subject": subject,
                        "expira": cert.get("notAfter", "desconocido"),
                        "version": version,
                    }
                    if version in ("TLSv1", "TLSv1.1"):
                        resultado["estado"] = "fallo"
                        resultado["advertencia"] = f"{version} está obsoleto — usa TLS 1.2+"
                    return resultado
        except ssl.SSLCertVerificationError as e:
            return {"estado": "fallo", "host": host, "error": f"Certificado inválido: {e}"}
        except ssl.SSLError as e:
            return {"estado": "fallo", "host": host, "error": f"Error TLS: {e}"}
        except (OSError, TimeoutError) as e:
            return {"estado": "error", "host": host, "error": str(e)}
