"""Tests del módulo ai_act: clasificador, transparencia, registro de decisiones, gobernanza."""

from kit_iso.ai_act import (
    ClasificadorRiesgoIA,
    DocumentacionTecnicaAnexoIV,
    ModeloIA,
    NivelRiesgoIA,
    RegistroDecisionesIA,
    RegistroModelosIA,
    RegistroRiesgosIA,
    RiesgoIA,
    TransparenciaIA,
)

# ── ClasificadorRiesgoIA ─────────────────────────────────────────────────────


def test_clasificador_prohibido():
    clf = ClasificadorRiesgoIA()
    r = clf.clasificar({"manipulacion_subliminal": True})
    assert r["nivel"] == NivelRiesgoIA.PROHIBIDO
    assert "Art. 5" in r["base_legal"]


def test_clasificador_alto_riesgo():
    r = ClasificadorRiesgoIA().clasificar({"infraestructura_critica": True})
    assert r["nivel"] == NivelRiesgoIA.ALTO
    assert len(r["obligaciones"]) >= 5


def test_clasificador_limitado_chatbot():
    r = ClasificadorRiesgoIA().clasificar({"interactua_humanos": True})
    assert r["nivel"] == NivelRiesgoIA.LIMITADO
    assert any("50.1" in ob for ob in r["obligaciones"])


def test_clasificador_limitado_genera_contenido():
    r = ClasificadorRiesgoIA().clasificar({"genera_contenido": True})
    assert r["nivel"] == NivelRiesgoIA.LIMITADO
    assert any("50.2" in ob for ob in r["obligaciones"])


def test_clasificador_minimo_riesgo():
    r = ClasificadorRiesgoIA().clasificar({})
    assert r["nivel"] == NivelRiesgoIA.MINIMO
    assert not r["obligaciones"]


def test_clasificador_prohibido_tiene_prioridad_sobre_alto():
    r = ClasificadorRiesgoIA().clasificar(
        {"manipulacion_subliminal": True, "infraestructura_critica": True}
    )
    assert r["nivel"] == NivelRiesgoIA.PROHIBIDO


def test_clasificador_incluye_fecha_aplicacion():
    r = ClasificadorRiesgoIA().clasificar({"interactua_humanos": True})
    assert "fecha_aplicacion" in r
    assert "2026" in r["fecha_aplicacion"]


# ── TransparenciaIA ──────────────────────────────────────────────────────────


def test_aviso_chatbot_espanol():
    texto = TransparenciaIA().aviso_chatbot("es")
    assert "inteligencia artificial" in texto.lower()
    assert "persona" in texto.lower()


def test_aviso_chatbot_ingles():
    texto = TransparenciaIA().aviso_chatbot("en")
    assert "artificial intelligence" in texto.lower()


def test_aviso_chatbot_idioma_desconocido_usa_espanol():
    texto = TransparenciaIA().aviso_chatbot("xx")
    assert "inteligencia artificial" in texto.lower()


def test_marcar_contenido_generado():
    resultado = TransparenciaIA().marcar_contenido_generado("Texto generado")
    assert resultado["ia_generado"] is True
    assert resultado["contenido"] == "Texto generado"
    assert "50.2" in resultado["norma"]
    assert "timestamp" in resultado


def test_declaracion_asistencia_ia():
    decl = TransparenciaIA().declaracion_asistencia_ia(
        descripcion_sistema="Sistema X",
        tareas_asistidas=["Redacción", "Traducción"],
        supervision_humana=True,
    )
    assert "Sistema X" in decl
    assert "Redacción" in decl
    assert "supervisión humana" in decl


# ── RegistroDecisionesIA ─────────────────────────────────────────────────────


def test_registro_crea_entrada():
    reg = RegistroDecisionesIA("sistema-test")
    entrada = reg.nueva_entrada(
        input_hash="sha256:abc123",
        output_resumen="Aprobado",
        confianza=0.92,
        supervisado_por_humano=True,
    )
    assert entrada.input_hash == "sha256:abc123"
    assert entrada.confianza == 0.92
    assert entrada.supervisado_por_humano is True


