# ADR 0002 — Separar la lógica de auditoría de la CLI

**Estado:** Aceptada · **Fecha:** 2026-07 · **Reversibilidad:** Reversible.

## Contexto

La Fase 4 añadió `kit-iso auditar`: ejecutar los 6 controles sobre un directorio y emitir un informe. La tentación es meter todo (recorrido de ficheros, ejecución de controles, formato de salida y parseo de argumentos) en el módulo de la CLI.

## Decisión

La lógica de auditoría vive en `kit_iso/_auditoria.py` (recorrido, controles, consolidación, `generar_markdown`). `kit_iso/cli.py` es una capa delgada: solo parsea argumentos, llama a `ejecutar_auditoria` y elige formato/salida. El prefijo `_` marca `_auditoria` como **interno**.

## Alternativas consideradas

- **Todo en `cli.py`**: descartado — obliga a probar la lógica a través de `subprocess`, lento y frágil.

## Consecuencias

- ✅ La lógica de auditoría se prueba **en proceso** (sin `subprocess`), rápido y determinista.
- ✅ `ejecutar_auditoria` es reutilizable como librería, no solo desde la terminal.
- ✅ Cambiar el parser de la CLI no toca la lógica, y viceversa.
