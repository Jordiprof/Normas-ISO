# ADR 0001 — Un módulo por norma

**Estado:** Aceptada · **Fecha:** 2026-07 · **Reversibilidad:** Difícil de revertir (es la API pública del paquete).

## Contexto

El kit cubre muchas normas heterogéneas (ISO 27001, 25010, 9241, 40500, AI Act, CRA, ISO 27701, 5055, 25012). Cada una tiene su propio vocabulario, sus controles y su evolución independiente.

## Decisión

Cada norma (o familia de normas afín) vive en su propio subpaquete de `src/kit_iso/` (`seguridad/`, `accesibilidad/`, `ai_act/`, `cra/`, `privacidad/`, `iso_5055/`, `iso_25012/`, …), con su clase o clases validadoras propias.

## Alternativas consideradas

- **Un único módulo monolítico** con todas las validaciones: descartado — acoplaría normas sin relación y crecería sin límite.
- **Un paquete por tipo de control** (todos los "checklist" juntos, todos los "generadores" juntos): descartado — parte el conocimiento de una norma en varios sitios; el usuario piensa por norma, no por tipo de control.

## Consecuencias

- ✅ Cada norma evoluciona sin tocar las demás; el mapeo norma → módulo es directo.
- ✅ La CLI de auditoría puede activar/desactivar controles por módulo.
- ⚠️ Alguna lógica transversal (p. ej. detección de secretos) se referencia entre módulos con imports relativos; hay que vigilar dependencias circulares.
