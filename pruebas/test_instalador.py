"""Tests de la instalación en un proyecto destino: skill, AGENTS.md, CLAUDE.md y workflow."""

import pytest

from kit_iso import __version__, instalador
from kit_iso.instalador import (
    AGENTES,
    IDS_AGENTES,
    MARCA_FIN,
    MARCA_INICIO,
    agente,
    bloque_agents_md,
    insertar_bloque,
    instalar_agents_md,
    instalar_claude_md,
    instalar_skill,
    instalar_workflow,
    texto_skill,
    texto_workflow,
)

# ── Recursos empaquetados ─────────────────────────────────────────────────────


def test_skill_tiene_frontmatter_agent_skills():
    s = texto_skill()
    assert s.startswith("---\nname: kit-iso\n")
    assert "description:" in s.splitlines()[2]
    assert "kit-iso.toml" in s


def test_skill_menciona_todos_los_modulos():
    from kit_iso.perfiles import MODULOS

    s = texto_skill()
    for m in MODULOS:
        assert f"`{m}`" in s, m


def test_bloque_agents_md_delimitado():
    b = bloque_agents_md()
    assert b.startswith(MARCA_INICIO)
    assert b.rstrip().endswith(MARCA_FIN)


def test_workflow_usa_version_actual():
    assert f"Jordiprof/Normas-ISO@v{__version__}" in texto_workflow()
    assert "@v9.9.9" in texto_workflow("v9.9.9")


# ── Agentes ───────────────────────────────────────────────────────────────────


def test_agentes_cubren_los_cinco():
    assert set(IDS_AGENTES) == {"claude", "cursor", "codex", "opencode", "antigravity"}


def test_agente_desconocido_falla():
    with pytest.raises(ValueError, match="Agente desconocido"):
        agente("copilot")


def test_instalar_skill_todos_sin_duplicar(tmp_path):
    rutas = instalar_skill(tmp_path, list(IDS_AGENTES))
    # codex, opencode y antigravity comparten .agents/skills → 3 rutas distintas
    assert len(rutas) == 3
    assert (tmp_path / ".claude/skills/kit-iso/SKILL.md").exists()
    assert (tmp_path / ".cursor/skills/kit-iso/SKILL.md").exists()
    assert (tmp_path / ".agents/skills/kit-iso/SKILL.md").exists()
    assert (tmp_path / ".claude/skills/kit-iso/SKILL.md").read_text(
        encoding="utf-8"
    ) == texto_skill()


def test_instalar_skill_solo_un_agente(tmp_path):
    rutas = instalar_skill(tmp_path, ["cursor"])
    assert rutas == [tmp_path / ".cursor/skills/kit-iso/SKILL.md"]
    assert not (tmp_path / ".claude").exists()


def test_instalar_skill_global_usa_home(tmp_path, monkeypatch):
    monkeypatch.setattr(instalador.Path, "home", lambda: tmp_path)
    rutas = instalar_skill(tmp_path / "proyecto", ["codex"], global_=True)
    assert rutas == [tmp_path / ".codex/skills/kit-iso/SKILL.md"]


def test_instalar_skill_actualiza_si_cambia(tmp_path):
    destino = tmp_path / ".claude/skills/kit-iso/SKILL.md"
    destino.parent.mkdir(parents=True)
    destino.write_text("versión vieja", encoding="utf-8")
    instalar_skill(tmp_path, ["claude"])
    assert destino.read_text(encoding="utf-8") == texto_skill()


# ── AGENTS.md ─────────────────────────────────────────────────────────────────


def test_insertar_bloque_en_vacio():
    assert insertar_bloque("", "X\n") == "X\n"


def test_insertar_bloque_conserva_contenido_ajeno():
    r = insertar_bloque("# Mío\n\nreglas\n", f"{MARCA_INICIO}\nkit\n{MARCA_FIN}\n")
    assert r.startswith("# Mío\n\nreglas\n\n")
    assert r.endswith(f"{MARCA_FIN}\n")


def test_insertar_bloque_reemplaza_existente():
    viejo = f"# Mío\n\n{MARCA_INICIO}\nviejo\n{MARCA_FIN}\n\n## Después\n"
    r = insertar_bloque(viejo, f"{MARCA_INICIO}\nnuevo\n{MARCA_FIN}\n")
    assert "viejo" not in r
    assert "nuevo" in r
    assert r.count(MARCA_INICIO) == 1
    assert "## Después" in r


def test_instalar_agents_md_idempotente(tmp_path):
    instalar_agents_md(tmp_path)
    primero = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    instalar_agents_md(tmp_path)
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == primero
    assert primero.count(MARCA_INICIO) == 1


def test_instalar_claude_md_crea_y_no_duplica(tmp_path):
    instalar_claude_md(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    instalar_claude_md(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8").count("@AGENTS.md") == 1


def test_instalar_claude_md_conserva_existente(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Reglas\n", encoding="utf-8")
    instalar_claude_md(tmp_path)
    contenido = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert contenido.startswith("# Reglas\n")
    assert "@AGENTS.md" in contenido


# ── Workflow ──────────────────────────────────────────────────────────────────


def test_instalar_workflow_no_sobrescribe_sin_forzar(tmp_path):
    ruta = instalar_workflow(tmp_path)
    assert ruta == tmp_path / ".github/workflows/kit-iso.yml"
    ruta.write_text("mío", encoding="utf-8")
    assert instalar_workflow(tmp_path) is None
    assert ruta.read_text(encoding="utf-8") == "mío"
    assert instalar_workflow(tmp_path, forzar=True) == ruta
    assert "Jordiprof/Normas-ISO@" in ruta.read_text(encoding="utf-8")


def test_todos_los_agentes_tienen_rutas():
    for a in AGENTES:
        assert a.dir_proyecto.endswith("skills")
        assert a.dir_global
