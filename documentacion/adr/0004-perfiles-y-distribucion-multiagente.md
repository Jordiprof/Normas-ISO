# ADR 0004 — Perfiles por proyecto y distribución multi-agente

**Estado:** Aceptada · **Fecha:** 2026-09 · **Reversibilidad:** Media (el formato de `kit-iso.toml` y los marcadores de `AGENTS.md` son contrato público desde v1.1.0).

## Contexto

El kit nació como repositorio aislado: se clonaba, se instalaba en editable y se usaba desde dentro. El objetivo desde v1.1.0 es instalarlo en **cualquier proyecto** y que **cualquier agente de IA** (Claude Code, Codex, Cursor, OpenCode, Antigravity) sepa aplicarlo. Dos problemas:

1. No todos los proyectos necesitan todas las normas. Auditar accesibilidad en una CLI sin HTML, o el CRA en un script interno, produce fallos que no significan nada y acaban ignorándose.
2. Cada agente tiene su propio mecanismo de instrucciones. Mantener cinco configuraciones distintas no es viable.

## Decisión

**Triaje explícito por proyecto.** `kit-iso init` hace siete preguntas de sí/no (web, base de datos, datos personales, IA, producto distribuido, datasets, sector público) y escribe `kit-iso.toml` con la lista de módulos activos y, para cada respuesta, su **justificación**. `--detectar` pre-rellena las respuestas con heurísticas sobre el repositorio y muestra la evidencia; la decisión final es siempre del responsable (o del agente, que debe pedir confirmación). `kit-iso auditar` lee ese archivo y marca los controles de módulos no activos como `omitido`: aparecen en el informe (queda constancia de que no aplican) pero no cuentan como fallo.

**Dos piezas estándar para los agentes, no una por fabricante:**

- **`AGENTS.md`** con un bloque delimitado por marcadores (`<!-- kit-iso:inicio -->` … `<!-- kit-iso:fin -->`), insertado o reemplazado sin tocar el contenido ajeno. Lo leen Codex, Cursor, OpenCode y Antigravity. Claude Code lee `CLAUDE.md`, donde se añade la línea `@AGENTS.md`.
- **Una skill en formato Agent Skills** (`SKILL.md` con frontmatter `name`/`description`), que vive una sola vez dentro del paquete (`kit_iso/recursos/skill/kit-iso/`) y se copia a las carpetas de descubrimiento: `.claude/skills/`, `.cursor/skills/` y `.agents/skills/` (compartida por Codex, OpenCode y Antigravity). Tres carpetas cubren los cinco agentes.

**Dependencias mínimas en runtime.** Los drivers de base de datos pasan al extra `[bd]` y bandit/radon al extra `[auditoria]`, con importación tolerante: instalar el kit en un proyecto no arrastra PostgreSQL ni MySQL.

## Alternativas consideradas

- **Detección automática sin confirmar**: descartada. Un falso negativo en "¿trata datos personales?" desactiva el RGPD en silencio. La heurística propone; la persona decide y queda escrito por qué.
- **Configuración en `pyproject.toml` (`[tool.kit-iso]`)**: descartada por ahora. Un archivo propio funciona igual en proyectos que no son Python (Node, mixtos) y es más visible para el agente.
- **Un archivo de instrucciones por agente** (`.cursorrules`, `GEMINI.md`, `.codex/instructions`…): descartada. Se desincronizan y varios ya están obsoletos; `AGENTS.md` + Agent Skills son los dos estándares que todos convergen a leer.
- **Vendorizar el código del kit en cada proyecto**: descartada. Cada copia se queda atrás; la instalación por `pip` con tag fija la versión y permite actualizar.

## Consecuencias

- ✅ Un proyecto sin HTML ni producto distribuido tiene una auditoría limpia y honesta: 4/4 aplicables, 2 omitidos con motivo.
- ✅ El mismo `SKILL.md` sirve a los cinco agentes; se actualiza con `kit-iso init` o `kit-iso skill`.
- ✅ `kit-iso.toml` es evidencia auditable: qué aplica, qué no y por qué.
- ⚠️ Las rutas de descubrimiento de skills las fijan los fabricantes y pueden cambiar; viven en una sola tabla (`instalador.AGENTES`).
- ⚠️ El triaje añade un paso antes de auditar. Es deliberado: sin `kit-iso.toml`, la skill obliga al agente a hacerlo y a pedir confirmación.
