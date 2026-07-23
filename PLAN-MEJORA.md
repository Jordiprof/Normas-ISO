# Plan de mejora — kit-cumplimiento-iso (hacia v1.0)

Objetivo: pasar de una colección de clases con marketing ISO a una **herramienta de "cumplimiento como código"**: controles técnicos automatizables, verificados con tests, con informe consolidado. El kit ayuda a cumplir; **no certifica** (las ISO de gestión certifican procesos, no código).

## ✅ Fase 1 — Reparar lo roto (COMPLETADA — v0.2.0, julio 2026)

- [x] Clave Fernet persistente vía `KIT_ISO_CLAVE` (antes: clave nueva por instancia → datos irrecuperables). Falla explícita si no hay clave.
- [x] `base_datos`: `commit`/`rollback` en escrituras (`ejecutar_segura`), `consulta_segura` solo lectura (antes: INSERT sin commit + `fetchall()` sobre INSERT), context manager, whitelist configurable, typo corregido.
- [x] Módulo `ia` retirado a stub explícito con `NotImplementedError` (antes: `NameError` por función inexistente, vendido como ISO 42001).
- [x] Dependencias: fuera `torch`/`langchain`/`langgraph` (sin uso real, ~2 GB); `pyproject` con `optional-dependencies` (dev/demo) y `requires-python`.
- [x] Tests reales: 2 → 20, incluyendo regresión de los tres bugs (clave, commit, fetchall). `test_seguridad.py` ahora testea seguridad.
- [x] CI: `ruff` + `black` + `bandit` + `pytest`, con `pip install -e .`.
- [x] `.env` verificado como nunca commiteado; `.env.example` saneado (tenía restos de markdown) con `KIT_ISO_CLAVE`; `.gitignore` + `src/*.egg-info/`.
- [x] README honesto (qué es / qué no es) y comentarios narradores eliminados de los módulos tocados.

## ✅ Fase 2 — Profundizar las normas existentes (COMPLETADA — v0.3.0, julio 2026)

- [x] **ISO 27001 `validador.py`**: `ValidadorSeguridad` ampliado (Bearer/JWT, PEM, AWS IAM, GitHub token, Slack, entropía Shannon configurable); `ValidadorContrasenasSeguras` (argon2/bcrypt, salt aleatorio, resistencia a timing); `ValidadorSecurityHeaders` (HSTS, X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy con verificación de valores); `ValidadorTLS` (certif. válido, versión TLS obsoleta detectada).
- [x] **WCAG 2.1 `accesibilidad`**: 6 criterios (1.1.1 alt, 1.3.1 jerarquía encabezados, 1.4.3 contraste hex inline, 2.4.4 enlaces descriptivos, 3.1.1 lang, 3.3.2 labels). API unificada con lista de hallazgos por criterio.
- [x] **ISO 25010 `calidad`**: `medir_complejidad` con radon (rangos McCabe A-F, umbral configurable); `medir_cobertura` con coverage (umbral configurable); `medir_performance` intacto.
- [x] Tests: 20 → 68 (18 nuevos en seguridad, 18 en accesibilidad, 12 en calidad). Dependencias: `argon2-cffi`, `bcrypt`, `radon`, `coverage`.

## ✅ Fase 3 — Normativas nuevas (COMPLETADA — v0.4.0, julio 2026)

**Módulos implementados:**

- **`ai_act/`** — art. 50 aplica el **2 de agosto de 2026**:
  - [x] `ClasificadorRiesgoIA`: cuestionario → prohibido / alto / limitado / mínimo + obligaciones por nivel + fechas de aplicación.
  - [x] `TransparenciaIA`: aviso chatbot (4 idiomas), marcado de contenido generado (Art. 50.2), declaración de asistencia IA.
  - [x] `RegistroDecisionesIA`: logging estructurado Art. 12 (alto riesgo) con timestamp, hash de input, confianza, supervisión humana.
  - [x] `DocumentacionTecnicaAnexoIV`: plantilla Markdown de las 10 secciones requeridas.
  - [x] `RegistroModelosIA` (ISO 42001): inventario con filtros por riesgo y producción.
  - [x] `RegistroRiesgosIA` (ISO 23894): puntuación probabilidad×impacto, clasificación por fase del ciclo de vida.

- **`cra/`** — reporte de vulnerabilidades obligatorio desde el **11 de septiembre de 2026**:
  - [x] `GeneradorSBOM`: CycloneDX 1.5 JSON desde requirements.txt o lista de dicts.
  - [x] `GeneradorPoliticaVulnerabilidades`: security.txt (RFC 9116) + SECURITY.md con plazos ISO 30111 y CRA.
  - [x] `ChecklistSecureByDesign`: 10 controles CRA Art. 13 con puntuación.
  - [x] `PlantillaReporteVulnerabilidad`: 3 documentos — aviso 24 h, notificación 72 h, informe final 14 días.

