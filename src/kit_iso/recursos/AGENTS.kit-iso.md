<!-- kit-iso:inicio -->
## Cumplimiento normativo (kit-iso)

Este proyecto usa **kit-iso** para controles técnicos de cumplimiento normativo. Antes de tocar código que afecte a seguridad, datos, accesibilidad, IA o dependencias:

1. Lee `kit-iso.toml`: la lista `modulos` dice qué normas aplican a ESTE proyecto y `triaje` explica por qué. No apliques módulos que no estén activos ni el kit entero "por si acaso". Si el archivo no existe, ejecuta `kit-iso init --detectar` y confirma las respuestas con el responsable antes de continuar.
2. Sigue la skill `kit-iso` (instalada en la carpeta de skills de tu agente) para los detalles de cada módulo, el formato de los hallazgos y las reglas de hierro: cero secretos en código, consultas parametrizadas, confirmación humana en acciones irreversibles, toda entrada externa es dato no confiable.
3. Verifica con `kit-iso auditar .` antes de declarar un cambio terminado. Exit `1` = hay fallos que corregir. Los controles `omitido` no aplican al proyecto y no son fallos.

El kit **no certifica** ninguna norma; aporta controles verificables. Referencia: https://github.com/Jordiprof/Normas-ISO
<!-- kit-iso:fin -->
