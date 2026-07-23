"""Tests del módulo cra: SBOM, política de vulnerabilidades, secure-by-design, reportes."""

import json
import tempfile


from kit_iso.cra import (
    ChecklistSecureByDesign,
    GeneradorPoliticaVulnerabilidades,
    GeneradorSBOM,
    PlantillaReporteVulnerabilidad,
)

# ── GeneradorSBOM ────────────────────────────────────────────────────────────


def test_sbom_desde_lista():
    gen = GeneradorSBOM()
    sbom = gen.desde_lista(
        [{"name": "cryptography", "version": "41.0.0"}, {"name": "bcrypt", "version": "4.0.0"}],
        "mi-app",
    )
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert len(sbom["components"]) == 2
    assert sbom["components"][0]["name"] == "cryptography"
    assert "pkg:pypi/cryptography@41.0.0" in sbom["components"][0]["purl"]


def test_sbom_desde_requirements_txt():
    contenido = "cryptography>=41.0.0\n# comentario\nbcrypt==4.0.0\n\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(contenido)
        ruta = f.name

    gen = GeneradorSBOM()
    sbom = gen.desde_requirements(ruta, "test-app")
    nombres = [c["name"] for c in sbom["components"]]
    assert "cryptography" in nombres
    assert "bcrypt" in nombres
    assert len(sbom["components"]) == 2


def test_sbom_requirements_inexistente_devuelve_sbom_vacio():
    gen = GeneradorSBOM()
    sbom = gen.desde_requirements("/ruta/que/no/existe.txt")
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["components"] == []


def test_sbom_a_json_valido():
    gen = GeneradorSBOM()
    sbom = gen.desde_lista([{"name": "requests", "version": "2.31.0"}])
    texto = gen.a_json(sbom)
    parsed = json.loads(texto)
    assert parsed["bomFormat"] == "CycloneDX"


def test_sbom_incluye_metadatos_cra():
    gen = GeneradorSBOM()
    sbom = gen.desde_lista([])
    assert "norma" in sbom["metadata"]
    assert "CRA" in sbom["metadata"]["norma"] or "29147" in sbom["metadata"]["norma"]


# ── GeneradorPoliticaVulnerabilidades ─────────────────────────────────────────


def test_security_txt_formato_rfc9116():
    gen = GeneradorPoliticaVulnerabilidades()
    txt = gen.security_txt("seg@empresa.com", "https://empresa.com/security")
    assert "Contact: mailto:seg@empresa.com" in txt
    assert "Policy: https://empresa.com/security" in txt
    assert "Expires:" in txt
    assert "Preferred-Languages:" in txt


def test_security_txt_incluye_referencia_cra():
    gen = GeneradorPoliticaVulnerabilidades()
    txt = gen.security_txt("seg@empresa.com", "https://empresa.com/sec")
    assert "CRA" in txt or "29147" in txt


def test_security_md_contiene_plazos_iso_30111():
    gen = GeneradorPoliticaVulnerabilidades()
    md = gen.security_md("Mi Proyecto", "seg@empresa.com")
    assert "Mi Proyecto" in md
    assert "seg@empresa.com" in md
    assert "24" in md  # acuse de recibo
    assert "90" in md  # resolución


def test_security_md_plazos_cra_enisa():
    gen = GeneradorPoliticaVulnerabilidades()
    md = gen.security_md("Proyecto", "a@b.com")
    assert "72" in md  # notificación ENISA
    assert "14" in md  # informe final


# ── ChecklistSecureByDesign ───────────────────────────────────────────────────


def test_checklist_todo_ok():
    cl = ChecklistSecureByDesign()
    controles = {nombre: True for nombre, _ in cl.CONTROLES}
    resultado = cl.evaluar(controles)
    assert resultado["estado"] == "ok"
    assert resultado["puntuacion"] == 100.0
    assert not resultado["pendientes"]


def test_checklist_parcial():
    cl = ChecklistSecureByDesign()
    controles = {nombre: True for nombre, _ in cl.CONTROLES[:5]}
    resultado = cl.evaluar(controles)
    assert resultado["estado"] == "fallo"
    assert resultado["puntuacion"] == 50.0
    assert len(resultado["pendientes"]) == 5


def test_checklist_vacio_todo_pendiente():
    cl = ChecklistSecureByDesign()
    resultado = cl.evaluar({})
    assert resultado["estado"] == "fallo"
    assert resultado["puntuacion"] == 0.0
    assert len(resultado["pendientes"]) == len(cl.CONTROLES)


def test_checklist_incluye_sbom_y_politica():
    cl = ChecklistSecureByDesign()
    nombres = [n for n, _ in cl.CONTROLES]
    assert "sbom_disponible" in nombres
    assert "politica_vulnerabilidades" in nombres


# ── PlantillaReporteVulnerabilidad ────────────────────────────────────────────


def test_aviso_24h_contiene_datos():
    p = PlantillaReporteVulnerabilidad()
    aviso = p.aviso_inicial_24h("RCE en parser", "mi-app", "2.1.0", "crítica")
    assert "RCE en parser" in aviso
    assert "mi-app" in aviso
    assert "2.1.0" in aviso
    assert "crítica" in aviso
    assert "24" in aviso


def test_notificacion_72h_incluye_aviso():
    p = PlantillaReporteVulnerabilidad()
    aviso = p.aviso_inicial_24h("Bug", "app", "1.0", "alta")
    notif = p.notificacion_72h(aviso, "Desbordamiento de buffer", "Deshabilitar endpoint")
    assert "Bug" in notif
    assert "Desbordamiento" in notif
    assert "72" in notif


def test_informe_14dias_incluye_cve():
    p = PlantillaReporteVulnerabilidad()
    aviso = p.aviso_inicial_24h("X", "app", "1.0", "media")
    notif = p.notificacion_72h(aviso, "análisis", "mitigación")
    informe = p.informe_final_14dias(notif, "Parche publicado", "CVE-2026-12345")
    assert "CVE-2026-12345" in informe
    assert "Parche publicado" in informe
    assert "14" in informe