- **`privacidad/`** (ISO 27701 + ISO 27017/27018):
  - [x] `DetectorPII`: 7 patrones (email, teléfono ES, tarjeta, DNI, NIE, IBAN, IP privada, password en logs) + patrones adicionales configurables.
  - [x] `EnmascaradorLogs`: reemplaza PII por etiquetas + filtro `logging.Filter` listo para añadir al logger.
  - [x] `ChecklistCloudPrivacidad`: 6 controles ISO 27017 + 6 controles ISO 27018 (GDPR Art. 17/20).

- **`iso_5055/`** (ISO/IEC 5055):
  - [x] `AnalizadorISO5055`: ejecuta bandit y mapea 50+ test_id a CWE-IDs con resumen por categoría ISO 5055.

- **`iso_25012/`** (ISO/IEC 25012):
  - [x] `ValidadorCalidadDatos`: `validar_completitud`, `validar_exactitud` (tipos/rangos/patrones), `validar_consistencia` (lambdas de negocio) con porcentajes y detalle por registro.

- [x] Tests: 68 → 156 tests (88 nuevos). Módulo `ia/__init__.py` actualizado para re-exportar `ai_act`.

Criterio de admisión aplicado: **cada norma entra solo si aporta al menos un control automatizable**.

## Fase 4 — Producto redondo (→ 100) ✅ COMPLETADA v1.0.0 (2026-07-15)

- [x] CLI unificada `kit-iso auditar <dir>` con informe Markdown/JSON y mapeo *norma → control → evidencia → veredicto*.
- [x] Flags: `--formato json|markdown`, `--salida ARCHIVO`, `--umbral-complejidad N`.
- [x] Exit code 1 cuando hay fallos (integración CI/CD directa).
- [x] Módulo `_auditoria.py` separado de la CLI para testabilidad.
- [x] 6 controles: ISO 27001 A.8.12, ISO 5055 (bandit→CWE), ISO 25010 (complejidad), ISO 27701 (PII), CRA Art.14 (artefactos), WCAG 2.1.
- [x] `CHANGELOG.md` con historial completo v0.1.0→v1.0.0.
- [x] `SECURITY.md` y `.well-known/security.txt` (el kit cumple sus propias normas CRA).
- [x] `ejemplos/auditoria_completa.py` end-to-end.
- [x] Tests: 156 → 181 tests (25 nuevos en test_cli.py). Todos los tests del código nuevo pasan.
- [x] **Prueba final**: `kit-iso auditar src/kit_iso` → 3/6 controles OK. Hallazgos restantes son falsos positivos reconocidos (emails en docstrings, patrones regex detectados como PII). El kit informa honestamente sobre sí mismo.

## Fuentes (investigación jul. 2026)

- AI Act art. 50: [artificialintelligenceact.eu/article/50](https://artificialintelligenceact.eu/article/50/) · [Guía práctica](https://artificialintelligenceact.eu/transparency-rules-article-50/)
- CRA: [Comisión Europea — Cyber Resilience Act](https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act) · [Hitos 2026](https://www.hlc.com/en/publications/eu-cyber-resilience-act-getting-ready-for-cra-compliance-in-2026) · [cyberresilienceact.eu](https://www.cyberresilienceact.eu/explained.html)
- ISO 29147/30111: [Secuvi](https://www1.secuvi.com/blog/compliance/managing-vulnerabilities-effectively-iso-iec-29147-and-30111-explained/) · [ISO 29147](https://www.iso.org/standard/72311.html)
- ISO 5055: [Perforce](https://www.perforce.com/blog/sca/what-is-iso-5055) · [CISQ](https://www.it-cisq.org/standards/code-quality-standards/)
- ISO 25012: [iso25000.com](https://iso25000.com/index.php/normas-iso-25000/iso-25012)
- ISO 27017/27018: [Thoropass](https://www.thoropass.com/blog/what-is-iso-27017-iso-27018) · [Microsoft Learn 27018](https://learn.microsoft.com/es-es/compliance/regulatory/offering-iso-27018)
- ISO 23894: [Gobernaria](https://gobernaria.com/marcos/iso-23894) · [isotools](https://isotools.org/2025/01/14/normas-iso-para-implementar-ia-a-considerar-en-el-desarrollo-de-sistemas-de-inteligencia-artificial/)
