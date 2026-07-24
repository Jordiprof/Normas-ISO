"""Tests de HerramientasAccesibilidad: criterios WCAG 2.1."""

import pytest

from kit_iso.accesibilidad import HerramientasAccesibilidad


@pytest.fixture
def acc():
    return HerramientasAccesibilidad()


# ── 1.1.1 — Alt text ─────────────────────────────────────────────────────────


def test_1_1_1_imagen_sin_alt_detectada(acc):
    html = '<img src="foto.jpg">'
    resultado = acc.validar_html_accesible(html)
    assert resultado["estado"] == "fallo"
    criterios = [h["criterio"] for h in resultado["hallazgos"]]
    assert "1.1.1" in criterios


def test_1_1_1_imagen_con_alt_ok(acc):
    html = '<img src="foto.jpg" alt="Descripción de la foto">'
    resultado = acc.validar_html_accesible(html)
    assert "1.1.1" not in [h["criterio"] for h in resultado["hallazgos"]]
    assert "1.1.1" in resultado["criterios_ok"]


# ── 1.3.1 — Jerarquía de encabezados ─────────────────────────────────────────


def test_1_3_1_salto_de_encabezado_detectado(acc):
    html = "<h1>Título</h1><h3>Subsección</h3>"  # salta h2
    resultado = acc.validar_html_accesible(html)
    criterios = [h["criterio"] for h in resultado["hallazgos"]]
    assert "1.3.1" in criterios


def test_1_3_1_jerarquia_correcta_ok(acc):
    html = "<h1>Título</h1><h2>Sección</h2><h3>Subsección</h3>"
    resultado = acc.validar_html_accesible(html)
    assert "1.3.1" not in [h["criterio"] for h in resultado["hallazgos"]]


# ── 1.4.3 — Contraste ────────────────────────────────────────────────────────


def test_1_4_3_contraste_insuficiente(acc):
    # #ccc sobre #fff → contraste ~1.6:1, muy por debajo de 4.5:1
    html = '<p style="color: #cccccc; background-color: #ffffff">Texto difícil de leer</p>'
    resultado = acc.validar_html_accesible(html)
    criterios = [h["criterio"] for h in resultado["hallazgos"]]
    assert "1.4.3" in criterios


def test_1_4_3_contraste_suficiente_ok(acc):
    # #000 sobre #fff → contraste 21:1
    html = '<p style="color: #000000; background-color: #ffffff">Texto legible</p>'
    resultado = acc.validar_html_accesible(html)
    assert "1.4.3" not in [h["criterio"] for h in resultado["hallazgos"]]


def test_1_4_3_sin_estilos_inline_no_falla(acc):
    html = '<p class="texto-claro">Sin estilos inline</p>'
    resultado = acc.validar_html_accesible(html)
    assert "1.4.3" not in [h["criterio"] for h in resultado["hallazgos"]]


# ── 2.4.4 — Propósito de enlaces ─────────────────────────────────────────────


def test_2_4_4_enlace_no_descriptivo(acc):
    html = '<a href="/docs">click aquí</a>'
    resultado = acc.validar_html_accesible(html)
    criterios = [h["criterio"] for h in resultado["hallazgos"]]
    assert "2.4.4" in criterios


def test_2_4_4_enlace_descriptivo_ok(acc):
    html = '<a href="/docs">Documentación de la API</a>'
    resultado = acc.validar_html_accesible(html)
    assert "2.4.4" not in [h["criterio"] for h in resultado["hallazgos"]]


# ── 3.1.1 — Atributo lang ────────────────────────────────────────────────────


def test_3_1_1_html_sin_lang_detectado(acc):
    html = "<html><body><p>Hola</p></body></html>"
    resultado = acc.validar_html_accesible(html)
    criterios = [h["criterio"] for h in resultado["hallazgos"]]
    assert "3.1.1" in criterios


def test_3_1_1_html_con_lang_ok(acc):
    html = '<html lang="es"><body><p>Hola</p></body></html>'
    resultado = acc.validar_html_accesible(html)
    assert "3.1.1" not in [h["criterio"] for h in resultado["hallazgos"]]


def test_3_1_1_fragmento_sin_html_no_falla(acc):
    # Un fragmento sin <html> no puede tener lang → no se reporta fallo.
    html = "<div><p>Fragmento</p></div>"
    resultado = acc.validar_html_accesible(html)
    assert "3.1.1" not in [h["criterio"] for h in resultado["hallazgos"]]


# ── 3.3.2 — Labels de formulario ─────────────────────────────────────────────


def test_3_3_2_input_sin_label(acc):
    html = '<form><input type="text" name="email"></form>'
    resultado = acc.validar_html_accesible(html)
    criterios = [h["criterio"] for h in resultado["hallazgos"]]
    assert "3.3.2" in criterios


def test_3_3_2_input_con_label_explicito_ok(acc):
    html = (
        '<form><label for="email">Email</label><input type="text" id="email" name="email"></form>'
    )
    resultado = acc.validar_html_accesible(html)
    assert "3.3.2" not in [h["criterio"] for h in resultado["hallazgos"]]


def test_3_3_2_input_envuelto_en_label_ok(acc):
    html = "<form><label>Email <input type='text' name='email'></label></form>"
    resultado = acc.validar_html_accesible(html)
    assert "3.3.2" not in [h["criterio"] for h in resultado["hallazgos"]]


def test_3_3_2_input_con_aria_label_ok(acc):
    html = '<form><input type="text" name="busqueda" aria-label="Buscar en el sitio"></form>'
    resultado = acc.validar_html_accesible(html)
    assert "3.3.2" not in [h["criterio"] for h in resultado["hallazgos"]]


def test_3_3_2_input_hidden_ignorado(acc):
    html = '<form><input type="hidden" name="csrf_token" value="abc"></form>'
    resultado = acc.validar_html_accesible(html)
    assert "3.3.2" not in [h["criterio"] for h in resultado["hallazgos"]]


# ── Integración ───────────────────────────────────────────────────────────────


def test_html_completamente_accesible_ok(acc):
    html = """
    <html lang="es">
      <body>
        <h1>Título</h1>
        <h2>Sección</h2>
        <img src="logo.png" alt="Logo de la empresa">
        <p style="color: #000000; background-color: #ffffff">Texto legible</p>
        <a href="/contacto">Formulario de contacto</a>
        <form>
          <label for="nombre">Nombre</label>
          <input type="text" id="nombre" name="nombre">
        </form>
      </body>
    </html>
    """
    resultado = acc.validar_html_accesible(html)
    assert resultado["estado"] == "ok"
    assert not resultado["hallazgos"]
    assert len(resultado["criterios_ok"]) == 6
