"""Lógica central de auditoría automatizada: ejecuta todos los controles y consolida resultados."""

import ast
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

from kit_iso import __version__

# ── Helpers ───────────────────────────────────────────────────────────────────


def _archivos(directorio: Path, patron: str, excluir: list[str] | None) -> list[Path]:
    """Lista archivos que matchean *patron*, saltando los que coincidan con algún glob de *excluir*.

    Los globs de exclusión se comparan contra la ruta relativa al directorio auditado,
    con separadores POSIX (p.ej. ``ejemplos/*``, ``*_test.py``, ``docs/**``).
    """
    archivos = []
    for f in sorted(directorio.rglob(patron)):
        rel = f.relative_to(directorio).as_posix()
        if excluir and any(fnmatch(rel, g) for g in excluir):
            continue
        archivos.append(f)
    return archivos


def _sin_docstrings(codigo: str) -> str:
    """Devuelve el código con los docstrings blanqueados (mismo nº de caracteres/posiciones).

    Los docstrings son documentación: los emails o teléfonos de ejemplo que contienen
    no son datos personales reales. Si el código no parsea, se devuelve sin cambios.
    """
    try:
        arbol = ast.parse(codigo)
    except SyntaxError:
        return codigo

    lineas = codigo.splitlines(keepends=True)
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        cuerpo = getattr(nodo, "body", [])
        if not cuerpo:
            continue
        primero = cuerpo[0]
        if not (isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant)):
            continue
        if not isinstance(primero.value.value, str):
            continue
        # Blanquear las líneas del docstring preservando longitudes y saltos de línea
        for i in range(primero.lineno - 1, primero.end_lineno):
            original = lineas[i]
            salto = "\n" if original.endswith("\n") else ""
            lineas[i] = " " * (len(original) - len(salto)) + salto
    return "".join(lineas)


# ── Controles individuales ────────────────────────────────────────────────────


