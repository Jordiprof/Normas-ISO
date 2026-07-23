"""Cyber Resilience Act (CRA, Reg. EU 2024/2847) + ISO 29147/30111 — SBOM, divulgación de vulnerabilidades, secure-by-design."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── SBOM (CRA Art. 13.5) ──────────────────────────────────────────────────────


class GeneradorSBOM:
    """Genera un SBOM (Software Bill of Materials) en formato CycloneDX JSON.

    El CRA exige SBOM legible por máquina para productos con elementos digitales
    (Art. 13.5, aplicación plena diciembre 2027).

    Ejemplo::

        gen = GeneradorSBOM()
        sbom = gen.desde_requirements("requirements.txt", "mi-aplicacion")
        print(gen.a_json(sbom))
    """

    def desde_requirements(self, ruta: str, nombre_componente: str = "aplicacion") -> dict:
        """Parsea requirements.txt o pyproject.toml y genera SBOM CycloneDX 1.5."""
        componentes = []
        path = Path(ruta)
        if path.exists():
            for linea in path.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                nombre, version = self._parsear_linea(linea)
                componentes.append(
                    {
                        "type": "library",
                        "name": nombre,
                        "version": version,
                        "purl": f"pkg:pypi/{nombre.lower()}@{version}",
                    }
                )

        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": {"type": "application", "name": nombre_componente},
                "norma": "CRA Art. 13.5 + ISO/IEC 29147",
            },
            "components": componentes,
        }

    def desde_lista(self, dependencias: list[dict], nombre_componente: str = "aplicacion") -> dict:
        """Genera SBOM desde lista de dicts ``[{"name": ..., "version": ...}]``."""
        componentes = [
            {
                "type": "library",
                "name": d["name"],
                "version": d.get("version", "desconocida"),
                "purl": f"pkg:pypi/{d['name'].lower()}@{d.get('version', 'desconocida')}",
            }
            for d in dependencias
        ]
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": {"type": "application", "name": nombre_componente},
                "norma": "CRA Art. 13.5 + ISO/IEC 29147",
            },
            "components": componentes,
        }

    def a_json(self, sbom: dict, sangria: int = 2) -> str:
        return json.dumps(sbom, ensure_ascii=False, indent=sangria)

    @staticmethod
    def _parsear_linea(linea: str) -> tuple[str, str]:
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if sep in linea:
                partes = linea.split(sep, 1)
                return partes[0].strip(), f"{sep}{partes[1].strip()}"
        return linea, "desconocida"


# ── Política de divulgación (CRA Art. 14 + ISO 29147) ───────────────────────


class GeneradorPoliticaVulnerabilidades:
    """Genera SECURITY.md y security.txt para cumplir CRA Art. 14 + ISO 29147.

    Ejemplo::

        gen = GeneradorPoliticaVulnerabilidades()
        txt = gen.security_txt("seguridad@empresa.com", "https://empresa.com/security")
        md  = gen.security_md("Mi Proyecto", "seguridad@empresa.com")
    """

    def security_txt(
        self,
        contacto_email: str,
        url_politica: str,
        idioma: str = "es",
        expires_dias: int = 365,
    ) -> str:
        """Genera /.well-known/security.txt según RFC 9116 (CRA Art. 14 + ISO 29147)."""
        expira = (datetime.now(timezone.utc) + timedelta(days=expires_dias)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return (
            f"Contact: mailto:{contacto_email}\n"
            f"Policy: {url_politica}\n"
            f"Expires: {expira}\n"
            f"Preferred-Languages: {idioma}, en\n"
            f"# Divulgación coordinada — CRA Art. 14 + ISO/IEC 29147\n"
        )

    def security_md(
        self,
        nombre_proyecto: str,
        contacto_email: str,
        url_politica: str | None = None,
    ) -> str:
        """Genera SECURITY.md con proceso de divulgación coordinada."""
        politica_url = url_politica or f"mailto:{contacto_email}"
        return f"""# Política de seguridad — {nombre_proyecto}

## Divulgación responsable (CRA Art. 14 + ISO/IEC 29147)

Si encuentras una vulnerabilidad, **no la hagas pública** hasta coordinar con nosotros.

### Cómo reportar

Envía los detalles a **{contacto_email}** incluyendo:
- Descripción de la vulnerabilidad e impacto potencial
- Pasos detallados para reproducirla
- Versión o commit afectado
- Propuesta de mitigación (opcional)

### Plazos de respuesta (ISO/IEC 30111)

| Evento | Plazo máximo |
|--------|-------------|
| Acuse de recibo | 24 horas |
| Confirmación o descarte | 7 días |
| Plan de mitigación | 30 días |
| Resolución y publicación coordinada | 90 días |

### Notificación a ENISA (CRA Art. 14 — productos UE)

| Fase | Plazo desde detección |
|------|-----------------------|
| Aviso inicial | 24 horas |
| Notificación completa | 72 horas |
| Informe final | 14 días |

### Política completa

