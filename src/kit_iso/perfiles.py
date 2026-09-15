"""Triaje, perfiles y configuración por proyecto (`kit-iso.toml`).

Decide **qué módulos del kit aplican** a un proyecto concreto. El triaje nunca adivina
en silencio: cada respuesta puede pre-rellenarse con heurísticas (`detectar`) pero se
guarda junto a su justificación, para que quede escrito por qué cada módulo está o no.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kit_iso import __version__

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover — solo Python 3.10
    import tomli as tomllib

NOMBRE_CONFIG = "kit-iso.toml"

# ── Módulos ───────────────────────────────────────────────────────────────────

MODULOS: dict[str, str] = {
    "seguridad": "ISO 27001 — secretos, cifrado, hashing, headers, TLS",
    "calidad": "ISO 25010 — complejidad ciclomática, cobertura, rendimiento",
    "iso_5055": "ISO/IEC 5055 — debilidades CWE (bandit)",
    "accesibilidad": "ISO 40500 / WCAG 2.1 — accesibilidad HTML",
    "usabilidad": "ISO 9241 — validación de inputs y métricas de usabilidad",
    "base_datos": "ISO 27001 — acceso seguro a base de datos",
    "privacidad": "ISO 27701 + RGPD — PII, enmascarado de logs, cloud",
    "ai_act": "AI Act + ISO 42001/23894 — transparencia y gobernanza IA",
    "cra": "CRA + ISO 29147/30111 — SBOM y divulgación de vulnerabilidades",
    "iso_25012": "ISO/IEC 25012 — calidad de datos",
    "ens": "ENS (RD 311/2022) — PENDIENTE en el kit",
}

MODULOS_BASE: tuple[str, ...] = ("seguridad", "calidad", "iso_5055")
MODULOS_PENDIENTES: frozenset[str] = frozenset({"ens"})

# ── Detección (heurísticas) ───────────────────────────────────────────────────

_IGNORAR_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    "site-packages",
}
_ARCHIVOS_DEPS = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "package.json",
    "environment.yml",
)
_MAX_ARCHIVOS = 5000


@dataclass
class Indicadores:
    """Resumen barato del proyecto sobre el que se aplican las heurísticas."""

    extensiones: dict[str, int] = field(default_factory=dict)
    directorios: set[str] = field(default_factory=set)
    dependencias: str = ""  # texto en minúsculas de los archivos de dependencias
    raiz: set[str] = field(default_factory=set)  # nombres de archivo en la raíz


def indicadores(directorio: Path | str) -> Indicadores:
    """Recorre el proyecto una sola vez y recoge extensiones, directorios y dependencias."""
    directorio = Path(directorio)
    ind = Indicadores()
    ind.raiz = {p.name for p in directorio.iterdir()} if directorio.is_dir() else set()

    textos: list[str] = []
    for nombre in _ARCHIVOS_DEPS:
        f = directorio / nombre
        if f.is_file():
            textos.append(f.read_text(encoding="utf-8", errors="ignore").lower())
    ind.dependencias = "\n".join(textos)

    _recorrer(directorio, ind)
    return ind


def _recorrer(directorio: Path, ind: Indicadores) -> None:
    """Cuenta extensiones y directorios saltando venv, node_modules, ocultos, etc."""
    vistos = 0
    pila = [directorio]
    while pila and vistos < _MAX_ARCHIVOS:
        actual = pila.pop()
        try:
            hijos = list(actual.iterdir())
        except OSError:
            continue
        for h in hijos:
            if h.is_dir():
                if h.name not in _IGNORAR_DIRS and not h.name.startswith("."):
                    ind.directorios.add(h.name.lower())
                    pila.append(h)
                continue
            vistos += 1
            if ext := h.suffix.lower():
                ind.extensiones[ext] = ind.extensiones.get(ext, 0) + 1


def _deps(ind: Indicadores, *nombres: str) -> list[str]:
    return [n for n in nombres if n in ind.dependencias]


def _detectar_web(ind: Indicadores) -> tuple[bool, str]:
    html = ind.extensiones.get(".html", 0) + ind.extensiones.get(".jinja", 0)
    frameworks = _deps(
        ind, "flask", "django", "fastapi", "jinja2", "react", "vue", "svelte", "next"
    )
    if html or "templates" in ind.directorios or frameworks:
        partes = []
        if html:
            partes.append(f"{html} archivo(s) .html")
        if "templates" in ind.directorios:
            partes.append("carpeta templates/")
        if frameworks:
            partes.append("dependencias: " + ", ".join(frameworks))
        return True, "; ".join(partes)
    return False, "sin .html, templates/ ni frameworks web"


def _detectar_bd(ind: Indicadores) -> tuple[bool, str]:
    drivers = _deps(
        ind, "psycopg", "sqlalchemy", "mysql", "sqlite", "prisma", "pymongo", "asyncpg", "peewee"
    )
    sql = ind.extensiones.get(".sql", 0)
    if drivers or sql:
        partes = []
        if drivers:
            partes.append("dependencias: " + ", ".join(drivers))
        if sql:
            partes.append(f"{sql} archivo(s) .sql")
        return True, "; ".join(partes)
    return False, "sin drivers de BD ni archivos .sql"


def _detectar_datos_personales(directorio: Path, ind: Indicadores) -> tuple[bool, str]:
    """Busca campos típicos de PII en código y esquemas (no datos reales: nombres de campo)."""
    import re

    patron = re.compile(
        r"\b(email|correo|dni|nif|nie|telefono|phone|iban|direccion|address)\b", re.IGNORECASE
    )
    coincidencias: list[str] = []
    for ext in (".py", ".ts", ".js", ".sql", ".prisma", ".json", ".yaml", ".yml"):
        for f in _archivos_por_extension(directorio, ext, limite=400):
            try:
                texto = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if patron.search(texto):
                coincidencias.append(f.relative_to(directorio).as_posix())
                if len(coincidencias) >= 5:
                    break
        if len(coincidencias) >= 5:
            break
    if coincidencias:
        return True, "campos de datos personales en: " + ", ".join(coincidencias)
    return False, "sin campos típicos de datos personales (email, dni, teléfono...)"


def _detectar_ia(ind: Indicadores) -> tuple[bool, str]:
    libs = _deps(
        ind,
        "openai",
        "anthropic",
        "langchain",
        "langgraph",
        "transformers",
        "torch",
        "ollama",
        "google-genai",
        "litellm",
        "llama",
    )
    if libs:
        return True, "dependencias de IA: " + ", ".join(libs)
    return False, "sin librerías de IA/LLM en las dependencias"


def _detectar_producto(ind: Indicadores) -> tuple[bool, str]:
    partes = []
    if "[project]" in ind.dependencias or "setup.py" in ind.raiz:
        partes.append("paquete Python distribuible (pyproject/setup.py)")
    if '"bin"' in ind.dependencias:
        partes.append("package.json con bin")
    if "Dockerfile" in ind.raiz:
        partes.append("Dockerfile")
    if partes:
        return True, "; ".join(partes)
    return False, "sin empaquetado ni Dockerfile: no parece un producto distribuido"


def _detectar_datasets(ind: Indicadores) -> tuple[bool, str]:
    libs = _deps(ind, "pandas", "polars", "pyarrow", "duckdb", "scikit-learn", "sklearn")
    datos = ind.extensiones.get(".csv", 0) + ind.extensiones.get(".parquet", 0)
    if libs or datos:
        partes = []
        if libs:
            partes.append("dependencias: " + ", ".join(libs))
        if datos:
            partes.append(f"{datos} archivo(s) .csv/.parquet")
        return True, "; ".join(partes)
    return False, "sin librerías de datos ni archivos .csv/.parquet"


def _archivos_por_extension(directorio: Path, ext: str, limite: int) -> list[Path]:
    encontrados: list[Path] = []
    for f in directorio.rglob(f"*{ext}"):
        if any(
            p in _IGNORAR_DIRS or p.startswith(".") for p in f.relative_to(directorio).parts[:-1]
        ):
            continue
        encontrados.append(f)
        if len(encontrados) >= limite:
            break
    return encontrados


# ── Preguntas del triaje ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class Pregunta:
    id: str
    texto: str
    modulos: tuple[str, ...]
    detector: Callable[[Path, Indicadores], tuple[bool, str]] | None = None


PREGUNTAS: tuple[Pregunta, ...] = (
    Pregunta(
        "web",
        "¿Tiene interfaz web / HTML?",
        ("accesibilidad", "usabilidad"),
        lambda _d, i: _detectar_web(i),
    ),
    Pregunta("base_datos", "¿Usa base de datos?", ("base_datos",), lambda _d, i: _detectar_bd(i)),
    Pregunta(
        "datos_personales", "¿Trata datos personales?", ("privacidad",), _detectar_datos_personales
    ),
    Pregunta("ia", "¿Usa IA / LLM?", ("ai_act",), lambda _d, i: _detectar_ia(i)),
    Pregunta(
        "producto",
        "¿Se distribuye como producto con software (CRA)?",
        ("cra",),
        lambda _d, i: _detectar_producto(i),
    ),
    Pregunta(
        "datasets",
        "¿Trabaja con datasets / analítica?",
        ("iso_25012",),
        lambda _d, i: _detectar_datasets(i),
    ),
    Pregunta("sector_publico", "¿Es para el sector público español (ENS)?", ("ens",), None),
)

PERFILES: dict[str, dict[str, bool]] = {
    "minimo": {},
    "web": {"web": True, "datos_personales": True},
    "api-datos-personales": {"base_datos": True, "datos_personales": True},
    "agente-llm": {"ia": True, "datos_personales": True},
    "producto-cra": {"producto": True},
    "sector-publico": {"web": True, "datos_personales": True, "sector_publico": True},
}


@dataclass
class Respuesta:
    valor: bool
    justificacion: str = ""


def detectar(directorio: Path | str) -> dict[str, Respuesta]:
    """Pre-rellena el triaje con heurísticas. Cada respuesta lleva su evidencia."""
    directorio = Path(directorio)
    ind = indicadores(directorio)
    respuestas: dict[str, Respuesta] = {}
    for p in PREGUNTAS:
        if p.detector is None:
            respuestas[p.id] = Respuesta(
                False, "no detectable automáticamente; confirmar con el responsable"
            )
        else:
            valor, evidencia = p.detector(directorio, ind)
            respuestas[p.id] = Respuesta(valor, evidencia)
    return respuestas


def respuestas_de_perfil(perfil: str) -> dict[str, Respuesta]:
    if perfil not in PERFILES:
        raise ValueError(f"Perfil desconocido: {perfil!r}. Disponibles: {', '.join(PERFILES)}")
    activas = PERFILES[perfil]
    return {p.id: Respuesta(activas.get(p.id, False), f"perfil '{perfil}'") for p in PREGUNTAS}


def modulos_desde_respuestas(respuestas: dict[str, Respuesta]) -> tuple[list[str], list[str]]:
    """Traduce respuestas → (módulos activos, módulos pendientes en el kit)."""
    activos: list[str] = list(MODULOS_BASE)
    pendientes: list[str] = []
    for p in PREGUNTAS:
        r = respuestas.get(p.id)
        if not (r and r.valor):
            continue
        for m in p.modulos:
            if m in MODULOS_PENDIENTES:
                if m not in pendientes:
                    pendientes.append(m)
            elif m not in activos:
                activos.append(m)
    return activos, pendientes


# ── Configuración ─────────────────────────────────────────────────────────────


@dataclass
class Configuracion:
    modulos: list[str]
    pendientes: list[str] = field(default_factory=list)
    perfil: str = "personalizado"
    umbral_complejidad: int = 10
    excluir: list[str] = field(default_factory=list)
    triaje: dict[str, Respuesta] = field(default_factory=dict)
    version: str = __version__

    @classmethod
    def desde_respuestas(
        cls,
        respuestas: dict[str, Respuesta],
        perfil: str = "personalizado",
        umbral_complejidad: int = 10,
        excluir: list[str] | None = None,
    ) -> Configuracion:
        modulos, pendientes = modulos_desde_respuestas(respuestas)
        return cls(
            modulos=modulos,
            pendientes=pendientes,
            perfil=perfil,
            umbral_complejidad=umbral_complejidad,
            excluir=list(excluir or []),
            triaje=dict(respuestas),
        )


def _toml_str(valor: str) -> str:
    return json.dumps(valor, ensure_ascii=False)


def _toml_lista(valores: list[str]) -> str:
    return "[" + ", ".join(_toml_str(v) for v in valores) + "]"


def a_toml(cfg: Configuracion) -> str:
    """Serializa la configuración (formato plano; sin dependencia de escritura TOML)."""
    lineas = [
        "# Configuración de kit-iso — generada por `kit-iso init`.",
        "# Lista los módulos del kit que aplican a ESTE proyecto y por qué. Se commitea.",
        "",
        "[kit-iso]",
        f"version = {_toml_str(cfg.version)}",
        f"perfil = {_toml_str(cfg.perfil)}",
        f"modulos = {_toml_lista(cfg.modulos)}",
        f"pendientes = {_toml_lista(cfg.pendientes)}",
        f"umbral_complejidad = {cfg.umbral_complejidad}",
        f"excluir = {_toml_lista(cfg.excluir)}",
    ]
    if cfg.triaje:
        lineas += ["", "[kit-iso.triaje]"]
        for p in PREGUNTAS:
            r = cfg.triaje.get(p.id)
            if r is None:
                continue
            valor = "true" if r.valor else "false"
            lineas.append(
                f"{p.id} = {{ valor = {valor}, justificacion = {_toml_str(r.justificacion)} }}"
            )
    return "\n".join(lineas) + "\n"


def guardar(cfg: Configuracion, ruta: Path | str) -> Path:
    ruta = Path(ruta)
    ruta.write_text(a_toml(cfg), encoding="utf-8")
    return ruta


def cargar(ruta: Path | str) -> Configuracion:
    """Lee un `kit-iso.toml`. Lanza ValueError si falta la sección o hay módulos desconocidos."""
    ruta = Path(ruta)
    datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    seccion = datos.get("kit-iso")
    if not isinstance(seccion, dict):
        # Error de formato del archivo, no de tipo de un argumento.
        raise ValueError(f"{ruta}: falta la sección [kit-iso]")  # noqa: TRY004
    modulos = list(seccion.get("modulos", []))
    desconocidos = [m for m in modulos if m not in MODULOS]
    if desconocidos:
        raise ValueError(f"{ruta}: módulos desconocidos: {', '.join(desconocidos)}")
    triaje = {
        k: Respuesta(bool(v.get("valor", False)), str(v.get("justificacion", "")))
        for k, v in seccion.get("triaje", {}).items()
        if isinstance(v, dict)
    }
    return Configuracion(
        modulos=modulos,
        pendientes=list(seccion.get("pendientes", [])),
        perfil=str(seccion.get("perfil", "personalizado")),
        umbral_complejidad=int(seccion.get("umbral_complejidad", 10)),
        excluir=list(seccion.get("excluir", [])),
        triaje=triaje,
        version=str(seccion.get("version", "")),
    )


def localizar(directorio: Path | str) -> Path | None:
    """Devuelve la ruta de `kit-iso.toml` buscando en *directorio* y sus padres (hasta 3)."""
    actual = Path(directorio).resolve()
    for candidato in (actual, *actual.parents[:3]):
        f = candidato / NOMBRE_CONFIG
        if f.is_file():
            return f
    return None