def _control_secretos(directorio: Path, excluir: list[str] | None = None) -> dict:
    """ISO 27001 A.8.12 — Secretos hardcodeados en código fuente."""
    try:
        from kit_iso.seguridad.validador import ValidadorSeguridad

        val = ValidadorSeguridad()
        hallazgos = []
        for py in _archivos(directorio, "*.py", excluir):
            try:
                for item in val.analizar_codigo(py.read_text(encoding="utf-8", errors="ignore")):
                    hallazgos.append(f"{py.relative_to(directorio)}: {item[:120]}")
            except Exception:  # nosec B110 — archivo inaccesible, se omite deliberadamente
                pass
        return {
            "norma": "ISO 27001 A.8.12",
            "control": "Secretos hardcodeados en código fuente",
            "estado": "fallo" if hallazgos else "ok",
            "hallazgos": hallazgos,
        }
    except Exception as e:
        return {
            "norma": "ISO 27001 A.8.12",
            "control": "Secretos hardcodeados en código fuente",
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


def _control_cwe(directorio: Path) -> dict:
    """ISO/IEC 5055 — Debilidades CWE detectadas via bandit."""
    try:
        from kit_iso.iso_5055 import AnalizadorISO5055

        resultado = AnalizadorISO5055().analizar_directorio(str(directorio))
        hallazgos = [
            f"{h['cwe']} — {h['descripcion'][:60]} ({Path(h['archivo']).name}:{h['linea']})"
            for h in resultado["hallazgos_cwe"]
        ]
        return {
            "norma": "ISO/IEC 5055",
            "control": "Calidad de código — debilidades CWE (bandit)",
            "estado": resultado["estado"],
            "hallazgos": hallazgos,
            "resumen_por_cwe": resultado.get("resumen_por_cwe", {}),
            "resumen_por_categoria": resultado.get("resumen_por_categoria", {}),
        }
    except Exception as e:
        return {
            "norma": "ISO/IEC 5055",
            "control": "Calidad de código — debilidades CWE (bandit)",
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


def _control_complejidad(directorio: Path, umbral: int, excluir: list[str] | None = None) -> dict:
    """ISO 25010 — Complejidad ciclomática de McCabe."""
    label = f"Complejidad ciclomática (umbral McCabe: {umbral})"
    try:
        from kit_iso.calidad import HerramientasCalidad

        hc = HerramientasCalidad(umbral_complejidad=umbral)
        sobre_umbral = []
        for py in _archivos(directorio, "*.py", excluir):
            try:
                r = hc.medir_complejidad(py.read_text(encoding="utf-8", errors="ignore"))
                for item in r.get("sobre_umbral", []):
                    sobre_umbral.append(f"{py.relative_to(directorio)}: {item}")
            except Exception:  # nosec B110 — archivo o módulo inaccesible, se omite
                pass
        return {
            "norma": "ISO 25010 — Mantenibilidad",
            "control": label,
            "estado": "fallo" if sobre_umbral else "ok",
            "hallazgos": sobre_umbral,
        }
    except Exception as e:
        return {
            "norma": "ISO 25010 — Mantenibilidad",
            "control": label,
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


def _control_pii(directorio: Path, excluir: list[str] | None = None) -> dict:
    """ISO 27701 + GDPR — PII en código fuente.

    Los docstrings se excluyen del escaneo: sus emails/teléfonos son ejemplos de
    documentación, no datos personales reales.
    """
    try:
        from kit_iso.privacidad import DetectorPII

        det = DetectorPII()
        hallazgos = []
        _EXCLUIR = {"password_log"}  # ya cubierto por ISO 27001
        for py in _archivos(directorio, "*.py", excluir):
            try:
                codigo = _sin_docstrings(py.read_text(encoding="utf-8", errors="ignore"))
                r = det.analizar(codigo)
                for h in r["hallazgos"]:
                    if h["tipo"] not in _EXCLUIR:
                        hallazgos.append(
                            f"{py.relative_to(directorio)}: {h['tipo']} (pos. {h['posicion']})"
                        )
            except Exception:  # nosec B110 — archivo inaccesible, se omite
                pass
        return {
            "norma": "ISO 27701 + GDPR Art. 5",
            "control": "PII en código fuente",
            "estado": "fallo" if hallazgos else "ok",
            "hallazgos": hallazgos,
        }
    except Exception as e:
        return {
            "norma": "ISO 27701 + GDPR Art. 5",
            "control": "PII en código fuente",
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


def _control_cra(directorio: Path) -> dict:
    """CRA Art. 14 + ISO 29147 — Artefactos de divulgación."""
    buscar_en = [directorio, directorio.parent, directorio.parent.parent]

    def existe(nombre: str) -> bool:
        return any((d / nombre).exists() for d in buscar_en)

    def existe_any(*nombres: str) -> bool:
        return any(existe(n) for n in nombres)

    artefactos = {
        "SECURITY.md": existe_any("SECURITY.md", "SECURITY"),
        ".well-known/security.txt": any(
            (d / ".well-known" / "security.txt").exists() for d in buscar_en
        ),
        "pyproject.toml o requirements.txt (fuente SBOM)": existe_any(
            "pyproject.toml", "requirements.txt"
        ),
    }
    pendientes = [nombre for nombre, ok in artefactos.items() if not ok]
    return {
        "norma": "CRA Art. 14 + ISO 29147",
        "control": "Artefactos de divulgación de vulnerabilidades",
        "estado": "ok" if not pendientes else "fallo",
        "hallazgos": [f"Falta: {a}" for a in pendientes],
    }


def _control_wcag(directorio: Path, excluir: list[str] | None = None) -> dict:
    """WCAG 2.1 / ISO 40500 — Accesibilidad HTML."""
    archivos_html = _archivos(directorio, "*.html", excluir)
    if not archivos_html:
        return {
            "norma": "WCAG 2.1 / ISO 40500",
            "control": "Accesibilidad HTML",
            "estado": "ok",
            "hallazgos": [],
            "nota": "No se encontraron archivos .html en el directorio auditado.",
        }
    try:
        from kit_iso.accesibilidad import HerramientasAccesibilidad

        acc = HerramientasAccesibilidad()
        hallazgos = []
        for html_file in archivos_html:
            try:
                r = acc.validar_html_accesible(
                    html_file.read_text(encoding="utf-8", errors="ignore")
                )
                for h in r["hallazgos"]:
                    hallazgos.append(
                        f"{html_file.relative_to(directorio)}: [{h['criterio']}] {h['mensaje'][:80]}"
                    )
            except Exception:  # nosec B110 — archivo inaccesible, se omite
                pass
        return {
            "norma": "WCAG 2.1 / ISO 40500",
            "control": "Accesibilidad HTML",
            "estado": "fallo" if hallazgos else "ok",
            "hallazgos": hallazgos,
        }
    except Exception as e:
        return {
            "norma": "WCAG 2.1 / ISO 40500",
            "control": "Accesibilidad HTML",
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


# ── API pública ───────────────────────────────────────────────────────────────


def ejecutar_auditoria(
    directorio: Path | str,
    umbral_complejidad: int = 10,
    excluir: list[str] | None = None,
) -> dict:
    """Ejecuta todos los controles automatizados sobre *directorio*.

    Args:
        directorio: raíz a auditar.
        umbral_complejidad: complejidad ciclomática máxima aceptable (McCabe).
        excluir: globs de rutas relativas a saltar (p.ej. ``["ejemplos/*", "*_demo.py"]``).
            Aplica a los controles que escanean archivos; no al de bandit (usa su
            propia configuración) ni al de artefactos CRA.

    Returns:
        {
            "version_kit": "1.0.0",
            "timestamp": "2026-07-15T...",
            "directorio": "/ruta/absoluta",
            "resumen": {"total_controles": 6, "pasados": 4, "fallidos": 2, "advertencias": 0},
            "controles": [{"norma": ..., "control": ..., "estado": ..., "hallazgos": [...]}, ...]
        }
    """
    directorio = Path(directorio).resolve()

    controles = [
        _control_secretos(directorio, excluir),
        _control_cwe(directorio),
        _control_complejidad(directorio, umbral_complejidad, excluir),
        _control_pii(directorio, excluir),
        _control_cra(directorio),
        _control_wcag(directorio, excluir),
    ]

    pasados = sum(1 for c in controles if c["estado"] == "ok")
    fallidos = sum(1 for c in controles if c["estado"] in ("fallo", "error"))
    advertencias = sum(1 for c in controles if c["estado"] == "advertencia")

    return {
        "version_kit": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directorio": str(directorio),
        "resumen": {
            "total_controles": len(controles),
            "pasados": pasados,
            "fallidos": fallidos,
            "advertencias": advertencias,
        },
        "controles": controles,
    }


def generar_markdown(resultados: dict) -> str:
    """Convierte un dict de resultados en un informe Markdown."""
    _ICONO = {"ok": "✅", "fallo": "❌", "error": "⚠️", "advertencia": "⚠️"}

    lineas = [
        f"# Informe de Auditoría — kit-iso v{resultados['version_kit']}",
        "",
        f"**Directorio auditado:** `{resultados['directorio']}`  ",
        f"**Fecha:** {resultados['timestamp'][:10]}  ",
        "",
        "## Resumen ejecutivo",
        "",
        "| Norma | Control | Estado |",
        "|-------|---------|--------|",
    ]

    for c in resultados["controles"]:
        icono = _ICONO.get(c["estado"], "❓")
        lineas.append(f"| {c['norma']} | {c['control']} | {icono} {c['estado']} |")

    r = resultados["resumen"]
    lineas += [
        "",
        f"> **{r['pasados']}/{r['total_controles']} controles pasados** — "
        f"Fallidos: {r['fallidos']} · Advertencias: {r['advertencias']}",
        "",
        "---",
        "",
    ]

    for c in resultados["controles"]:
        icono = _ICONO.get(c["estado"], "❓")
        lineas.append(f"## {icono} {c['norma']} — {c['control']}")
        lineas.append("")

        if nota := c.get("nota"):
            lineas.append(f"_{nota}_")
            lineas.append("")

        if c.get("error"):
            lineas.append(f"> **Error al ejecutar el control:** `{c['error']}`")
            lineas.append("")
        elif c.get("hallazgos"):
            for h in c["hallazgos"]:
                lineas.append(f"- {h}")
        else:
            lineas.append("_Sin hallazgos — control superado._")

        if resumen_cwe := c.get("resumen_por_cwe"):
            lineas.append("")
            lineas.append("**Resumen por CWE:**")
            for cwe, n in sorted(resumen_cwe.items()):
                lineas.append(f"- `{cwe}`: {n} hallazgo(s)")

        lineas.append("")

    return "\n".join(lineas)
