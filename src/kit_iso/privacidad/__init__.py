"""Privacidad y protección de datos — ISO 27701, ISO 27017/27018 (GDPR/cloud PII)."""

import logging
import re
from typing import ClassVar

# ── Patrones PII (ISO 27701 + GDPR Art. 4) ───────────────────────────────────

_PATRONES_PII: dict[str, str] = {
    "email": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "telefono_es": r"\b(?:\+34|0034\s?)?[6789]\d{2}[\s\-]?\d{3}[\s\-]?\d{3}\b",
    "tarjeta_credito": r"\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})\b",
    "dni_es": r"\b\d{8}[A-HJ-NP-TV-Z]\b",
    "nie_es": r"\b[XYZ]\d{7}[A-Z]\b",
    "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b",
    "ip_privada": r"\b(?:10\.\d{1,3}\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b",
    "password_log": r"(?:password|passwd|clave|contraseña)\s*[=:]\s*\S+",  # nosec B105 — es un regex de detección, no una contraseña
}


class DetectorPII:
    """Detecta datos personales en texto (ISO 27701 + GDPR Art. 5 — minimización).

    Ejemplo::

        det = DetectorPII()
        resultado = det.analizar("Contacta con juan@empresa.com o al 612345678")
        # → {"contiene_pii": True, "hallazgos": [{"tipo": "email", ...}, ...]}
    """

    def __init__(self, patrones_adicionales: dict[str, str] | None = None):
        self.patrones = dict(_PATRONES_PII)
        if patrones_adicionales:
            self.patrones.update(patrones_adicionales)

    def analizar(self, texto: str) -> dict:
        """Detecta PII en el texto dado.

        Returns::

            {
                "contiene_pii": bool,
                "norma": "ISO 27701 + GDPR Art. 5",
                "hallazgos": [{"tipo": "email", "posicion": 12, "muestra": "j***@empresa.com"}]
            }
        """
        hallazgos = []
        for tipo, patron in self.patrones.items():
            for match in re.finditer(patron, texto, re.IGNORECASE):
                hallazgos.append(
                    {
                        "tipo": tipo,
                        "posicion": match.start(),
                        "muestra": self._enmascarar(match.group(), tipo),
                    }
                )
        return {
            "contiene_pii": bool(hallazgos),
            "norma": "ISO 27701 + GDPR Art. 5",
            "hallazgos": hallazgos,
        }

    @staticmethod
    def _enmascarar(valor: str, tipo: str) -> str:
        if tipo == "email":
            partes = valor.split("@")
            return (partes[0][0] + "***@" + partes[1]) if len(partes) == 2 else "***"
        if tipo == "tarjeta_credito":
            limpio = re.sub(r"[\s\-]", "", valor)
            return "*" * (len(limpio) - 4) + limpio[-4:]
        if len(valor) > 4:
            return valor[:2] + "*" * (len(valor) - 4) + valor[-2:]
        return "***"


# ── Enmascarador de logs (ISO 27701 + ISO 27018) ──────────────────────────────


class EnmascaradorLogs:
    """Enmascara PII en mensajes de log antes de persistirlos (ISO 27701 + ISO 27018).

    Ejemplo::

        em = EnmascaradorLogs()
        limpio = em.enmascarar("Usuario juan@empresa.com inició sesión desde 192.168.1.5")
        # → "Usuario [EMAIL] inició sesión desde [IP_PRIVADA]"

        # O como filtro de logging:
        logging.getLogger().addFilter(em.crear_filtro_logging())
    """

    def __init__(self, detector: DetectorPII | None = None):
        self._detector = detector or DetectorPII()

    def enmascarar(self, mensaje: str) -> str:
        """Reemplaza todos los valores PII encontrados por marcadores de tipo."""
        resultado = mensaje
        for tipo, patron in self._detector.patrones.items():
            etiqueta = f"[{tipo.upper()}]"
            resultado = re.sub(patron, etiqueta, resultado, flags=re.IGNORECASE)
        return resultado

    def crear_filtro_logging(self) -> logging.Filter:
        """Devuelve un ``logging.Filter`` que enmascara PII en todos los registros."""
        enmascarador = self

        class FiltroAntiPII(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                record.msg = enmascarador.enmascarar(str(record.msg))
                return True

        return FiltroAntiPII()


# ── Checklist cloud (ISO 27017 + ISO 27018) ──────────────────────────────────


class ChecklistCloudPrivacidad:
    """Checklist de seguridad cloud y privacidad de datos en cloud (ISO 27017 + ISO 27018).

    Ejemplo::

        cl = ChecklistCloudPrivacidad()
        r27017 = cl.evaluar_27017({"cifrado_almacenamiento": True, "acceso_minimo_privilegio": True})
        r27018 = cl.evaluar_27018({"pii_no_en_logs": True, "retencion_datos_definida": False})
    """

    _CONTROLES_27017: ClassVar[list[tuple[str, str]]] = [
        (
            "separacion_responsabilidades",
            "Responsabilidades cloud (proveedor vs. cliente) documentadas",
        ),
        ("monitoreo_cloud", "Monitoreo y alertas de actividad cloud configurados"),
        ("cifrado_almacenamiento", "Cifrado de almacenamiento cloud habilitado"),
        ("acceso_minimo_privilegio", "Acceso con mínimo privilegio (IAM restrictivo)"),
        ("backups_cifrados", "Backups cifrados y proceso de recuperación probado"),
        ("logs_auditoria_cloud", "Logs de auditoría cloud habilitados y exportados"),
    ]

    _CONTROLES_27018: ClassVar[list[tuple[str, str]]] = [
        ("pii_no_en_logs", "PII ausente en logs (filtro activo o política revisada)"),
        ("pii_no_en_backups_sin_cifrar", "PII en backups solo en forma cifrada"),
        ("retencion_datos_definida", "Política de retención de PII definida y automatizada"),
        ("portabilidad_datos", "Mecanismo de exportación de datos disponible (GDPR Art. 20)"),
        ("derecho_supresion", "Proceso de borrado de datos implementado (GDPR Art. 17)"),
        ("dpa_firmado", "DPA (Data Processing Agreement) firmado con el proveedor cloud"),
    ]

    def evaluar_27017(self, controles: dict[str, bool]) -> dict:
        """Evalúa controles de seguridad cloud (ISO 27017)."""
        return self._evaluar(controles, self._CONTROLES_27017, "ISO 27017 — Seguridad cloud")

    def evaluar_27018(self, controles: dict[str, bool]) -> dict:
        """Evalúa controles de privacidad de PII en cloud (ISO 27018)."""
        return self._evaluar(controles, self._CONTROLES_27018, "ISO 27018 — PII en cloud")

    @staticmethod
    def _evaluar(controles: dict[str, bool], lista: list, norma: str) -> dict:
        cumplidos = [desc for nombre, desc in lista if controles.get(nombre, False)]
        pendientes = [desc for nombre, desc in lista if not controles.get(nombre, False)]
        puntuacion = round(len(cumplidos) / len(lista) * 100, 1) if lista else 100.0
        return {
            "estado": "ok" if not pendientes else "fallo",
            "norma": norma,
            "puntuacion": puntuacion,
            "cumplidos": cumplidos,
            "pendientes": pendientes,
        }