def test_registro_asigna_sistema_id():
    reg = RegistroDecisionesIA("mi-sistema")
    entrada = reg.nueva_entrada("h", "salida")
    reg.registrar(entrada)
    assert entrada.sistema_id == "mi-sistema"


def test_registro_tiene_timestamp():
    reg = RegistroDecisionesIA("s")
    entrada = reg.nueva_entrada("h", "salida")
    assert entrada.timestamp
    assert "T" in entrada.timestamp  # formato ISO 8601


# ── DocumentacionTecnicaAnexoIV ──────────────────────────────────────────────


def test_plantilla_contiene_secciones_requeridas():
    doc = DocumentacionTecnicaAnexoIV()
    md = doc.generar_plantilla({"nombre_sistema": "TestSys", "version": "1.0", "proveedor": "Acme"})
    assert "TestSys" in md
    assert "Acme" in md
    assert "Anexo IV" in md
    for num, _ in doc.SECCIONES:
        assert f"## {num}." in md


def test_plantilla_sin_datos_tiene_placeholders():
    md = DocumentacionTecnicaAnexoIV().generar_plantilla({})
    assert "[COMPLETAR]" in md
    assert "PENDIENTE" in md


# ── RegistroModelosIA ────────────────────────────────────────────────────────


def test_registro_modelos_registra_y_filtra():
    reg = RegistroModelosIA()
    modelo = ModeloIA(
        nombre="ChatBot",
        version="1.0",
        proveedor="Empresa",
        propósito="Soporte",
        nivel_riesgo=NivelRiesgoIA.LIMITADO,
        datos_entrenamiento="Texto público",
        fecha_despliegue="2026-08-01",
        responsable="ia@empresa.com",
    )
    reg.registrar(modelo)
    assert len(reg.modelos_en_produccion()) == 1
    assert len(reg.modelos_por_riesgo(NivelRiesgoIA.LIMITADO)) == 1
    assert len(reg.modelos_por_riesgo(NivelRiesgoIA.ALTO)) == 0


def test_resumen_registro_modelos():
    reg = RegistroModelosIA()
    reg.registrar(ModeloIA("M1", "1", "P", "x", NivelRiesgoIA.LIMITADO, "d", "2026-01-01", "r"))
    reg.registrar(
        ModeloIA(
            "M2", "1", "P", "x", NivelRiesgoIA.ALTO, "d", "2026-01-01", "r", en_produccion=False
        )
    )
    resumen = reg.resumen()
    assert resumen["total"] == 2
    assert resumen["en_produccion"] == 1
    assert resumen["por_nivel"]["limitado"] == 1


# ── RegistroRiesgosIA ────────────────────────────────────────────────────────


def test_riesgo_puntuacion_correcta():
    reg = RegistroRiesgosIA()
    riesgo = RiesgoIA(
        id="R001",
        descripcion="Sesgo",
        fase_ciclo_vida="despliegue",
        probabilidad=3,
        impacto=5,
        medidas_mitigacion=["Auditoría mensual"],
        propietario="equipo-ia@empresa.com",
    )
    reg.añadir(riesgo)
    assert reg.puntuacion(riesgo) == 15
    assert riesgo in reg.riesgos_altos()


def test_riesgo_bajo_no_es_alto():
    reg = RegistroRiesgosIA()
    bajo = RiesgoIA("R002", "Leve", "diseño", 1, 2, [], "r")
    reg.añadir(bajo)
    assert bajo not in reg.riesgos_altos()


def test_registro_riesgos_resumen():
    reg = RegistroRiesgosIA()
    reg.añadir(RiesgoIA("R001", "A", "despliegue", 4, 4, [], "r", estado="abierto"))
    reg.añadir(RiesgoIA("R002", "B", "operación", 1, 1, [], "r", estado="cerrado"))
    resumen = reg.resumen()
    assert resumen["total"] == 2
    assert resumen["abiertos"] == 1
    assert resumen["altos"] == 1
    assert resumen["por_fase"]["despliegue"] == 1
