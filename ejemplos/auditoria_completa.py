"""
Ejemplo end-to-end: auditoría de cumplimiento de un proyecto Python.

Uso desde la raíz del proyecto:
    python ejemplos/auditoria_completa.py

O con la CLI:
    kit-iso auditar src/kit_iso
    kit-iso auditar src/kit_iso --formato json --salida informe.json
"""

import json
from pathlib import Path

from kit_iso._auditoria import ejecutar_auditoria, generar_markdown

DIRECTORIO = Path(__file__).parent.parent / "src" / "kit_iso"


def demo_auditoria_markdown():
    print("=" * 60)
    print("  Auditoría completa — formato Markdown")
    print("=" * 60)
    resultados = ejecutar_auditoria(DIRECTORIO)
    print(generar_markdown(resultados))


def demo_auditoria_json():
    print("=" * 60)
    print("  Auditoría completa — formato JSON (resumen)")
    print("=" * 60)
    resultados = ejecutar_auditoria(DIRECTORIO)
    resumen = {
        "version_kit": resultados["version_kit"],
        "directorio": resultados["directorio"],
        "resumen": resultados["resumen"],
        "estados": {c["norma"]: c["estado"] for c in resultados["controles"]},
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


def demo_controles_individuales():
    """Muestra cómo invocar controles individuales directamente."""
    from kit_iso._auditoria import (
        _control_complejidad,
        _control_cra,
        _control_pii,
        _control_secretos,
    )

    print("=" * 60)
    print("  Controles individuales")
    print("=" * 60)

    for nombre, ctrl in [
        ("Secretos", _control_secretos(DIRECTORIO)),
        ("Complejidad", _control_complejidad(DIRECTORIO, umbral=10)),
        ("PII", _control_pii(DIRECTORIO)),
        ("CRA artefactos", _control_cra(DIRECTORIO)),
    ]:
        estado = ctrl["estado"]
        n_hallazgos = len(ctrl["hallazgos"])
        print(f"  {nombre:<20} {estado:<12} ({n_hallazgos} hallazgo(s))")


def demo_modulos_normativos():
    """Muestra cómo usar los módulos normativos directamente."""
    from kit_iso.ai_act import ClasificadorRiesgoIA, TransparenciaIA
    from kit_iso.cra import GeneradorSBOM
    from kit_iso.privacidad import DetectorPII

    print("=" * 60)
    print("  Módulos normativos — ejemplos directos")
    print("=" * 60)

    # AI Act: clasificar un chatbot de soporte
    clf = ClasificadorRiesgoIA()
    nivel = clf.clasificar({"interactua_humanos": True, "genera_contenido": True})
    print(f"\n  AI Act — Chatbot de soporte:")
    print(f"    Nivel de riesgo : {nivel['nivel'].value}")
    print(f"    Base legal      : {nivel['base_legal']}")
    print(f"    Obligaciones    : {nivel['obligaciones']}")

    # Transparencia: aviso art. 50
    trans = TransparenciaIA()
    print(f"\n  Aviso chatbot (art. 50, es): {trans.aviso_chatbot('es')}")

    # CRA: generar SBOM mínimo
    sbom = GeneradorSBOM().desde_lista(
        [{"name": "cryptography", "version": "41.0.0"}, {"name": "bcrypt", "version": "4.0.0"}],
        "mi-servicio",
    )
    print(f"\n  SBOM CycloneDX — {len(sbom['components'])} componentes:")
    for comp in sbom["components"]:
        print(f"    - {comp['purl']}")

    # Privacidad: detectar PII
    det = DetectorPII()
    texto_log = "Login fallido para usuario juan@empresa.com desde 192.168.1.50"
    r = det.analizar(texto_log)
    print(f"\n  DetectorPII en log de ejemplo:")
    print(f"    Contiene PII : {r['contiene_pii']}")
    for h in r["hallazgos"]:
        print(f"    - {h['tipo']} (muestra: {h['muestra']})")


if __name__ == "__main__":
    demo_auditoria_markdown()
    print()
    demo_auditoria_json()
    print()
    demo_controles_individuales()
    print()
    demo_modulos_normativos()