{politica_url}
"""


# ── Secure-by-design checklist (CRA Art. 13) ─────────────────────────────────


class ChecklistSecureByDesign:
    """Evaluación de controles de diseño seguro por defecto (CRA Art. 13 + ENISA).

    Ejemplo::

        cl = ChecklistSecureByDesign()
        resultado = cl.evaluar({
            "autenticacion_fuerte": True,
            "cifrado_datos_transito": True,
            "sbom_disponible": False,
        })
        # → {"estado": "fallo", "puntuacion": 60.0, "pendientes": [...]}
    """

    CONTROLES = [
        ("autenticacion_fuerte", "Autenticación fuerte por defecto (MFA, sin contraseñas débiles)"),
        ("cifrado_datos_reposo", "Datos sensibles cifrados en reposo"),
        ("cifrado_datos_transito", "Comunicaciones cifradas en tránsito (TLS 1.2+)"),
        (
            "superficie_ataque_minima",
            "Superficie de ataque mínima (puertos cerrados, features off por defecto)",
        ),
        ("actualizaciones_seguridad", "Mecanismo de actualización de seguridad disponible"),
        (
            "sin_credenciales_defecto",
            "Sin credenciales por defecto (se exige cambio en primer uso)",
        ),
        ("logs_seguridad", "Logs de seguridad habilitados (sin PII en logs)"),
        ("sbom_disponible", "SBOM disponible y actualizado (CRA Art. 13.5)"),
        ("politica_vulnerabilidades", "Política de divulgación publicada (CRA Art. 14)"),
        ("tests_seguridad_ci", "Tests de seguridad automatizados en el pipeline CI/CD"),
    ]

    def evaluar(self, controles_implementados: dict[str, bool]) -> dict:
        """Evalúa el cumplimiento secure-by-design.

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "CRA Art. 13",
                "puntuacion": 80.0,
                "cumplidos": [...],
                "pendientes": [...]
            }
        """
        cumplidos = []
        pendientes = []
        for nombre, descripcion in self.CONTROLES:
            if controles_implementados.get(nombre, False):
                cumplidos.append({"control": nombre, "descripcion": descripcion})
            else:
                pendientes.append({"control": nombre, "descripcion": descripcion})

        total = len(self.CONTROLES)
        return {
            "estado": "ok" if not pendientes else "fallo",
            "norma": "CRA Art. 13 — Secure-by-Design",
            "puntuacion": round(len(cumplidos) / total * 100, 1),
            "cumplidos": cumplidos,
            "pendientes": pendientes,
        }


# ── Plantillas de reporte de vulnerabilidad (CRA Art. 14 + ISO 30111) ─────────


class PlantillaReporteVulnerabilidad:
    """Genera los tres documentos del proceso de notificación CRA Art. 14.

    Flujo obligatorio para productos con elementos digitales en la UE:
        1. Aviso inicial a ENISA — 24 h desde detección
        2. Notificación completa — 72 h desde detección
        3. Informe final — 14 días desde detección

    Ejemplo::

        p = PlantillaReporteVulnerabilidad()
        aviso = p.aviso_inicial_24h("RCE en parser", "mi-app", "2.1.0", "crítica")
        notif = p.notificacion_72h(aviso, "Desbordamiento de buffer en...", "Deshabilitar endpoint /parse")
        informe = p.informe_final_14dias(notif, "Publicado parche v2.1.1", "CVE-2026-XXXX")
    """

    @staticmethod
    def _ts() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def aviso_inicial_24h(
        self,
        descripcion_breve: str,
        producto: str,
        version: str,
        severidad: str,
    ) -> str:
        """Aviso inicial a ENISA (plazo: 24 h desde detección — CRA Art. 14.2(a))."""
        return (
            f"# Aviso Inicial — CRA Art. 14.2(a)\n"
            f"Fecha: {self._ts()}\n"
            f"Estado: AVISO INICIAL (≤ 24 h)\n\n"
            f"Producto: {producto} v{version}\n"
            f"Descripción breve: {descripcion_breve}\n"
            f"Severidad estimada: {severidad}\n\n"
            f"_[Completar con detalles a medida que avance la investigación]_\n"
        )

    def notificacion_72h(
        self, aviso_inicial: str, analisis: str, mitigacion_provisional: str
    ) -> str:
        """Notificación completa a ENISA (plazo: 72 h desde detección — CRA Art. 14.2(b))."""
        return (
            f"{aviso_inicial}\n---\n"
            f"# Actualización 72 h — CRA Art. 14.2(b)\n"
            f"Fecha: {self._ts()}\n\n"
            f"Análisis técnico: {analisis}\n"
            f"Mitigación provisional: {mitigacion_provisional}\n"
        )

    def informe_final_14dias(
        self, notificacion: str, resolucion: str, cve: str = "pendiente"
    ) -> str:
        """Informe final a ENISA (plazo: 14 días desde detección — CRA Art. 14.2(c))."""
        return (
            f"{notificacion}\n---\n"
            f"# Informe Final 14 días — CRA Art. 14.2(c)\n"
            f"Fecha: {self._ts()}\n\n"
            f"CVE asignado: {cve}\n"
            f"Resolución: {resolucion}\n"
        )
