# Changelog — kit-cumplimiento-iso

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)  
Versionado: [Semantic Versioning 2.0.0](https://semver.org/lang/es/)

---

## [1.1.0] — 2026-09-15

El kit pasa de repositorio aislado a **herramienta instalable en cualquier proyecto** y usable desde **cualquier agente de IA** (Claude Code, Codex, Cursor, OpenCode, Antigravity). Decisión de diseño en [ADR 0004](documentacion/adr/0004-perfiles-y-distribucion-multiagente.md).

### Añadido

- **`kit-iso init`**: triaje del proyecto (siete preguntas de sí/no) que genera `kit-iso.toml` con los módulos que aplican y la **justificación** de cada respuesta. `--detectar` pre-rellena las respuestas con heurísticas sobre el repositorio (HTML, drivers de BD, campos de datos personales, librerías de IA, empaquetado, datasets) y muestra la evidencia; `--perfil` (`minimo`, `web`, `api-datos-personales`, `agente-llm`, `producto-cra`, `sector-publico`) arranca sin preguntas; `--si` acepta las propuestas; `--solo-mostrar` no escribe nada. Idempotente: repetirlo conserva el triaje y refresca el resto.
- **Skill `kit-iso`** en formato Agent Skills (`SKILL.md` con frontmatter), empaquetada en `kit_iso/recursos/` y copiada por `init` a `.claude/skills/`, `.cursor/skills/` y `.agents/skills/` (tres carpetas cubren los cinco agentes). `kit-iso skill [--global]` la instala por separado. Obliga al agente a leer `kit-iso.toml` antes de auditar y a pedir confirmación del triaje si no existe.
- **Bloque en `AGENTS.md`** delimitado por `<!-- kit-iso:inicio/fin -->` (se inserta o reemplaza sin tocar contenido ajeno) y **`CLAUDE.md`** con `@AGENTS.md` para Claude Code.
- **`action.yml`**: GitHub Action composite reutilizable (`uses: Jordiprof/Normas-ISO@v1.1.0`) que instala el kit, audita, vuelca el informe en el resumen del job y lo sube como artefacto. `kit-iso init --ci` genera el workflow que la usa.
- **`kit-iso auditar` lee `kit-iso.toml`** (del directorio o sus padres, o `--config`) y marca los controles de módulos no activos como **`omitido`** (⏭️): quedan en el informe pero no cuentan como fallo. Los flags explícitos prevalecen sobre el archivo. El JSON incluye `modulos`, `config`, `pendientes` y `resumen.omitidos`.
- **Módulo `perfiles`** (`detectar`, `cargar`, `guardar`, `Configuracion`) y **`instalador`** (`instalar_skill`, `instalar_agents_md`, `instalar_claude_md`, `instalar_workflow`) como API pública.
- **Extras de instalación**: `kit-iso[auditoria]` (bandit + radon) y `kit-iso[bd]` (drivers PostgreSQL/MySQL). `tomli` solo en Python 3.10.
- **`kit-iso.toml` del propio repositorio**: el kit se audita a sí mismo con su propio mecanismo (4/4 controles aplicables, 2 omitidos con motivo).
- **CI**: matriz Python 3.10/3.12, `pip-audit`, autoauditoría con `kit-iso auditar .` y prueba de la action contra el propio repo.
- Tests: 174 → **249** (`test_perfiles.py`, `test_instalador.py`, CLI `init`/`skill`/`auditar` con toml).

### Cambiado

- **Licencia: de MIT a propietaria** (todos los derechos reservados). `pyproject.toml` declara `license = "LicenseRef-Proprietary"` (PEP 639).
- **`pytest` ya no es requisito de importación de `calidad`** (solo lo usan `medir_cobertura` y `run_tests`): el control de complejidad funciona en proyectos sin pytest.
- **Los drivers de base de datos ya no son dependencia obligatoria**: `base_datos` los importa de forma tolerante y `BaseDatosSegura` falla con instrucción de instalación (`pip install "kit-iso[bd]"`) si faltan. Instalar el kit en un proyecto ya no arrastra `psycopg2` ni `mysql-connector`.
- **bandit se invoca con el intérprete actual** (`python -m bandit`), respeta `excluir` (`-x`) y tolera la barra de progreso que escribe en stdout con muchos archivos. El control CWE propaga el mensaje de error real en vez de un estado `error` mudo.
- **README** reescrito: instalación en otro proyecto, uso con agentes, triaje, CLI, CI, tabla de normas con resumen de una línea, estructura del repo y hoja de ruta.
- **`requirements.txt`** ahora solo para desarrollar el kit (equivale a `pip install -e ".[dev,auditoria,demo]"`).
- Refactor de complejidad (umbral 10 del propio kit): `ejecutar_auditoria`, `generar_markdown`, `_sin_docstrings`, `cmd_auditar`, `AnalizadorISO5055.analizar_directorio`, `ValidadorCalidadDatos.validar_exactitud`, `perfiles.indicadores`. Sin cambios de comportamiento.

### Eliminado

- `PLAN-MEJORA.md` (historial ya recogido aquí; la hoja de ruta vive en el README) y el `SKILL.md` de la raíz (desactualizado: apuntaba al stub `kit_iso.ia` e ignoraba seis módulos). La skill vive ahora en el paquete.

## [1.0.2] — 2026-07-16

Arregla el CI, que empezó a fallar al pushear todo el trabajo de las Fases 2-4 por primera vez (el workflow existía desde la Fase 1, pero nunca había corrido contra este código en un entorno limpio). Sin cambios de comportamiento.

### Corregido

- **`ruff check` (37 issues) y `black --check` (2 archivos)**: deuda de estilo acumulada durante las Fases 2-4, nunca verificada porque ruff/black no estaban instalados en local hasta ahora. Desglose:
  - 7 atributos de clase mutables (`RUF012`) anotados como `ClassVar` (tablas de lookup de solo lectura: patrones, controles, secciones — nunca se mutan).
  - 6 `with` anidados combinados en una sola sentencia (`SIM117`).
  - 2 `subprocess.run` con `check=False` explícito (ya se gestionaba el returncode manualmente).
  - Los `except Exception` deliberados (saltar un archivo ilegible durante un escaneo, o convertir cualquier fallo de un control en estado `"error"` en vez de crashear la CLI) llevan ahora `# noqa: BLE001, S110` junto al `# nosec B110` de bandit — antes solo bandit los reconocía; ruff no entiende la sintaxis de bandit y los seguía marcando.
  - 1 `if` anidado colapsado (`SIM102`), 1 concatenación implícita de f-strings parentizada (`ISC004`).
- Verificado: bandit sigue suprimiendo las mismas 9 excepciones (sin regresión de cobertura de seguridad), mypy sigue limpio, 177 tests pasan, auto-auditoría 6/6.

---

## [1.0.1] — 2026-07-16

Pulido de empaquetado y documentación para publicación (sin cambios de comportamiento ni de API).

### Añadido

- **Metadata completa en `pyproject.toml`**: `readme`, `license` (SPDX `MIT`) + `license-files`, `authors`, `keywords`, `classifiers` (incl. `Typing :: Typed` y versiones de Python 3.10–3.13) y `[project.urls]` (Repository, Changelog). Antes la página de PyPI habría salido vacía.
- **Marcador `py.typed`**: la librería ya enviaba type hints, pero ahora los **exporta** a los consumidores (PEP 561) — sus type checkers los aprovechan.
- **Verificación de tipos con mypy**: config en `pyproject.toml` + paso en CI. La suite de tipos pasa limpia sobre los 16 módulos.
- **Registros de decisión de arquitectura (ADR)** en `documentacion/adr/`: layout por norma, separación `_auditoria`/`cli`, clave Fernet persistente.
- **Sección "Contrato público vs interno"** en el README: qué es API estable (clases validadoras, CLI) y qué es interno (`_auditoria`, prefijo `_`).

### Corregido

- **`LICENSE` roto**: era una plantilla a medio rellenar (`[Nombre Empresa]` + un comentario "buscar template" y el texto MIT truncado). Reemplazado por el texto MIT completo y válido.
- **Bugs latentes de `None` detectados por mypy** (habrían petado en runtime en casos borde):
  - `_auditoria._sin_docstrings`: `range()` recibía `end_lineno`, que la AST devuelve como `None` en algunos nodos → `TypeError`. Ahora con guarda.
  - `seguridad.ValidadorTLS.verificar_tls`: `getpeercert()` puede devolver `None` en conexiones sin certificado verificado → `AttributeError` al hacer `.get()`. Ahora con `or {}`.
  - `accesibilidad`: atributos HTML multivaluados de BeautifulSoup (lista) rompían `.lower()`/indexado; se normalizan a `str` con un helper `_attr`.

---

## [1.0.0] — 2026-07-15

### Añadido

- **CLI unificada** (`kit-iso auditar <directorio>`):
  - Ejecuta 6 controles automatizados y emite informe Markdown o JSON.
  - Mapeo *norma → control → evidencias → veredicto* en una sola pasada.
  - Flags: `--formato json|markdown`, `--salida ARCHIVO`, `--umbral-complejidad N`, `--excluir GLOB` (repetible).
  - El control de PII excluye docstrings del escaneo (los emails/teléfonos de ejemplo en documentación no son datos personales reales).
  - El propio kit pasa su auditoría **6/6**: comentarios saneados en `usabilidad`, supresiones `# nosec` justificadas en `iso_5055` y `privacidad`, y artefactos `SECURITY.md` + `.well-known/security.txt`.
- **Tests robustos a dependencias opcionales**: los 9 tests que ejercitan `argon2-cffi`, `bcrypt` o `radon` ahora se saltan (`skip`) con motivo explícito si la librería no está instalada, en vez de fallar con `ImportError`. El comportamiento de fallo explícito sin la librería sigue cubierto por tests dedicados que no dependen de tenerla instalada.
  - Exit code 1 cuando hay fallos (integración directa con CI/CD).
  - Invocable también como `python -m kit_iso.cli`.
- **Entry point** `[project.scripts]` en `pyproject.toml`: `kit-iso = "kit_iso.cli:main"`.
- **Módulo `_auditoria`**: lógica central de auditoría separada de la CLI para testabilidad.
- **Tests** `pruebas/test_cli.py`: 18 tests cubriendo markdown, JSON, flags, exit codes y subprocess.

### Controles disponibles en `kit-iso auditar`

| Norma | Control |
|-------|---------|
| ISO 27001 A.8.12 | Secretos hardcodeados en código fuente |
| ISO/IEC 5055 | Debilidades CWE (bandit → CWE mapping) |
| ISO 25010 | Complejidad ciclomática (McCabe, radon) |
| ISO 27701 + GDPR Art. 5 | PII en código fuente |
| CRA Art. 14 + ISO 29147 | Artefactos de divulgación de vulnerabilidades |
| WCAG 2.1 / ISO 40500 | Accesibilidad HTML (si hay archivos .html) |

---

## [0.4.0] — 2026-07-14 (Fase 3)

### Añadido

- **Módulo `ai_act`** — AI Act (Reg. EU 2024/1689) + ISO 42001 + ISO 23894:
  - `ClasificadorRiesgoIA`: clasifica en prohibido/alto/limitado/mínimo según cuestionario.
  - `TransparenciaIA`: avisos chatbot art. 50 en es/en/ca/fr, marcado de contenido generado.
  - `RegistroDecisionesIA`: logging estructurado art. 12 (alto riesgo).
  - `DocumentacionTecnicaAnexoIV`: plantilla Markdown con 10 secciones obligatorias.
  - `RegistroModelosIA` (ISO 42001): inventario de modelos en producción por nivel de riesgo.
  - `RegistroRiesgosIA` (ISO 23894): registro probabilidad × impacto con fases del ciclo de vida.
- **Módulo `cra`** — Cyber Resilience Act + ISO 29147/30111:
  - `GeneradorSBOM`: CycloneDX JSON 1.5 desde requirements.txt o lista.
  - `GeneradorPoliticaVulnerabilidades`: security.txt (RFC 9116) y SECURITY.md.
  - `ChecklistSecureByDesign`: 10 controles CRA Art. 13 con puntuación porcentual.
  - `PlantillaReporteVulnerabilidad`: plantillas 24 h / 72 h / 14 días para ENISA.
- **Módulo `privacidad`** — ISO 27701 + ISO 27017/27018 + GDPR:
  - `DetectorPII`: 7 tipos (email, teléfono ES, tarjeta, DNI, NIE, IBAN, IP privada, contraseña en log).
  - `EnmascaradorLogs`: reemplaza PII por `[TIPO]` con filtro `logging.Filter`.
  - `ChecklistCloudPrivacidad`: checklists ISO 27017 (6 controles) e ISO 27018 (6 controles).
- **Módulo `iso_5055`** — ISO/IEC 5055:
  - `AnalizadorISO5055`: mapeo bandit test_id → CWE (50+ entradas), resumen por categoría.
- **Módulo `iso_25012`** — ISO/IEC 25012:
  - `ValidadorCalidadDatos`: completitud, exactitud (tipos/rangos/patrones) y consistencia (lambdas).
- Módulo `ia/__init__.py` actualizado para re-exportar desde `ai_act`.
- Tests: 68 → 156 tests (88 nuevos).

---

## [0.3.0] — 2026-07-13 (Fase 2)

### Añadido

- **`ValidadorSeguridad`** refactorizado con 8 patrones críticos:
  JWT/Bearer, clave PEM, clave AWS IAM, token GitHub, token Slack, más entropía Shannon
  configurable para detectar secretos de alta entropía.
- **`ValidadorContrasenasSeguras`**: hashing argon2-cffi y bcrypt con verificación.
- **`ValidadorSecurityHeaders`**: 5 headers obligatorios (HSTS, X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy) con validación de valores.
- **`ValidadorTLS`**: verificación de protocolo, caducidad de certificado y CN via `ssl`.
- **WCAG 2.1** ampliado a 6 criterios: 1.1.1 alt text, 1.3.1 jerarquía de headings,
  1.4.3 contraste (sRGB), 2.4.4 enlaces descriptivos, 3.1.1 atributo lang, 3.3.2 etiquetas de formulario.
- **ISO 25010** ampliado: `medir_complejidad` (radon, McCabe) y `medir_cobertura` (coverage.py).
- Tests: 20 → 68 tests (48 nuevos).

### Cambiado

- Dependencias de desarrollo añadidas: `argon2-cffi`, `bcrypt`, `radon`, `coverage`.

---

## [0.2.0] — 2026-07-12 (Fase 1 — corrección de bugs críticos)

### Corregido

- **Clave Fernet por instancia** (pérdida de datos irrecuperable): cada instancia de
  `EncriptadorDatos` generaba su propia clave → datos cifrados en una sesión eran
  indescifrable en la siguiente. Corregido requiriendo `KIT_ISO_CLAVE` del entorno.
- **INSERT sin commit** (pérdida silenciosa de datos): `ejecutar_query` no hacía `commit`
  en escrituras. Separado en `consulta_segura` (SELECT + fetchall) y `ejecutar_segura`
  (INSERT/UPDATE/DELETE + commit + rollback automático en excepción).
- **Módulo IA con `NameError`**: importaciones de `torch`/`langchain`/`langgraph` fallaban
  en runtime. Reemplazado por `NotImplementedError` honesto.

### Eliminado

- Dependencias: `torch`, `langchain`, `langgraph` (~2 GB, sin uso real).

---

## [0.1.0] — 2026-07-11 (versión inicial)

Versión inicial con implementaciones parciales y tres bugs críticos de seguridad/integridad.
Ver historial de commits para detalles.
