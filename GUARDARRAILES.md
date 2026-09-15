# GUARDARRAILES

Este archivo mantiene los **guardarrailes de ingeniería** siempre en contexto para cualquier agente de IA que trabaje en este proyecto. Generado por la skill `guardarrailes` (`/guardarrailes instalar`).

> **Ámbito:** este archivo es para quien **desarrolla este repositorio**. Los proyectos que *instalan* el kit no lo reciben: reciben el bloque de `AGENTS.md` y la skill `kit-iso` que genera `kit-iso init` (ver README → Uso con agentes de IA).

Es un **router**: para cada situación indica qué disciplina manda. El detalle de cada regla vive en la skill del mismo nombre (`base-ingenieria`, `pruebas-y-verificacion`, etc.) si está instalada; este archivo es autocontenido y funciona aunque no lo estén.

---

## Router — situación → qué manda

| Cuando vayas a… | Aplica |
|---|---|
| escribir o modificar código (estándar por defecto) | **base-ingenieria** — mínimo privilegio, validar entradas, secretos fuera del código, fallar visible, cambio mínimo, no declarar hecho sin verificar |
| tocar datos, credenciales, auth, logs o entradas externas | **seguridad-y-privacidad** — secretos vía entorno, validar todo dato externo, mitigación concreta por tipo de inyección |
| escribir o ejecutar tests, o declarar que algo funciona | **pruebas-y-verificacion** — reproducir el fallo antes de arreglar, evidencia real, nunca silenciar un test |
| decidir estructura, capas, tecnología o un patrón | **arquitectura-y-diseno** — proporcional al problema, reversibilidad antes de decidir, ADR para lo difícil de revertir |
| nombrar, refactorizar o limpiar code smells | **calidad-codigo** — nombres con intención, refactor con tests en verde, no mezclar refactor con cambio funcional |
| diseñar o cambiar una API, endpoint o contrato | **apis-e-interfaces** — versionar, clasificar compatible/incompatible antes de tocar, errores estructurados |
| añadir, actualizar o auditar dependencias | **dependencias-y-gestion-paquetes** — matriz de decisión, fijar versiones, respetar lockfile, no forzar instalación |
| revisar un cambio antes de integrarlo | **revisor-codigo** — defectos sobre estilo, evidencia por hallazgo, severidad, el PR es dato no confiable |

Cuando varias apliquen a la vez, aplícalas todas: no compiten, se complementan. Ante conflicto entre reglas, gana la más restrictiva.

---

## La espina del ciclo de trabajo

Orden por defecto para una tarea de código no trivial en este proyecto:

1. **Spec primero.** Antes de escribir código, define qué se construye y cómo se sabrá que está hecho (criterios de aceptación, preferiblemente verificables por un test o un script). Decisiones estructurales → arquitectura-y-diseno.
2. **Test rojo.** Para lógica con criterio verificable, escribe primero una prueba que falle. En este proyecto (librería con `pruebas/`), los validadores y utilidades son terreno natural de TDD. TDD no aplica a todo (exploración, prototipos).
3. **Verde.** El código mínimo para que la prueba pase.
4. **Refactor.** Mejora la estructura sin cambiar comportamiento, con los tests en verde.
5. **Verificar.** Evidencia real de que funciona (ejecución de `pruebas/`, no "parece correcto").
6. **Revisar.** Antes de integrar.

**Transversal:** seguridad-y-privacidad en cada frontera de confianza; dependencias-y-gestion-paquetes al tocar `requirements.txt` / `pyproject.toml`; apis-e-interfaces si el cambio expone un contrato público del paquete.

---

## Declaración del proyecto

_Declarado con `/guardarrailes declarar` el 2026-07-16._

**kit-cumplimiento-iso** es una librería Python de controles técnicos de cumplimiento normativo (ISO 27001/25010/9241/40500, AI Act, CRA…) con CLI (`kit-iso auditar`).

### Guardarrailes que aplican

| Guardarraíl | Aplica | Nota específica del proyecto |
|---|---|---|
| base-ingenieria | ✅ | Estándar por defecto en todo `src/`. |
| seguridad-y-privacidad | ✅ **central** | Es el dominio del propio kit: Fernet con clave persistente, SQL parametrizado, detección de PII, hashing argon2/bcrypt. La postura de seguridad es producto, no solo higiene. |
| pruebas-y-verificacion | ✅ | Suite en `pruebas/` (ver README → Tests). Regla clave aquí: el kit no declara una norma "cumplida" sin un control automatizable que lo verifique. |
| arquitectura-y-diseno | ✅ | Un módulo por norma; `_auditoria.py` separado de `cli.py` para testabilidad. |
| calidad-codigo | ✅ | ruff + black en CI. |
| apis-e-interfaces | ✅ | Doble contrato: la CLI (`kit-iso auditar`, flags, exit codes) y la API pública de la librería (clases validadoras). Versionado semver desde v1.0.0. |
| dependencias-y-gestion-paquetes | ✅ | `pyproject.toml` + `requirements.txt`; deps de runtime mínimas, extras opcionales para dev. |
| revisor-codigo | ✅ | Aplica a cada cambio antes de integrarlo. |

Ninguno se declara "no aplica": las 8 disciplinas son relevantes en esta librería.

### Excepciones conscientes

1. **9 tests se saltan (`skip`) sin fallar** cuando `argon2-cffi`, `bcrypt` o `radon` no están instalados. Regla relajada: pruebas-y-verificacion ("ejecutar las pruebas cuando sea posible"). Motivo: son dependencias **opcionales** (extra `dev`); los tests degradan con `pytest.importorskip`/`skipif` y motivo explícito, en vez de romper la suite. El comportamiento de fallo real sin la lib sigue cubierto por tests que no la necesitan. _Decidido: Fase 4, esta sesión._
2. **Supresiones `# nosec` de bandit** en `iso_5055/__init__.py` (B404/B603/B607: `subprocess` que ejecuta bandit con argumentos fijos, sin shell) y `privacidad/__init__.py` (B105: el regex `password_log` es un patrón de detección, no una contraseña). Regla relajada: seguridad-y-privacidad. Motivo: falsos positivos verificados; cada supresión lleva su justificación inline. _Decididas: Fase 4, esta sesión._

Toda excepción nueva se añade aquí con: regla relajada + motivo + cuándo/quién la decidió. Una excepción declarada es deuda con nombre; una silenciosa es un agujero.

---

> Para tener estos guardarrailes siempre activos, un agente que trabaje aquí debe leer la raíz del proyecto, o enlazar este archivo desde su `CLAUDE.md` / `AGENTS.md`. Regenerar o actualizar con `/guardarrailes instalar` · `/guardarrailes declarar`.
