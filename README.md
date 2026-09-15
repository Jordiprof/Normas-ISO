# kit-iso — Cumplimiento normativo como código

[![CI](https://github.com/Jordiprof/Normas-ISO/actions/workflows/ci.yml/badge.svg)](https://github.com/Jordiprof/Normas-ISO/actions/workflows/ci.yml)
[![Versión](https://img.shields.io/badge/versi%C3%B3n-1.1.0-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

Librería Python + CLI con **controles técnicos verificables** alineados con las normas que afectan al software: seguridad (ISO 27001), privacidad (ISO 27701 / RGPD), calidad (ISO 25010 / 5055 / 25012), usabilidad y accesibilidad (ISO 9241 / WCAG 2.1), inteligencia artificial (AI Act / ISO 42001) y ciberresiliencia (CRA).

Se instala en **cualquier proyecto** con una línea, decide **qué normas aplican a ese proyecto** mediante un triaje con evidencia, y deja instrucciones para que **cualquier agente de IA** (Claude Code, Codex, Cursor, OpenCode, Antigravity) las aplique.

> **Qué es y qué no es.** El kit ayuda a *implementar y demostrar* controles técnicos. **No certifica** ninguna norma: ISO 27001, 42001 y el ENS certifican sistemas de gestión (procesos, políticas, auditorías), no código. Úsalo como una capa de buenas prácticas verificables y como evidencia para una auditoría, no como un sello.

---

## Índice

- [Instalación en tu proyecto](#instalación-en-tu-proyecto)
- [Uso con agentes de IA](#uso-con-agentes-de-ia)
- [Triaje y `kit-iso.toml`](#triaje-y-kit-isotoml)
- [CLI](#cli)
- [Integración continua](#integración-continua)
- [Módulos y normas](#módulos-y-normas)
- [Uso como librería](#uso-como-librería)
- [Desarrollo del kit](#desarrollo-del-kit)
- [Hoja de ruta](#hoja-de-ruta)

---

## Instalación en tu proyecto

**Requisitos:** Python 3.10 o superior.

```bash
pip install "kit-iso[auditoria] @ git+https://github.com/Jordiprof/Normas-ISO.git@v1.1.0"
```

Fija siempre un tag (`@v1.1.0`): así cada proyecto actualiza cuando decide. Extras disponibles:

| Extra | Instala | Cuándo |
|---|---|---|
| `auditoria` | `bandit`, `radon` | Para `kit-iso auditar` (controles CWE y complejidad). Recomendado. |
| `bd` | `psycopg2-binary`, `mysql-connector-python` | Solo si usas `BaseDatosSegura`. |

Después, en la raíz del proyecto:

```bash
kit-iso init --detectar
```

`init` hace el triaje (siete preguntas de sí/no, pre-rellenadas con evidencia del propio repositorio), y genera:

| Archivo | Para qué |
|---|---|
| `kit-iso.toml` | Qué módulos aplican a este proyecto y **por qué**. Se commitea. |
| `AGENTS.md` (bloque delimitado) | Instrucciones que leen Codex, Cursor, OpenCode y Antigravity. Respeta lo que ya hubiera. |
| `CLAUDE.md` (línea `@AGENTS.md`) | Claude Code importa el mismo archivo. |
| `.claude/skills/kit-iso/`, `.cursor/skills/kit-iso/`, `.agents/skills/kit-iso/` | La skill `kit-iso` en formato [Agent Skills](https://agentskills.io); tres carpetas cubren los cinco agentes. |
| `.github/workflows/kit-iso.yml` (con `--ci`) | Auditoría en cada push y PR. |

Todo es idempotente: repetir `kit-iso init` conserva el triaje y refresca la skill. Para elegir agentes: `--agentes claude,cursor`. Para no tocar nada: `--solo-mostrar`.

Verifica:

```bash
kit-iso auditar .
```

---

## Uso con agentes de IA

Una vez hecho `kit-iso init`, en cualquier conversación con tu agente dentro del proyecto basta con:

> «Aplica el kit-iso según `kit-iso.toml`.»

El agente encuentra la skill, lee `kit-iso.toml`, aplica solo los módulos activos, corrige con el formato *veredicto / hallazgo / remediación* y verifica con `kit-iso auditar`. Si el proyecto aún no tiene `kit-iso.toml`, la skill le obliga a proponer el triaje con evidencia y **pedirte confirmación** antes de escribirlo; nunca aplica el kit entero «por si acaso».

| Agente | Lee las instrucciones de | Skill en |
|---|---|---|
| Claude Code | `CLAUDE.md` → `@AGENTS.md` | `.claude/skills/` |
| Cursor | `AGENTS.md` | `.cursor/skills/` |
| Codex CLI | `AGENTS.md` | `.agents/skills/` |
| OpenCode | `AGENTS.md` | `.agents/skills/` (también lee `.claude/skills/`) |
| Antigravity | `AGENTS.md` | `.agents/skills/` |

Para tener la skill disponible en **todos** tus proyectos sin instalarla en cada uno:

```bash
kit-iso skill --global --agentes claude,codex
```

---

## Triaje y `kit-iso.toml`

No todos los proyectos necesitan todas las normas. Auditar accesibilidad en una CLI sin HTML, o el CRA en un script interno, produce fallos que no significan nada y acaban ignorándose. El triaje lo evita:

| Pregunta | Si es «sí», activa | `--detectar` lo propone a partir de |
|---|---|---|
| (siempre) | `seguridad`, `calidad`, `iso_5055` | — |
| ¿Interfaz web / HTML? | `accesibilidad`, `usabilidad` | `.html`, `templates/`, flask/django/fastapi/react/vue… |
| ¿Base de datos? | `base_datos` | psycopg/sqlalchemy/mysql/sqlite/prisma…, `.sql` |
| ¿Datos personales? | `privacidad` | campos `email`, `dni`, `telefono`, `iban`… en código o esquemas |
| ¿IA / LLM? | `ai_act` | openai/anthropic/langchain/transformers/ollama… |
| ¿Producto distribuido con software? | `cra` | `pyproject.toml`/`setup.py`, `package.json` con `bin`, `Dockerfile` |
| ¿Datasets / analítica? | `iso_25012` | pandas/polars/duckdb…, `.csv`/`.parquet` |
| ¿Sector público español? | `ens` (pendiente en el kit) | no detectable: se pregunta siempre |

La heurística **propone**; la persona (o el agente, pidiendo confirmación) **decide**, y la decisión queda escrita:

```toml
[kit-iso]
version = "1.1.0"
perfil = "personalizado"
modulos = ["seguridad", "calidad", "iso_5055", "accesibilidad", "usabilidad", "privacidad"]
pendientes = []
umbral_complejidad = 10
excluir = ["ejemplos/*"]

[kit-iso.triaje]
web = { valor = true, justificacion = "3 archivo(s) .html; carpeta templates/; dependencias: flask" }
datos_personales = { valor = true, justificacion = "campos de datos personales en: modelos.py" }
ia = { valor = false, justificacion = "sin librerías de IA/LLM en las dependencias" }
# ...
```

Perfiles predefinidos para arrancar sin preguntas: `--perfil minimo | web | api-datos-personales | agente-llm | producto-cra | sector-publico`.

---

## CLI

```bash
kit-iso init [dir] [--detectar] [--perfil P] [--si] [--agentes a,b] [--ci] [--forzar] [--solo-mostrar]
kit-iso auditar <dir> [--formato markdown|json] [--salida ARCHIVO] [--config kit-iso.toml]
                      [--umbral-complejidad N] [--excluir GLOB]...
kit-iso skill [dir] [--agentes a,b] [--global]
```

`auditar` busca `kit-iso.toml` en el directorio y sus padres; los flags explícitos tienen prioridad sobre el archivo. Sin `kit-iso.toml`, ejecuta todos los controles.

### Controles automatizados

| Módulo | Norma | Control | Detecta |
|---|---|---|---|
| `seguridad` | ISO 27001 A.8.12 | Secretos hardcodeados | Contraseñas, API keys, tokens, claves PEM (8 patrones + entropía Shannon) |
| `iso_5055` | ISO/IEC 5055 | Debilidades CWE | Hallazgos de bandit mapeados a CWE, respetando `excluir` |
| `calidad` | ISO 25010 | Complejidad ciclomática | Funciones por encima del umbral McCabe |
| `privacidad` | ISO 27701 + RGPD art. 5 | PII en código | Emails, teléfonos, DNI/NIE, IBAN, IPs privadas (ignora docstrings) |
| `cra` | CRA art. 14 + ISO 29147 | Artefactos de divulgación | `SECURITY.md`, `.well-known/security.txt`, fuente de SBOM |
| `accesibilidad` | WCAG 2.1 / ISO 40500 | Accesibilidad HTML | 6 criterios sobre los `.html` del proyecto |

Los controles de módulos no activos aparecen como **omitidos**: quedan en el informe (constancia de que no aplican) pero no cuentan como fallo.

### Informe (el kit auditándose a sí mismo)

```markdown
# Informe de Auditoría — kit-iso v1.1.0

| Norma | Control | Estado |
|-------|---------|--------|
| ISO 27001 A.8.12 | Secretos hardcodeados en código fuente | ✅ ok |
| ISO/IEC 5055 | Calidad de código — debilidades CWE (bandit) | ✅ ok |
| ISO 25010 — Mantenibilidad | Complejidad ciclomática (umbral McCabe: 10) | ✅ ok |
| ISO 27701 + GDPR Art. 5 | PII en código fuente | ⏭️ omitido |
| CRA Art. 14 + ISO 29147 | Artefactos de divulgación de vulnerabilidades | ✅ ok |
| WCAG 2.1 / ISO 40500 | Accesibilidad HTML | ⏭️ omitido |

> **4/4 controles pasados** — Fallidos: 0 · Advertencias: 0 · Omitidos (no aplican): 2
```

### Códigos de salida

- `0` todos los controles activos pasan · `1` hay fallos · `2` error de uso (directorio o `kit-iso.toml` inválidos).

---

## Integración continua

`kit-iso init --ci` deja un workflow que usa la action de este repositorio:

```yaml
- uses: actions/checkout@v4
- uses: Jordiprof/Normas-ISO@v1.1.0
  with:
    directorio: .          # opcional
    argumentos: ""         # flags extra para `kit-iso auditar`
```

La action instala el kit (misma versión que el tag), ejecuta `kit-iso auditar`, vuelca el informe en el resumen del job y lo sube como artefacto. Falla el job si hay controles fallidos.

---

## Módulos y normas

| Módulo | Norma | Clases principales | Resumen de la norma |
|---|---|---|---|
| `seguridad` | ISO 27001 | `ToolkitSeguridad` (Fernet, clave en `KIT_ISO_CLAVE`), `ValidadorSeguridad`, `ValidadorContrasenasSeguras` (argon2/bcrypt), `ValidadorSecurityHeaders`, `ValidadorTLS` | Seguridad de la información: accesos, cifrado, secretos, registro. Certificable. |
| `base_datos` | ISO 27001 | `BaseDatosSegura` (SQL parametrizado, whitelist de identificadores, commit/rollback) | Idem, aplicado al acceso a datos. Extra `[bd]`. |
| `privacidad` | ISO 27701 + RGPD + 27017/27018 | `DetectorPII` (7 tipos), `EnmascaradorLogs`, `ChecklistCloudPrivacidad` | Datos personales: minimización, derechos, encargados y nube. |
| `calidad` | ISO 25010 | `HerramientasCalidad` (McCabe con radon, cobertura, rendimiento) | Modelo de calidad del software: mantenibilidad, eficiencia, fiabilidad. |
| `iso_5055` | ISO/IEC 5055 | `AnalizadorISO5055` (bandit → CWE) | Calidad del código medida por debilidades concretas (CWE). |
| `iso_25012` | ISO/IEC 25012 | `ValidadorCalidadDatos` (completitud, exactitud, consistencia) | Calidad de los datos. |
| `usabilidad` | ISO 9241 | `HerramientasUsabilidad` | Interfaces eficaces, eficientes y satisfactorias. |
| `accesibilidad` | ISO 40500 / WCAG 2.1 | `HerramientasAccesibilidad` (criterios 1.1.1, 1.3.1, 1.4.3, 2.4.4, 3.1.1, 3.3.2) | Accesibilidad web para personas con discapacidad. |
| `ai_act` | AI Act + ISO 42001 / 23894 | `ClasificadorRiesgoIA`, `TransparenciaIA` (art. 50), `RegistroDecisionesIA` (art. 12), `DocumentacionTecnicaAnexoIV`, `RegistroModelosIA`, `RegistroRiesgosIA` | Ley europea de IA por niveles de riesgo; el art. 50 (avisar de que se habla con una IA) aplica desde el 2/8/2026. ISO 42001: gestión de IA responsable. |
| `cra` | CRA + ISO 29147 / 30111 | `GeneradorSBOM` (CycloneDX), `GeneradorPoliticaVulnerabilidades`, `ChecklistSecureByDesign`, `PlantillaReporteVulnerabilidad` | Productos con software: seguro por diseño, SBOM, divulgación y gestión de vulnerabilidades. |
| `ens` | ENS (RD 311/2022) | pendiente | Obligatorio para el sector público español y sus proveedores. |

`kit_iso.ia` se mantiene solo por compatibilidad: usa `kit_iso.ai_act`.

---

## Uso como librería

```python
from kit_iso.seguridad import ToolkitSeguridad
from kit_iso.seguridad.validador import ValidadorSeguridad
from kit_iso.privacidad import DetectorPII
from kit_iso.ai_act import TransparenciaIA

seg = ToolkitSeguridad()                       # clave desde KIT_ISO_CLAVE; falla explícito si no existe
cifrado = seg.encriptar_datos("dato sensible")

ValidadorSeguridad().analizar_codigo("api_key = '12345'")
# → ["RIESGO ISO 27001: api_key hardcodeada (patrón: ...)"]

DetectorPII().analizar("Contacta con juan@empresa.com")
# → {"contiene_pii": True, "hallazgos": [{"tipo": "email", ...}]}
```

Auditoría programática (mismo resultado que la CLI):

```python
from kit_iso._auditoria import ejecutar_auditoria, generar_markdown
from kit_iso.perfiles import cargar

cfg = cargar("kit-iso.toml")
resultados = ejecutar_auditoria(".", modulos=cfg.modulos, excluir=cfg.excluir)
print(generar_markdown(resultados))
```

**Configuración sensible por variables de entorno** (`.env`, nunca commiteado; plantilla en [`.env.example`](.env.example)). Genera la clave Fernet una sola vez:

```bash
python -c "from kit_iso.seguridad import ToolkitSeguridad; print(ToolkitSeguridad.generar_clave().decode())"
```

Si la clave se pierde, los datos cifrados son irrecuperables; si se expone, rótala y recifra.

**Contrato público (SemVer):** las clases exportadas por cada módulo, `ejecutar_auditoria`, el formato de `kit-iso.toml`, los marcadores de `AGENTS.md` y los comandos de la CLI con sus flags y códigos de salida. Todo lo que empieza por `_` es interno. Los type hints se distribuyen (`py.typed`).

---

## Desarrollo del kit

```bash
git clone https://github.com/Jordiprof/Normas-ISO.git
cd Normas-ISO
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -e ".[dev,auditoria]"
pytest pruebas/ -v
kit-iso auditar .        # el kit se audita con su propio kit-iso.toml
```

```
Normas-ISO/
├── src/kit_iso/
│   ├── cli.py                 # init · auditar · skill
│   ├── _auditoria.py          # controles y consolidación del informe
│   ├── perfiles.py            # triaje, perfiles y kit-iso.toml
│   ├── instalador.py          # skill, AGENTS.md, CLAUDE.md, workflow
│   ├── recursos/              # SKILL.md, bloque AGENTS.md y plantilla de CI (package-data)
│   └── <un módulo por norma>/ # seguridad, privacidad, calidad, ai_act, cra, ...
├── pruebas/                   # tests (pytest)
├── ejemplos/                  # API FastAPI de demostración y auditoría programática
├── documentacion/adr/         # registros de decisión de arquitectura
├── action.yml                 # GitHub Action reutilizable
├── kit-iso.toml               # triaje del propio kit
├── GUARDARRAILES.md           # reglas de ingeniería para quien desarrolla ESTE repo
├── SECURITY.md                # divulgación responsable (CRA / ISO 29147)
└── CHANGELOG.md
```

La suite tiene **249 tests** (pytest 8, Python 3.10–3.13); los que dependen de `argon2-cffi`, `bcrypt` o `radon` se saltan si no están instalados. CI en GitHub Actions: `ruff`, `black`, `bandit`, `pip-audit`, `mypy`, `pytest`, autoauditoría y prueba de la action. Convenciones de trabajo en [GUARDARRAILES.md](GUARDARRAILES.md); decisiones estructurales en [documentacion/adr/](documentacion/adr/README.md).

---

## Hoja de ruta

Versión actual: **1.1.0** (septiembre 2026). Historial completo en [CHANGELOG.md](CHANGELOG.md).

Siguiente fase (pendiente, sin fecha):

- **`ens`**: valoración de las cinco dimensiones (confidencialidad, integridad, trazabilidad, autenticidad, disponibilidad), categoría del sistema y mapeo a las medidas del Anexo II.
- **Seguridad de agentes y LLM** (OWASP Top 10 LLM): detección de inyección de prompt directa e indirecta, validación de la salida del modelo con esquema, inventario de herramientas con permisos mínimos, aprobación humana en acciones irreversibles, límites de iteraciones y coste.
- **Trazabilidad a prueba de manipulación**: registro estructurado por ejecución encadenado con hashes, con retención definida.
- **Borrado en cascada** (RGPD art. 17) con prueba de fuga entre usuarios.
- **AI Act**: rol proveedor / responsable del despliegue, art. 22 y calendario del Reglamento (UE) 2026/1744.
- **Plantillas de Fase 0**: ficha del sistema, clasificación de la información, análisis de riesgos, DPIA / ISO 42005, declaración de aplicabilidad, evaluación de proveedores.

---

Licencia [MIT](LICENSE). Vulnerabilidades: ver [SECURITY.md](SECURITY.md).
