"""Instalación del kit en un proyecto destino: skill para agentes, AGENTS.md, CLAUDE.md y CI.

Todo es idempotente: se puede ejecutar `kit-iso init` varias veces sin duplicar nada.
Nunca se sobrescribe contenido ajeno; el bloque de AGENTS.md va delimitado por marcadores.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from kit_iso import __version__

MARCA_INICIO = "<!-- kit-iso:inicio -->"
MARCA_FIN = "<!-- kit-iso:fin -->"
NOMBRE_SKILL = "kit-iso"


@dataclass(frozen=True)
class Agente:
    id: str
    nombre: str
    dir_proyecto: str  # relativo a la raíz del proyecto
    dir_global: str  # relativo a ~


# Rutas de descubrimiento de skills (formato Agent Skills, SKILL.md) por agente.
# `.agents/skills/` es la ruta común que leen Codex, OpenCode y Antigravity.
AGENTES: tuple[Agente, ...] = (
    Agente("claude", "Claude Code", ".claude/skills", ".claude/skills"),
    Agente("cursor", "Cursor", ".cursor/skills", ".cursor/skills"),
    Agente("codex", "Codex CLI", ".agents/skills", ".codex/skills"),
    Agente("opencode", "OpenCode", ".agents/skills", ".config/opencode/skills"),
    Agente("antigravity", "Antigravity", ".agents/skills", ".gemini/antigravity/skills"),
)
IDS_AGENTES: tuple[str, ...] = tuple(a.id for a in AGENTES)


def agente(id_: str) -> Agente:
    for a in AGENTES:
        if a.id == id_:
            return a
    raise ValueError(f"Agente desconocido: {id_!r}. Disponibles: {', '.join(IDS_AGENTES)}")


def _recurso(nombre: str) -> str:
    return (resources.files("kit_iso.recursos") / nombre).read_text(encoding="utf-8")


def texto_skill() -> str:
    return _recurso(f"skill/{NOMBRE_SKILL}/SKILL.md")


def bloque_agents_md() -> str:
    return _recurso("AGENTS.kit-iso.md").strip() + "\n"


def texto_workflow(version: str | None = None) -> str:
    return _recurso("workflow.yml").replace("__VERSION__", version or f"v{__version__}")


# ── Skill ─────────────────────────────────────────────────────────────────────


def instalar_skill(raiz: Path, agentes: list[str], *, global_: bool = False) -> list[Path]:
    """Copia la skill a la carpeta de cada agente. Devuelve las rutas escritas (sin duplicados)."""
    contenido = texto_skill()
    escritas: list[Path] = []
    destinos: list[Path] = []
    for id_ in agentes:
        a = agente(id_)
        base = Path.home() / a.dir_global if global_ else raiz / a.dir_proyecto
        destino = base / NOMBRE_SKILL / "SKILL.md"
        if destino not in destinos:
            destinos.append(destino)
    for destino in destinos:
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.exists() or destino.read_text(encoding="utf-8") != contenido:
            destino.write_text(contenido, encoding="utf-8")
        escritas.append(destino)
    return escritas


# ── AGENTS.md / CLAUDE.md ─────────────────────────────────────────────────────


def insertar_bloque(texto: str, bloque: str) -> str:
    """Inserta o reemplaza el bloque delimitado por los marcadores en *texto*."""
    bloque = bloque.strip() + "\n"
    if MARCA_INICIO in texto and MARCA_FIN in texto:
        ini = texto.index(MARCA_INICIO)
        fin = texto.index(MARCA_FIN) + len(MARCA_FIN)
        resto = texto[fin:]
        resto = resto.removeprefix("\n")
        return texto[:ini] + bloque + resto
    if not texto:
        return bloque
    return texto.rstrip("\n") + "\n\n" + bloque


def instalar_agents_md(raiz: Path) -> Path:
    ruta = raiz / "AGENTS.md"
    actual = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
    nuevo = insertar_bloque(actual, bloque_agents_md())
    if nuevo != actual:
        ruta.write_text(nuevo, encoding="utf-8")
    return ruta


def instalar_claude_md(raiz: Path) -> Path:
    """Claude Code lee CLAUDE.md; la línea `@AGENTS.md` importa el archivo común."""
    ruta = raiz / "CLAUDE.md"
    linea = "@AGENTS.md"
    if not ruta.exists():
        ruta.write_text(f"{linea}\n", encoding="utf-8")
        return ruta
    actual = ruta.read_text(encoding="utf-8")
    if not any(ln.strip() == linea for ln in actual.splitlines()):
        ruta.write_text(actual.rstrip("\n") + f"\n\n{linea}\n", encoding="utf-8")
    return ruta


# ── CI ────────────────────────────────────────────────────────────────────────


def instalar_workflow(raiz: Path, *, forzar: bool = False) -> Path | None:
    ruta = raiz / ".github" / "workflows" / "kit-iso.yml"
    if ruta.exists() and not forzar:
        return None
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto_workflow(), encoding="utf-8")
    return ruta
