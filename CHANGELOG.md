# Changelog — kit-cumplimiento-iso

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)  
Versionado: [Semantic Versioning 2.0.0](https://semver.org/lang/es/)

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
