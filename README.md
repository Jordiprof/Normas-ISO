# Kit Cumplimiento ISO

Toolkit modular en Python con **controles técnicos automatizables** alineados con normas ISO para aplicaciones full-stack: seguridad (ISO 27001), calidad (ISO 25010), usabilidad (ISO 9241) y accesibilidad (ISO 40500 / WCAG 2.1). Soporta PostgreSQL y MySQL.

> **Qué es y qué no es.** Este kit ayuda a *implementar controles técnicos* alineados con normas ISO. **No certifica** el cumplimiento de ninguna norma: ISO 27001 y similares certifican sistemas de gestión (procesos, políticas, auditorías), no código. Úsalo como una capa de buenas prácticas verificables, no como un sello.

---

## Índice

- [Características](#características)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [CLI: `kit-iso auditar`](#cli-kit-iso-auditar)
- [Módulos y uso](#módulos-y-uso)
- [API de demostración](#api-de-demostración)
- [Tests](#tests)
- [Dependencias](#dependencias)
- [Hoja de ruta](#hoja-de-ruta)

---

## Características

| Norma | Módulo | Clase principal |
|-------|--------|----------------|
| ISO 27001 — Seguridad | `kit_iso.seguridad` | `ToolkitSeguridad` (Fernet), `ValidadorSeguridad` (8 patrones + entropía), `ValidadorContrasenasSeguras` (argon2/bcrypt), `ValidadorSecurityHeaders`, `ValidadorTLS` |
| ISO 9241 — Usabilidad | `kit_iso.usabilidad` | `HerramientasUsabilidad` |
| ISO 27001 + BD | `kit_iso.base_datos` | `BaseDatosSegura` |
| ISO 40500 / WCAG 2.1 — Accesibilidad | `kit_iso.accesibilidad` | `HerramientasAccesibilidad` (6 criterios: 1.1.1, 1.3.1, 1.4.3, 2.4.4, 3.1.1, 3.3.2) |
| ISO 25010 — Calidad | `kit_iso.calidad` | `HerramientasCalidad` (rendimiento + complejidad McCabe con radon + cobertura con coverage) |
| AI Act + ISO 42001/23894 — IA | `kit_iso.ai_act` | `ClasificadorRiesgoIA`, `TransparenciaIA` (art. 50), `RegistroDecisionesIA` (art. 12), `DocumentacionTecnicaAnexoIV`, `RegistroModelosIA`, `RegistroRiesgosIA` |
| CRA + ISO 29147/30111 — Ciberresiliencia | `kit_iso.cra` | `GeneradorSBOM` (CycloneDX), `GeneradorPoliticaVulnerabilidades` (security.txt/SECURITY.md), `ChecklistSecureByDesign`, `PlantillaReporteVulnerabilidad` (24h/72h/14d) |
| ISO 27701 + 27017/27018 — Privacidad | `kit_iso.privacidad` | `DetectorPII` (7 tipos), `EnmascaradorLogs`, `ChecklistCloudPrivacidad` |
| ISO/IEC 5055 — Calidad de código | `kit_iso.iso_5055` | `AnalizadorISO5055` (bandit → CWE) |
| ISO/IEC 25012 — Calidad de datos | `kit_iso.iso_25012` | `ValidadorCalidadDatos` (completitud, exactitud, consistencia) |
| **CLI unificada** | `kit_iso.cli` | `kit-iso auditar <dir>` — 6 controles, informe Markdown/JSON |

---

## Estructura del proyecto

```
kit-cumplimiento-iso/
├── src/
│   └── kit_iso/
│       ├── __init__.py              # Punto de entrada del paquete (v1.0.0)
│       ├── cli.py                   # CLI: kit-iso auditar <dir>
│       ├── _auditoria.py            # Lógica de auditoría consolidada (6 controles)
│       ├── seguridad/
│       │   ├── __init__.py          # ToolkitSeguridad — Fernet con clave persistente (env)
│       │   └── validador.py         # ValidadorSeguridad — detección de secretos expuestos
│       ├── usabilidad/
│       │   └── __init__.py          # HerramientasUsabilidad — validación de inputs + métricas
│       ├── base_datos/
│       │   └── __init__.py          # BaseDatosSegura — PostgreSQL/MySQL, commit/rollback, whitelist
│       ├── accesibilidad/
│       │   └── __init__.py          # HerramientasAccesibilidad — validación WCAG 2.1
│       ├── calidad/
│       │   └── __init__.py          # HerramientasCalidad — performance + complejidad + cobertura
│       ├── ai_act/
│       │   └── __init__.py          # AI Act + ISO 42001/23894 — transparencia y gobernanza IA
│       ├── cra/
│       │   └── __init__.py          # CRA + ISO 29147/30111 — SBOM y divulgación de vulnerabilidades
│       ├── privacidad/
│       │   └── __init__.py          # ISO 27701 + 27017/27018 — PII, enmascarado, cloud
│       ├── iso_5055/
│       │   └── __init__.py          # ISO/IEC 5055 — bandit → CWE
│       ├── iso_25012/
│       │   └── __init__.py          # ISO/IEC 25012 — calidad de datos
│       ├── ia/
│       │   └── __init__.py          # Re-exporta ai_act (compatibilidad)
│       └── nucleo/
│           └── __init__.py          # Logger + config desde variables de entorno
├── ejemplos/
│   └── ejemplos_codigo.py           # API FastAPI de demostración
├── pruebas/
│   ├── test_seguridad.py            # Clave persistente, ciclo encriptar/desencriptar, detector
│   ├── test_base_datos.py           # Commit/rollback, whitelist, context manager (BD mockeada)
│   └── test_usabilidad.py           # Validación de inputs y feedback
├── requirements.txt
├── pyproject.toml
├── PLAN-MEJORA.md                   # Plan por fases hacia v1.0 (AI Act, CRA, más ISOs)
└── README.md
```

---

## Instalación

**Requisitos:** Python 3.10+

```bash
git clone <url-del-repo>
cd kit-cumplimiento-iso

python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

---

## Configuración

Toda la configuración sensible va por variables de entorno (archivo `.env`, nunca commiteado). Copia `.env.example` a `.env`:

```env
# Clave de encriptación Fernet — OBLIGATORIA para usar seguridad/base_datos
KIT_ISO_CLAVE=<clave generada>

DB_TIPO=postgres        # "postgres" o "mysql"
DB_HOST=localhost
DB_USUARIO=tu_usuario
DB_PASSWORD=tu_password
DB_NOMBRE=nombre_bd
```

Genera la clave una sola vez:

```bash
python -c "from kit_iso.seguridad import ToolkitSeguridad; print(ToolkitSeguridad.generar_clave().decode())"
```

> **Gestión de claves (ISO 27001):** la clave es persistente y vive fuera del código. Si la pierdes, los datos encriptados con ella son **irrecuperables**. Si se expone (commit, log, chat), considérala comprometida: rótala y re-encripta.

---

## CLI: `kit-iso auditar`

Tras `pip install -e .`, el comando `kit-iso` queda disponible. Ejecuta **6 controles automatizados** sobre un directorio y emite un informe consolidado que mapea *norma → control → evidencia → veredicto*.

```bash
# Auditar el código fuente y mostrar el informe Markdown por pantalla
kit-iso auditar src/

# Auditar el directorio actual
kit-iso auditar .

# Guardar el informe en un archivo
kit-iso auditar src/ --salida informe-auditoria.md

# Salida JSON (para integrar en pipelines o dashboards)
kit-iso auditar src/ --formato json --salida auditoria.json

# Ajustar el umbral de complejidad ciclomática (default: 10)
kit-iso auditar src/ --umbral-complejidad 8

# Excluir rutas del escaneo (glob relativo, repetible)
kit-iso auditar . --excluir "ejemplos/*" --excluir "*_demo.py"
```

Equivalente sin el entry point instalado: `python -m kit_iso.cli auditar src/`.

### Controles que ejecuta

| Norma | Control | Detecta |
|-------|---------|---------|
| ISO 27001 A.8.12 | Secretos hardcodeados | Contraseñas, API keys, tokens (8 patrones + entropía Shannon) |
| ISO/IEC 5055 | Debilidades CWE | Hallazgos de bandit mapeados a CWE por categoría |
| ISO 25010 | Complejidad ciclomática | Funciones por encima del umbral McCabe |
| ISO 27701 + GDPR | PII en código | Emails, teléfonos, DNI/NIE, IBAN, IPs privadas |
| CRA Art. 14 + ISO 29147 | Artefactos de divulgación | Presencia de `SECURITY.md` y `.well-known/security.txt` |
| WCAG 2.1 / ISO 40500 | Accesibilidad HTML | Fallos de accesibilidad en archivos `.html` (si los hay) |

### Ejemplo de salida (Markdown)

```markdown
# Informe de Auditoría — kit-iso v1.0.0

## Resumen ejecutivo

| Norma | Control | Estado |
|-------|---------|--------|
| ISO 27001 A.8.12 | Secretos hardcodeados en código fuente | ✅ ok |
| ISO/IEC 5055 | Calidad de código — debilidades CWE (bandit) | ❌ fallo |
| ISO 25010 — Mantenibilidad | Complejidad ciclomática (umbral McCabe: 10) | ✅ ok |
| ...

> **5/6 controles pasados** — Fallidos: 1 · Advertencias: 0
```

### Códigos de salida (integración CI/CD)

- `0` — todos los controles pasan.
- `1` — hay al menos un control fallido (falla el paso del pipeline).
- `2` — error de uso (p. ej. directorio inexistente).

```yaml
# Ejemplo en GitHub Actions: bloquea el merge si la auditoría falla
- run: kit-iso auditar src/
```

También es invocable como librería:

```python
from kit_iso._auditoria import ejecutar_auditoria, generar_markdown

resultados = ejecutar_auditoria("src/", umbral_complejidad=10)
print(generar_markdown(resultados))
# resultados["resumen"] → {"total_controles": 6, "pasados": 5, "fallidos": 1, ...}
```

Ejemplo completo end-to-end en [`ejemplos/auditoria_completa.py`](ejemplos/auditoria_completa.py).

---

## Módulos y uso

### Seguridad — ISO 27001

```python
from kit_iso.seguridad import ToolkitSeguridad
from kit_iso.seguridad.validador import ValidadorSeguridad

# Encriptación simétrica Fernet — la clave sale de KIT_ISO_CLAVE (o del argumento clave=)
seg = ToolkitSeguridad()
encriptado = seg.encriptar_datos("dato sensible")
original   = seg.desencriptar_datos(encriptado)

# Detección de secretos expuestos en código fuente
val = ValidadorSeguridad()
hallazgos = val.analizar_codigo("api_key = '12345'")
# → ["RIESGO ISO 27001: Se detectó un secreto expuesto (patrón: api_key...)"]
```

Sin `KIT_ISO_CLAVE` configurada, `ToolkitSeguridad()` **falla de forma explícita** con instrucciones — nunca genera una clave implícita que haría los datos irrecuperables.

---

### Base de Datos Segura — ISO 27001 A.10.1

```python
from kit_iso.base_datos import BaseDatosSegura

with BaseDatosSegura(
    tipo_bd="postgres", host="localhost",
    usuario="user", password="pass", nombre_bd="mi_bd",
) as db:
    # Lecturas: consulta parametrizada (previene SQL Injection)
    filas = db.consulta_segura("SELECT * FROM usuarios WHERE id = %s", (1,))

    # Escrituras: parametrizadas y con commit automático (rollback si falla)
    db.ejecutar_segura("UPDATE registros SET contenido = %s WHERE id = %s", ("x", 1))

    # Almacenar encriptado con whitelist de tablas/columnas
    db.almacenar_encriptado("registros", "contenido", "dato sensible")
```

Whitelist por defecto — tablas: `usuarios`, `registros`, `auditorias`, `documentos`; columnas: `datos`, `contenido`, `valor`, `texto`. Configurable: `BaseDatosSegura(..., tablas_permitidas={"eventos"}, columnas_permitidas={"payload"})`.

---

### Usabilidad — ISO 9241

```python
from kit_iso.usabilidad import HerramientasUsabilidad

hu = HerramientasUsabilidad()
input_ok = hu.validar_input_usuario("Hola mundo")   # longitud + patrón + escaneo de secretos
resultado, duracion = hu.medir_eficiencia_interaccion(mi_funcion, arg1)
mensaje = hu.generar_feedback(exito=True)
```

---

### Accesibilidad — ISO 40500 / WCAG 2.1

```python
from kit_iso.accesibilidad import HerramientasAccesibilidad

ha = HerramientasAccesibilidad()
informe = ha.validar_html_accesible('<img src="foto.jpg">')
# → {"estado": "fallo", "criterio": "1.1.1", "hallazgos": ["Img sin atributo alt: 'foto.jpg'"]}
```

---

### Calidad — ISO 25010

```python
from kit_iso.calidad import HerramientasCalidad

hc = HerramientasCalidad()
resultado, duracion = hc.medir_performance(mi_funcion, arg1)
hc.run_tests()
```

---

## API de demostración

```bash
uvicorn ejemplos.ejemplos_codigo:app --reload
```

Endpoints en `http://127.0.0.1:8000/docs`: `/demo/almacenar`, `/demo/accesibilidad`, `/demo/encriptar`. Requiere `.env` con `KIT_ISO_CLAVE` y credenciales de BD.

---

## Tests

```bash
pytest pruebas/ -v
```

La suite (181 tests) incluye **tests de regresión de los bugs corregidos en v0.2.0**, los controles de las Fases 2–3 y la CLI de la Fase 4. Los tests que dependen de `argon2-cffi`, `bcrypt` o `radon` (dependencias opcionales) se saltan automáticamente si no están instaladas:

- `test_seguridad.py` — falla explícita sin clave, ciclo encriptar/desencriptar, **clave persistente entre instancias** (bug original: cada instancia generaba la suya → datos irrecuperables), detector de secretos sin falsos positivos.
- `test_base_datos.py` — **commit en escrituras** (bug original), rollback, whitelist, context manager. BD mockeada.
- `test_usabilidad.py` — validación de inputs y feedback.
- `test_accesibilidad.py` — 18 tests, uno por criterio WCAG (detección y ausencia de falsos positivos). Test de integración con HTML completamente accesible.
- `test_calidad.py` — 12 tests: rendimiento, complejidad simple vs compleja, umbrales configurables, medir_cobertura mockeado.
- `test_seguridad.py` — ampliado a 30 tests: 7 patrones nuevos (Bearer, PEM, AWS, GitHub, Slack), entropía Shannon, argon2/bcrypt, security headers, TLS mockeado.

CI en GitHub Actions: `ruff` + `black` + `bandit` + `pytest` en cada push/PR.

---

## Dependencias

| Paquete | Versión mínima | Uso |
|---------|---------------|-----|
| `cryptography` | 41.0.0 | Encriptación Fernet (ISO 27001) |
| `psycopg2-binary` | 2.9.0 | Conector PostgreSQL |
| `mysql-connector-python` | 8.0.0 | Conector MySQL |
| `beautifulsoup4` | 4.12.0 | Parsing HTML (ISO 40500) |
| `python-dotenv` | 1.0.0 | Variables de entorno (demo) |
| `fastapi` / `uvicorn` | 0.109 / 0.27 | API de demostración |
| `pytest` / `bandit` / `ruff` / `black` | — | Calidad y seguridad (dev) |
| `radon` | 6.0.0 | Complejidad ciclomática McCabe (ISO 25010) |
| `coverage` | 7.0.0 | Cobertura de tests (ISO 25010) |
| `argon2-cffi` | 23.0.0 | Hashing de contraseñas argon2 (ISO 27001 A.9.4) |
| `bcrypt` | 4.0.0 | Hashing de contraseñas bcrypt (ISO 27001 A.9.4) |

> `torch`, `langchain` y `langgraph` se retiraron en v0.2.0: ningún módulo los usaba. Volverán solo si la implementación real de IA (Fase 3) los necesita.

---

## Hoja de ruta

Ver [PLAN-MEJORA.md](PLAN-MEJORA.md) y [CHANGELOG.md](CHANGELOG.md). Las cuatro fases están **completadas**:

- ✅ **Fase 1** (v0.2.0): corrección de 3 bugs críticos (clave Fernet persistente, commit/rollback en BD, módulo IA a stub explícito).
- ✅ **Fase 2** (v0.3.0): profundización de normas existentes (8 patrones de secretos + entropía, argon2/bcrypt, security headers, TLS, WCAG de 1 a 6 criterios, complejidad y cobertura reales).
- ✅ **Fase 3** (v0.4.0): módulos **AI Act** (art. 50, aplica desde el 2 de agosto de 2026), **CRA** (SBOM, divulgación de vulnerabilidades), ISO 42001/23894, 29147/30111, 27701 + 27017/27018, 25012 y 5055.
- ✅ **Fase 4** (v1.0.0): CLI `kit-iso auditar` con informe consolidado, `CHANGELOG.md`, versionado semver y prueba final (el kit se audita a sí mismo).

---

## Versión

`1.0.0` — Julio 2026. Fase 4: **CLI `kit-iso auditar`** con 6 controles e informe Markdown/JSON (mapeo norma → control → evidencia → veredicto), exit codes para CI/CD, `CHANGELOG.md`, versionado semver y prueba final (el kit se audita a sí mismo). Historial completo en [CHANGELOG.md](CHANGELOG.md).

`0.4.0` — Julio 2026. Fase 3: módulos `ai_act` (AI Act + ISO 42001/23894), `cra` (CRA + ISO 29147/30111), `privacidad` (ISO 27701 + 27017/27018), `iso_5055` (bandit → CWE) e `iso_25012` (calidad de datos); 68 → 156 tests.

`0.3.0` — Julio 2026. Fase 2: `ValidadorSeguridad` con 8 patrones + entropía Shannon; `ValidadorContrasenasSeguras` (argon2/bcrypt); `ValidadorSecurityHeaders` (5 headers, valores validados); `ValidadorTLS`; WCAG ampliado de 1 a 6 criterios (1.1.1, 1.3.1, 1.4.3, 2.4.4, 3.1.1, 3.3.2); `HerramientasCalidad` con complejidad ciclomática (radon) y cobertura (coverage); 20 → 68 tests.

`0.2.0` — Julio 2026. Fase 1: clave Fernet persistente, commit/rollback en BD, módulo IA a stub explícito, dependencias reducidas (~2 GB menos), 2 → 20 tests, CI con bandit.
