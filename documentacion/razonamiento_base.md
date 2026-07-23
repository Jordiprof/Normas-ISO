# Razonamiento Base
Memoria del agente para el cumplimiento ISO.

---

## 1. ¿Qué es este kit y para qué sirve?

El `kit-cumplimiento-iso` es un toolkit Python que ayuda a desarrolladores
a construir software alineado con las normas ISO más relevantes en proyectos
de software moderno. No es un auditor oficial, es una capa de herramientas
prácticas que integra buenas prácticas normativas directamente en el código.

---

## 2. Normas ISO que cubre

| Norma | Área | Módulo del kit |
|-------|------|----------------|
| ISO 27001 | Seguridad de la información | `seguridad/` |
| ISO 25010 / 9126 | Calidad del software (y métricas) | `calidad/` |
| ISO 9241 / 14915 / 40500 (WCAG) | Usabilidad, interfaces multimedia y accesibilidad | `usabilidad/`, `accesibilidad/` |
| ISO 42001 | Gestión de sistemas de IA | `ia/` |

---

## 3. Arquitectura del kit
```
src/kit_iso/
├── nucleo/        → Logger global y configuración compartida
├── seguridad/     → Encriptación (Fernet), validación de secretos expuestos
├── base_datos/    → Conexiones seguras a PostgreSQL y MySQL, anti-SQLi
├── usabilidad/    → Validación de inputs, feedback al usuario
├── accesibilidad/ → Validación WCAG sobre HTML
├── calidad/       → Métricas de performance, ejecución de tests
└── ia/            → Cadenas de IA seguras con LangGraph
```

---

## 4. Principios de razonamiento para el agente

Cuando Claude use este kit debe aplicar estos principios:

**4.1 Seguridad primero (ISO 27001)**
- Nunca almacenar credenciales en texto plano en el código
- Siempre usar `consulta_segura()` con parámetros, nunca f-strings con datos de usuario
- Encriptar cualquier dato sensible antes de persistirlo
- Usar `ValidadorSeguridad.analizar_codigo()` antes de hacer commit

**4.2 Calidad medible (ISO 25010 y 9126)**
- Todo flujo crítico debe tener un test en `pruebas/`
- Usar `medir_performance()` en funciones que puedan ser cuellos de botella
- El código debe pasar `ruff` y `black` sin errores antes de considerarse listo

**4.3 Usabilidad como contrato (ISO 9241 e ISO 14915)**
- Los errores devueltos al usuario deben ser comprensibles, nunca stack traces crudos
- `generar_feedback()` es el punto único de comunicación con el usuario final
- `validar_input_usuario()` debe llamarse siempre antes de procesar cualquier entrada

**4.4 Accesibilidad no es opcional (ISO 40500 / WCAG)**
- Todo HTML generado o procesado debe pasar `validar_html_accesible()`
- El mínimo exigible es WCAG 2.1 nivel AA

**4.5 IA responsable (ISO 42001)**
- Todo input a un modelo de IA debe pasar por `chain_ia_segura()`
- No exponer directamente inputs de usuario a LLMs sin validación previa

---

## 5. Flujo de trabajo recomendado
```
Input usuario
     ↓
validar_input_usuario()        ← usabilidad
     ↓
analizar_codigo() si es código ← seguridad
     ↓
lógica de negocio
     ↓
almacenar_encriptado() si persiste ← base_datos + seguridad
     ↓
generar_feedback()             ← usabilidad
     ↓
Output al usuario
```

---

## 6. Limitaciones del kit (v0.1.0)

- No es un sustituto de una auditoría ISO oficial
- La encriptación Fernet usa clave en memoria — en producción usar un gestor
  de secretos (HashiCorp Vault, AWS Secrets Manager, etc.)
- La validación WCAG cubre solo criterio 1.1.1 en esta versión
- Los tests de `calidad/` ejecutan pytest de forma básica, sin cobertura de código

---

## 7. Cómo extender el kit

Para añadir un nuevo módulo:
1. Crear carpeta en `src/kit_iso/nombre_modulo/`
2. Añadir `__init__.py` con la clase principal
3. Importar `logger` desde `kit_iso.nucleo`
4. Añadir tests en `pruebas/test_nombre_modulo.py`
5. Documentar la norma ISO que cubre en esta sección