"""Tests del triaje, los perfiles y la configuración `kit-iso.toml`."""

import pytest

from kit_iso import perfiles
from kit_iso.perfiles import (
    MODULOS,
    MODULOS_BASE,
    PERFILES,
    PREGUNTAS,
    Configuracion,
    Respuesta,
    a_toml,
    cargar,
    detectar,
    guardar,
    localizar,
    modulos_desde_respuestas,
    respuestas_de_perfil,
)

# ── Triaje → módulos ──────────────────────────────────────────────────────────


def test_sin_respuestas_solo_modulos_base():
    activos, pendientes = modulos_desde_respuestas({})
    assert activos == list(MODULOS_BASE)
    assert pendientes == []


def test_web_activa_accesibilidad_y_usabilidad():
    activos, _ = modulos_desde_respuestas({"web": Respuesta(True)})
    assert "accesibilidad" in activos
    assert "usabilidad" in activos


def test_respuesta_negativa_no_activa():
    activos, _ = modulos_desde_respuestas({"web": Respuesta(False)})
    assert "accesibilidad" not in activos


def test_sector_publico_queda_pendiente():
    activos, pendientes = modulos_desde_respuestas({"sector_publico": Respuesta(True)})
    assert "ens" not in activos
    assert pendientes == ["ens"]


def test_todas_las_preguntas_apuntan_a_modulos_conocidos():
    for p in PREGUNTAS:
        for m in p.modulos:
            assert m in MODULOS


def test_perfil_desconocido_falla():
    with pytest.raises(ValueError, match="Perfil desconocido"):
        respuestas_de_perfil("inexistente")


@pytest.mark.parametrize("perfil", list(PERFILES))
def test_todos_los_perfiles_generan_configuracion(perfil):
    cfg = Configuracion.desde_respuestas(respuestas_de_perfil(perfil), perfil=perfil)
    assert set(MODULOS_BASE) <= set(cfg.modulos)
    assert cfg.perfil == perfil


def test_perfil_agente_llm_activa_ai_act():
    cfg = Configuracion.desde_respuestas(respuestas_de_perfil("agente-llm"))
    assert "ai_act" in cfg.modulos


# ── TOML ida y vuelta ─────────────────────────────────────────────────────────


def test_toml_ida_y_vuelta(tmp_path):
    respuestas = {
        "web": Respuesta(True, "3 archivo(s) .html"),
        "datos_personales": Respuesta(False, "sin campos típicos"),
        "sector_publico": Respuesta(True, "confirmado por el responsable"),
    }
    cfg = Configuracion.desde_respuestas(respuestas, perfil="web", excluir=["ejemplos/*"])
    ruta = guardar(cfg, tmp_path / "kit-iso.toml")

    leida = cargar(ruta)
    assert leida.modulos == cfg.modulos
    assert leida.pendientes == ["ens"]
    assert leida.perfil == "web"
    assert leida.excluir == ["ejemplos/*"]
    assert leida.triaje["web"].valor is True
    assert leida.triaje["web"].justificacion == "3 archivo(s) .html"
    assert leida.triaje["datos_personales"].valor is False


def test_toml_justificacion_con_comillas_y_acentos(tmp_path):
    cfg = Configuracion.desde_respuestas({"ia": Respuesta(True, 'dependencias: "openai", más')})
    leida = cargar(guardar(cfg, tmp_path / "kit-iso.toml"))
    assert leida.triaje["ia"].justificacion == 'dependencias: "openai", más'


def test_toml_contiene_version_del_kit():
    cfg = Configuracion.desde_respuestas({})
    assert f'version = "{perfiles.__version__}"' in a_toml(cfg)


def test_cargar_sin_seccion_falla(tmp_path):
    f = tmp_path / "kit-iso.toml"
    f.write_text("[otra]\nx = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"\[kit-iso\]"):
        cargar(f)


def test_cargar_modulo_desconocido_falla(tmp_path):
    f = tmp_path / "kit-iso.toml"
    f.write_text('[kit-iso]\nmodulos = ["seguridad", "magia"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="magia"):
        cargar(f)


def test_localizar_en_padres(tmp_path):
    (tmp_path / "kit-iso.toml").write_text("[kit-iso]\nmodulos = []\n", encoding="utf-8")
    sub = tmp_path / "src" / "paquete"
    sub.mkdir(parents=True)
    assert localizar(sub) == tmp_path / "kit-iso.toml"


def test_localizar_ausente(tmp_path):
    assert localizar(tmp_path) is None


# ── Detección ─────────────────────────────────────────────────────────────────


def test_detectar_proyecto_vacio_todo_negativo(tmp_path):
    r = detectar(tmp_path)
    assert set(r) == {p.id for p in PREGUNTAS}
    assert not any(v.valor for v in r.values())
    assert all(v.justificacion for v in r.values())


def test_detectar_web_por_html(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    r = detectar(tmp_path)
    assert r["web"].valor is True
    assert ".html" in r["web"].justificacion


def test_detectar_bd_e_ia_por_dependencias(tmp_path):
    (tmp_path / "requirements.txt").write_text("sqlalchemy>=2\nopenai>=1\n", encoding="utf-8")
    r = detectar(tmp_path)
    assert r["base_datos"].valor is True
    assert "sqlalchemy" in r["base_datos"].justificacion
    assert r["ia"].valor is True
    assert "openai" in r["ia"].justificacion


def test_detectar_datos_personales_por_campos(tmp_path):
    (tmp_path / "modelos.py").write_text("class Usuario:\n    email: str\n", encoding="utf-8")
    r = detectar(tmp_path)
    assert r["datos_personales"].valor is True
    assert "modelos.py" in r["datos_personales"].justificacion


def test_detectar_producto_por_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert detectar(tmp_path)["producto"].valor is True


def test_detectar_ignora_node_modules_y_venv(tmp_path):
    nm = tmp_path / "node_modules" / "lib"
    nm.mkdir(parents=True)
    (nm / "x.html").write_text("<html></html>", encoding="utf-8")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "m.py").write_text("email = 1\n", encoding="utf-8")
    r = detectar(tmp_path)
    assert r["web"].valor is False
    assert r["datos_personales"].valor is False


def test_sector_publico_nunca_se_detecta(tmp_path):
    r = detectar(tmp_path)
    assert r["sector_publico"].valor is False
    assert "confirmar" in r["sector_publico"].justificacion
