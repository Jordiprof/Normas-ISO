"""Lógica central de auditoría automatizada: ejecuta todos los controles y consolida resultados."""

import ast
from collections.abc import Callable, Iterable
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
        docstring = _nodo_docstring(nodo)
        if docstring is None:
            continue
        # Blanquear las líneas del docstring preservando longitudes y saltos de línea
        fin = docstring.end_lineno if docstring.end_lineno is not None else docstring.lineno
        for i in range(docstring.lineno - 1, fin):
            original = lineas[i]
            salto = "\n" if original.endswith("\n") else ""
            lineas[i] = " " * (len(original) - len(salto)) + salto
    return "".join(lineas)


def _nodo_docstring(nodo: ast.AST) -> ast.Expr | None:
    """Devuelve la expresión docstring de un módulo/clase/función, o None."""
    if not isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    cuerpo = nodo.body
    if not cuerpo:
        return None
    primero = cuerpo[0]
    es_str = isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant)
    if es_str and isinstance(primero.value.value, str):  # type: ignore[attr-defined]
        return primero  # type: ignore[return-value]
    return None


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
            # Archivo o módulo inaccesible durante el escaneo: se omite deliberadamente.
            except Exception:  # nosec B110  # noqa: BLE001, S110
                pass
        return {
            "norma": "ISO 27001 A.8.12",
            "control": "Secretos hardcodeados en código fuente",
            "estado": "fallo" if hallazgos else "ok",
            "hallazgos": hallazgos,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "norma": "ISO 27001 A.8.12",
            "control": "Secretos hardcodeados en código fuente",
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


def _control_cwe(directorio: Path, excluir: list[str] | None = None) -> dict:
    """ISO/IEC 5055 — Debilidades CWE detectadas via bandit."""
    try:
        from kit_iso.iso_5055 import AnalizadorISO5055

        resultado = AnalizadorISO5055().analizar_directorio(str(directorio), excluir)
        hallazgos = [
            f"{h['cwe']} — {h['descripcion'][:60]} ({Path(h['archivo']).name}:{h['linea']})"
            for h in resultado["hallazgos_cwe"]
        ]
        control = {
            "norma": "ISO/IEC 5055",
            "control": "Calidad de código — debilidades CWE (bandit)",
            "estado": resultado["estado"],
            "hallazgos": hallazgos,
            "resumen_por_cwe": resultado.get("resumen_por_cwe", {}),
            "resumen_por_categoria": resultado.get("resumen_por_categoria", {}),
        }
        if resultado.get("error"):
            control["error"] = resultado["error"]
        return control
    except Exception as e:  # noqa: BLE001
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
            # Archivo o módulo inaccesible durante el escaneo: se omite deliberadamente.
            except Exception:  # nosec B110  # noqa: BLE001, S110
                pass
        return {
            "norma": "ISO 25010 — Mantenibilidad",
            "control": label,
            "estado": "fallo" if sobre_umbral else "ok",
            "hallazgos": sobre_umbral,
        }
    except Exception as e:  # noqa: BLE001
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
            # Archivo o módulo inaccesible durante el escaneo: se omite deliberadamente.
            except Exception:  # nosec B110  # noqa: BLE001, S110
                pass
        return {
            "norma": "ISO 27701 + GDPR Art. 5",
            "control": "PII en código fuente",
            "estado": "fallo" if hallazgos else "ok",
            "hallazgos": hallazgos,
        }
    except Exception as e:  # noqa: BLE001
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
            # Archivo o módulo inaccesible durante el escaneo: se omite deliberadamente.
            except Exception:  # nosec B110  # noqa: BLE001, S110
                pass
        return {
            "norma": "WCAG 2.1 / ISO 40500",
            "control": "Accesibilidad HTML",
            "estado": "fallo" if hallazgos else "ok",
            "hallazgos": hallazgos,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "norma": "WCAG 2.1 / ISO 40500",
            "control": "Accesibilidad HTML",
            "estado": "error",
            "hallazgos": [],
            "error": str(e),
        }


# ── API pública ───────────────────────────────────────────────────────────────


# Cada control pertenece a un módulo del kit; `kit-iso.toml` decide qué módulos aplican.
# (módulo, norma, nombre del control, función)
_CONTROLES: tuple[tuple[str, str, str, Callable[..., dict]], ...] = (
    ("seguridad", "ISO 27001 A.8.12", "Secretos hardcodeados en código fuente", _control_secretos),
    ("iso_5055", "ISO/IEC 5055", "Calidad de código — debilidades CWE (bandit)", _control_cwe),
    ("calidad", "ISO 25010 — Mantenibilidad", "Complejidad ciclomática", _control_complejidad),
    ("privacidad", "ISO 27701 + GDPR Art. 5", "PII en código fuente", _control_pii),
    (
        "cra",
        "CRA Art. 14 + ISO 29147",
        "Artefactos de divulgación de vulnerabilidades",
        _control_cra,
    ),
    ("accesibilidad", "WCAG 2.1 / ISO 40500", "Accesibilidad HTML", _control_wcag),
)

MODULOS_AUDITABLES: tuple[str, ...] = tuple(m for m, *_ in _CONTROLES)


def _omitido(modulo: str, norma: str, nombre: str) -> dict:
    return {
        "norma": norma,
        "control": nombre,
        "modulo": modulo,
        "estado": "omitido",
        "hallazgos": [],
        "nota": f"No aplica a este proyecto: módulo '{modulo}' no activo en kit-iso.toml.",
    }


def _ejecutar_control(
    fn: Callable[..., dict], directorio: Path, umbral: int, excluir: list[str] | None
) -> dict:
    """Cada control tiene su propia firma; aquí se centraliza el despacho."""
    if fn is _control_complejidad:
        return fn(directorio, umbral, excluir)
    if fn is _control_cra:
        return fn(directorio)
    return fn(directorio, excluir)


def _resumen(controles: list[dict]) -> dict:
    estados = [c["estado"] for c in controles]
    return {
        "total_controles": len(controles),
        "pasados": estados.count("ok"),
        "fallidos": estados.count("fallo") + estados.count("error"),
        "advertencias": estados.count("advertencia"),
        "omitidos": estados.count("omitido"),
    }


def ejecutar_auditoria(
    directorio: Path | str,
    umbral_complejidad: int = 10,
    excluir: list[str] | None = None,
    modulos: Iterable[str] | None = None,
) -> dict:
    """Ejecuta los controles automatizados sobre *directorio*.

    Args:
        directorio: raíz a auditar.
        umbral_complejidad: complejidad ciclomática máxima aceptable (McCabe).
        excluir: globs de rutas relativas a saltar (p.ej. ``["ejemplos/*", "*_demo.py"]``).
            Aplica a todos los controles que escanean archivos (bandit incluido);
            no al de artefactos CRA.
        modulos: módulos del kit activos (normalmente los de ``kit-iso.toml``). Los controles
            de módulos no activos se registran con estado ``"omitido"``: siguen en el informe
            para que quede constancia de que no aplican, pero no cuentan como fallo.
            ``None`` ejecuta todos.

    Returns:
        {
            "version_kit": "1.1.0",
            "timestamp": "2026-09-15T...",
            "directorio": "/ruta/absoluta",
            "modulos": ["calidad", "seguridad", ...],
            "resumen": {"total_controles": 6, "pasados": 4, "fallidos": 1,
                        "advertencias": 0, "omitidos": 1},
            "controles": [{"norma": ..., "control": ..., "modulo": ..., "estado": ...,
                           "hallazgos": [...]}, ...]
        }
    """
    directorio = Path(directorio).resolve()
    activos = None if modulos is None else set(modulos)

    controles = []
    for modulo, norma, nombre, fn in _CONTROLES:
        if activos is not None and modulo not in activos:
            controles.append(_omitido(modulo, norma, nombre))
            continue
        resultado = _ejecutar_control(fn, directorio, umbral_complejidad, excluir)
        resultado["modulo"] = modulo
        controles.append(resultado)

    return {
        "version_kit": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directorio": str(directorio),
        "modulos": sorted(activos) if activos is not None else sorted(MODULOS_AUDITABLES),
        "resumen": _resumen(controles),
        "controles": controles,
    }


def generar_markdown(resultados: dict) -> str:
    """Convierte un dict de resultados en un informe Markdown."""
    _ICONO = {"ok": "✅", "fallo": "❌", "error": "⚠️", "advertencia": "⚠️", "omitido": "⏭️"}

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
    omitidos = r.get("omitidos", 0)
    aplicables = r["total_controles"] - omitidos
    resumen_linea = (
        f"> **{r['pasados']}/{aplicables} controles pasados** — "
        f"Fallidos: {r['fallidos']} · Advertencias: {r['advertencias']}"
    )
    if omitidos:
        resumen_linea += f" · Omitidos (no aplican): {omitidos}"
    lineas += [
        "",
        resumen_linea,
        "",
        "---",
        "",
    ]

    for c in resultados["controles"]:
        lineas += _seccion_control(c, _ICONO.get(c["estado"], "❓"))

    return "\n".join(lineas)


def _seccion_control(c: dict, icono: str) -> list[str]:
    lineas = [f"## {icono} {c['norma']} — {c['control']}", ""]
    if nota := c.get("nota"):
        lineas += [f"_{nota}_", ""]
    if c["estado"] == "omitido":
        return lineas + [""]
    if c.get("error"):
        lineas += [f"> **Error al ejecutar el control:** `{c['error']}`", ""]
    elif c.get("hallazgos"):
        lineas += [f"- {h}" for h in c["hallazgos"]]
    else:
        lineas.append("_Sin hallazgos — control superado._")
    if resumen_cwe := c.get("resumen_por_cwe"):
        lineas += ["", "**Resumen por CWE:**"]
        lineas += [f"- `{cwe}`: {n} hallazgo(s)" for cwe, n in sorted(resumen_cwe.items())]
    return lineas + [""]
