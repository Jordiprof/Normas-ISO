"""AI Act (Reg. EU 2024/1689) + ISO 42001 + ISO 23894 — transparencia, trazabilidad y gobernanza IA."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

# ── Clasificación de riesgo (AI Act art. 6, Anexo III) ────────────────────────


class NivelRiesgoIA(str, Enum):
    """Niveles de riesgo del AI Act."""

    PROHIBIDO = "prohibido"  # Art. 5
    ALTO = "alto"  # Anexo III
    LIMITADO = "limitado"  # Art. 50 — chatbots, deepfakes
    MINIMO = "minimo"  # Sin restricciones específicas


class ClasificadorRiesgoIA:
    """Clasifica el nivel de riesgo de un sistema de IA según el AI Act.

    Ejemplo::

        clf = ClasificadorRiesgoIA()
        resultado = clf.clasificar({
            "interactua_humanos": True,
            "infraestructura_critica": False,
        })
        # → {"nivel": "limitado", "obligaciones": [...], "fecha_aplicacion": "..."}
    """

    _PROHIBIDOS = ("manipulacion_subliminal", "puntuacion_social", "biometria_autoridades")
    _ALTO_RIESGO = (
        "infraestructura_critica",
        "educacion_empleo",
        "servicios_esenciales",
        "seguridad_publica",
    )

    def clasificar(self, respuestas: dict) -> dict:
        """Clasifica el riesgo a partir de un cuestionario de características.

        Claves reconocidas en ``respuestas``:
            - ``manipulacion_subliminal``: técnicas subliminales o deceptivas (Art. 5)
            - ``puntuacion_social``: evaluación o clasificación de personas (Art. 5)
            - ``biometria_autoridades``: biometría en tiempo real por FFSS (Art. 5)
            - ``infraestructura_critica``: IA en infraestructura crítica (Anexo III)
            - ``educacion_empleo``: IA en educación, contratación o empleo (Anexo III)
            - ``servicios_esenciales``: IA en servicios esenciales (Anexo III)
            - ``seguridad_publica``: IA en seguridad pública o migración (Anexo III)
            - ``interactua_humanos``: chatbot o agente que habla con personas (Art. 50.1)
            - ``genera_contenido``: genera texto, imágenes, audio o video (Art. 50.2)
        """
        if any(respuestas.get(k) for k in self._PROHIBIDOS):
            nivel = NivelRiesgoIA.PROHIBIDO
            base_legal = "Art. 5 — Sistema de riesgo inaceptable (prohibido)"
        elif any(respuestas.get(k) for k in self._ALTO_RIESGO):
            nivel = NivelRiesgoIA.ALTO
            base_legal = "Art. 6 + Anexo III — Sistema de alto riesgo"
        elif respuestas.get("interactua_humanos") or respuestas.get("genera_contenido"):
            nivel = NivelRiesgoIA.LIMITADO
            base_legal = "Art. 50 — Obligaciones de transparencia"
        else:
            nivel = NivelRiesgoIA.MINIMO
            base_legal = "Sin obligaciones específicas (riesgo mínimo)"

        return {
            "nivel": nivel,
            "base_legal": base_legal,
            "obligaciones": self._obligaciones(nivel, respuestas),
            "fecha_aplicacion": _FECHAS_APLICACION[nivel],
        }

    @staticmethod
    def _obligaciones(nivel: NivelRiesgoIA, respuestas: dict) -> list[str]:
        if nivel == NivelRiesgoIA.PROHIBIDO:
            return ["Sistema prohibido — no puede ponerse en servicio (Art. 5 AI Act)"]
        if nivel == NivelRiesgoIA.ALTO:
            return [
                "Sistema de gestión de riesgos continuo (Art. 9)",
                "Gobernanza de datos de entrenamiento y prueba (Art. 10)",
                "Documentación técnica Anexo IV (Art. 11)",
                "Registro automático de eventos / logging (Art. 12)",
                "Transparencia e instrucciones al usuario (Art. 13)",
                "Supervisión humana activa (Art. 14)",
                "Exactitud, robustez y ciberseguridad (Art. 15)",
                "Registro en la base de datos de la UE (Art. 71)",
            ]
        if nivel == NivelRiesgoIA.LIMITADO:
            obs = []
            if respuestas.get("interactua_humanos"):
                obs.append("Informar al usuario de que interactúa con una IA (Art. 50.1)")
            if respuestas.get("genera_contenido"):
                obs.append(
                    "Marcar contenido generado por IA de forma legible por máquina (Art. 50.2)"
                )
            return obs
        return []


_FECHAS_APLICACION = {
    NivelRiesgoIA.PROHIBIDO: "2024-08-01 (vigente)",
    NivelRiesgoIA.ALTO: "2026-08-02",
    NivelRiesgoIA.LIMITADO: "2026-08-02 (transición hasta 2026-12-02 para sistemas ya en mercado)",
    NivelRiesgoIA.MINIMO: "N/A",
}


# ── Transparencia art. 50 ─────────────────────────────────────────────────────


class TransparenciaIA:
    """Genera avisos y marcas de transparencia obligatorias (Art. 50).

    Aplica desde el **2 de agosto de 2026** (transición hasta diciembre 2026
    para sistemas ya en mercado el 2 de agosto de 2024).
    """

    _AVISOS = {
        "es": (
            "Este servicio utiliza inteligencia artificial. "
            "Estás interactuando con un sistema automatizado, no con una persona."
        ),
        "en": (
            "This service uses artificial intelligence. "
            "You are interacting with an automated system, not a person."
        ),
        "ca": (
            "Aquest servei utilitza intel·ligència artificial. "
            "Esteu interactuant amb un sistema automatitzat, no amb una persona."
        ),
        "fr": (
            "Ce service utilise l'intelligence artificielle. "
            "Vous interagissez avec un système automatisé, pas avec une personne."
        ),
    }

    def aviso_chatbot(self, idioma: str = "es") -> str:
        """Aviso obligatorio para chatbots (Art. 50.1 AI Act)."""
        return self._AVISOS.get(idioma, self._AVISOS["es"])

    def marcar_contenido_generado(self, contenido: str, metadata: dict | None = None) -> dict:
        """Envuelve contenido generado por IA con metadatos legibles por máquina (Art. 50.2)."""
        return {
            "contenido": contenido,
            "ia_generado": True,
            "norma": "AI Act art. 50.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

    def declaracion_asistencia_ia(
        self,
        descripcion_sistema: str,
        tareas_asistidas: list[str],
        supervision_humana: bool,
    ) -> str:
        """Genera declaración de uso de IA para documentos o decisiones asistidas."""
        supervision = "con supervisión humana" if supervision_humana else "sin supervisión humana ⚠"
        tareas_fmt = "\n".join(f"  - {t}" for t in tareas_asistidas)
        return (
            f"[ASISTIDO POR IA — AI Act art. 50]\n"
            f"Sistema: {descripcion_sistema}\n"
            f"Tareas asistidas:\n{tareas_fmt}\n"
            f"Modalidad: {supervision}\n"
            f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        )


# ── Registro de decisiones art. 12 (alto riesgo) ─────────────────────────────


@dataclass
class EntradaDecision:
    """Entrada del registro de decisiones requerido por Art. 12 (alto riesgo)."""

    input_hash: str  # SHA-256 del input — nunca el dato en claro
    output_resumen: str  # Descripción de la decisión (sin datos personales)
    confianza: float | None  # Score 0-1 si el modelo lo expone
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sistema_id: str = ""
    supervisado_por_humano: bool = False


class RegistroDecisionesIA:
    """Registro estructurado de decisiones de IA requerido por Art. 12 (alto riesgo).

    Ejemplo::

        registro = RegistroDecisionesIA("mi-sistema-v1")
        entrada = registro.nueva_entrada(
            input_hash="sha256:abc123...",
            output_resumen="Solicitud aprobada",
            confianza=0.87,
            supervisado_por_humano=True,
        )
        registro.registrar(entrada)
    """

    def __init__(self, sistema_id: str):
        self.sistema_id = sistema_id
        self._logger = logging.getLogger(f"ai_act.art12.{sistema_id}")

    def nueva_entrada(
        self,
        input_hash: str,
        output_resumen: str,
        confianza: float | None = None,
        supervisado_por_humano: bool = False,
    ) -> EntradaDecision:
        """Crea una EntradaDecision con los campos obligatorios del Art. 12."""
        return EntradaDecision(
            input_hash=input_hash,
            output_resumen=output_resumen,
            confianza=confianza,
            sistema_id=self.sistema_id,
            supervisado_por_humano=supervisado_por_humano,
        )

    def registrar(self, entrada: EntradaDecision) -> None:
        """Persiste la decisión en el log estructurado (Art. 12)."""
        entrada.sistema_id = self.sistema_id
        self._logger.info(
            "ai_act_decision",
            extra={"ai_act_art12": True, "decision": vars(entrada)},
        )


# ── Documentación técnica Anexo IV ────────────────────────────────────────────


class DocumentacionTecnicaAnexoIV:
    """Genera la plantilla de documentación técnica requerida por el Anexo IV (alto riesgo).

    Ejemplo::

        doc = DocumentacionTecnicaAnexoIV()
        md = doc.generar_plantilla({
            "nombre_sistema": "Mi sistema de IA",
            "version": "1.0.0",
            "proveedor": "Acme SL",
        })
    """

    SECCIONES = [
        ("1", "Descripción del sistema de IA y su propósito previsto"),
        ("2", "Nombre y datos de contacto del proveedor"),
        ("3", "Versión del software y fecha de la versión"),
        ("4", "Descripción de los componentes de hardware"),
        ("5", "Descripción general del sistema (arquitectura, lógica de decisión)"),
        ("6", "Descripción de los datos de entrenamiento, validación y prueba"),
        ("7", "Descripción del proceso de entrenamiento y validación"),
        ("8", "Descripción del sistema de supervisión y métricas de rendimiento"),
        ("9", "Riesgos conocidos y medidas de mitigación adoptadas"),
        ("10", "Descripción de las modificaciones relevantes durante el ciclo de vida"),
    ]

    def generar_plantilla(self, datos: dict) -> str:
        """Genera plantilla Markdown de documentación técnica Anexo IV."""
        lineas = [
            "# Documentación Técnica — AI Act Anexo IV",
            "",
            f"**Sistema:** {datos.get('nombre_sistema', '[COMPLETAR]')}  ",
            f"**Versión:** {datos.get('version', '[COMPLETAR]')}  ",
            f"**Proveedor:** {datos.get('proveedor', '[COMPLETAR]')}  ",
            f"**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  ",
            "",
        ]
        for num, titulo in self.SECCIONES:
            clave = f"seccion_{num}"
            valor = datos.get(clave, "_[PENDIENTE DE COMPLETAR]_")
            lineas += [f"## {num}. {titulo}", "", valor, ""]
        return "\n".join(lineas)


# ── ISO 42001 — Registro de modelos ──────────────────────────────────────────


@dataclass
class ModeloIA:
    """Entrada del registro de modelos de IA (ISO 42001 — AIMS)."""

    nombre: str
    version: str
    proveedor: str
    propósito: str
    nivel_riesgo: NivelRiesgoIA
    datos_entrenamiento: str  # descripción, no datos en bruto
    fecha_despliegue: str
    responsable: str
    en_produccion: bool = True
    notas: str = ""


class RegistroModelosIA:
    """Registro central de sistemas de IA en uso (ISO 42001 — AIMS, cláusula 6.1).

    Ejemplo::

        registro = RegistroModelosIA()
        registro.registrar(ModeloIA(
            nombre="Chatbot-Soporte",
            version="2.1",
            proveedor="Anthropic",
            propósito="Atención al cliente",
            nivel_riesgo=NivelRiesgoIA.LIMITADO,
            datos_entrenamiento="Datos públicos + conversaciones anonimizadas",
            fecha_despliegue="2026-01-15",
            responsable="equipo-ia@empresa.com",
        ))
        activos = registro.modelos_en_produccion()
    """

    def __init__(self):
        self._modelos: list[ModeloIA] = []

    def registrar(self, modelo: ModeloIA) -> None:
        self._modelos.append(modelo)

    def modelos_en_produccion(self) -> list[ModeloIA]:
        return [m for m in self._modelos if m.en_produccion]

    def modelos_por_riesgo(self, nivel: NivelRiesgoIA) -> list[ModeloIA]:
        return [m for m in self._modelos if m.nivel_riesgo == nivel]

    def resumen(self) -> dict:
        return {
            "total": len(self._modelos),
            "en_produccion": len(self.modelos_en_produccion()),
            "por_nivel": {
                nivel.value: len(self.modelos_por_riesgo(nivel)) for nivel in NivelRiesgoIA
            },
        }


# ── ISO 23894 — Registro de riesgos de IA ────────────────────────────────────


@dataclass
class RiesgoIA:
    """Entrada del registro de riesgos de IA (ISO 23894 — AI risk management)."""

    id: str  # p.ej. "RIESGO-001"
    descripcion: str
    fase_ciclo_vida: str  # diseño / entrenamiento / despliegue / operación / retirada
    probabilidad: int  # 1-5
    impacto: int  # 1-5
    medidas_mitigacion: list[str]
    propietario: str
    estado: str = "abierto"  # abierto / en-mitigacion / cerrado / aceptado


class RegistroRiesgosIA:
    """Registro de riesgos de IA por ciclo de vida (ISO 23894 — cláusula 6.3).

    La puntuación de riesgo es probabilidad × impacto (1-25).
    Niveles: 1-5 bajo · 6-12 medio · 13-25 alto.

    Ejemplo::

        registro = RegistroRiesgosIA()
        registro.añadir(RiesgoIA(
            id="RIESGO-001",
            descripcion="Sesgo en decisiones de contratación",
            fase_ciclo_vida="despliegue",
            probabilidad=3,
            impacto=5,
            medidas_mitigacion=["Auditoría mensual de fairness", "Dataset balanceado"],
            propietario="equipo-ia@empresa.com",
        ))
        altos = registro.riesgos_altos()
    """

    def __init__(self):
        self._riesgos: list[RiesgoIA] = []

    def añadir(self, riesgo: RiesgoIA) -> None:
        self._riesgos.append(riesgo)

    def puntuacion(self, riesgo: RiesgoIA) -> int:
        return riesgo.probabilidad * riesgo.impacto

    def riesgos_altos(self) -> list[RiesgoIA]:
        return [r for r in self._riesgos if self.puntuacion(r) >= 13]

    def riesgos_abiertos(self) -> list[RiesgoIA]:
        return [r for r in self._riesgos if r.estado == "abierto"]

    def resumen(self) -> dict:
        return {
            "total": len(self._riesgos),
            "abiertos": len(self.riesgos_abiertos()),
            "altos": len(self.riesgos_altos()),
            "por_fase": self._contar_por("fase_ciclo_vida"),
            "por_estado": self._contar_por("estado"),
        }

    def _contar_por(self, atributo: str) -> dict:
        conteo: dict = {}
        for r in self._riesgos:
            clave = getattr(r, atributo)
            conteo[clave] = conteo.get(clave, 0) + 1
        return conteo
