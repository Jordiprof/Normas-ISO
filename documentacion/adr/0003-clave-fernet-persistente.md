# ADR 0003 — Clave Fernet persistente por variable de entorno

**Estado:** Aceptada · **Fecha:** 2026-07 · **Reversibilidad:** Difícil de revertir (afecta a datos ya cifrados).

## Contexto

`ToolkitSeguridad` cifra datos con Fernet (cifrado simétrico). En la versión inicial, cada instancia generaba su propia clave si no se le pasaba una. Bug crítico: lo cifrado en una sesión era **indescifrable** en la siguiente, porque la clave nueva no coincidía → pérdida de datos silenciosa.

## Decisión

La clave **debe** venir de la variable de entorno `KIT_ISO_CLAVE` (o pasarse explícitamente al constructor). Sin clave configurada, `ToolkitSeguridad()` **falla de forma visible** con instrucciones, en vez de generar una implícita.

## Alternativas consideradas

- **Generar y persistir la clave en un fichero** dentro del proyecto: descartado — arriesga commitear la clave; la gestión de secretos es responsabilidad del entorno, no del código (ISO 27001).
- **Clave por defecto embebida**: descartado — una clave conocida no cifra nada de verdad.

## Consecuencias

- ✅ Los datos cifrados sobreviven a reinicios; se acabó la pérdida silenciosa.
- ✅ La clave vive fuera del código (variable de entorno / gestor de secretos).
- ⚠️ Si se pierde la clave, los datos son **irrecuperables** — es el precio correcto de un cifrado real. Si se expone, se rota y se re-cifra.
