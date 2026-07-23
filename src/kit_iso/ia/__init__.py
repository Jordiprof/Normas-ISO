"""Módulo ia — redirige al módulo ai_act (implementación real en Fase 3).

El módulo ai_act cubre AI Act art. 50, ISO 42001 e ISO 23894.
La función chain_ia_segura (basada en LangChain) permanece pendiente.
"""

from kit_iso.ai_act import (  # noqa: F401 — re-exportados para compatibilidad
    ClasificadorRiesgoIA,
    NivelRiesgoIA,
    RegistroDecisionesIA,
    TransparenciaIA,
)


def chain_ia_segura(input_datos: str):
    raise NotImplementedError(
        "chain_ia_segura está pendiente de implementación real (Fase 4). "
        "Para controles del AI Act usa kit_iso.ai_act directamente."
    )
