"""kit_iso — controles técnicos automatizables para cumplimiento normativo.

Este paquete ayuda a implementar controles técnicos alineados con normas ISO;
no certifica el cumplimiento de ninguna norma (eso corresponde a un sistema de
gestión y a una auditoría externa).

Módulos disponibles:
    seguridad    — ISO 27001: encriptación, detección de secretos, hashing, headers, TLS
    base_datos   — ISO 27001: BD segura con commit/rollback y whitelist
    accesibilidad — WCAG 2.1: 6 criterios de accesibilidad HTML
    calidad      — ISO 25010: rendimiento, complejidad ciclomática, cobertura
    usabilidad   — ISO 9241: validación de inputs y métricas de usabilidad
    ai_act       — AI Act + ISO 42001 + ISO 23894: transparencia, clasificación de riesgo, gobernanza
    cra          — CRA + ISO 29147/30111: SBOM, divulgación de vulnerabilidades, secure-by-design
    privacidad   — ISO 27701 + ISO 27017/27018: detección PII, enmascarado de logs, cloud
    iso_5055     — ISO 5055: calidad de código (bandit → CWE mapping)
    iso_25012    — ISO 25012: calidad de datos (completitud, exactitud, consistencia)
"""

import logging

from .base_datos import BaseDatosSegura
from .seguridad import ToolkitSeguridad
from .usabilidad import HerramientasUsabilidad

__all__ = ["BaseDatosSegura", "HerramientasUsabilidad", "ToolkitSeguridad"]
__version__ = "1.0.2"

# NullHandler: una librería nunca configura el logging global (basicConfig);
# eso es responsabilidad de la aplicación que la usa.
logging.getLogger("KitISO").addHandler(logging.NullHandler())
