"""HerramientasAccesibilidad — validación WCAG 2.1 (ISO 40500)."""

import re
from bs4 import BeautifulSoup

# Textos de enlace considerados no descriptivos (WCAG 2.4.4).
_TEXTOS_NO_DESCRIPTIVOS = {
    "click aquí",
    "click here",
    "aquí",
    "here",
    "más",
    "more",
    "leer más",
    "read more",
    "ver más",
    "este enlace",
    "this link",
    "enlace",
    "link",
    "haga clic",
    "pulse aquí",
}


class HerramientasAccesibilidad:
    """Valida criterios WCAG 2.1 sobre HTML (ISO 40500).

    Criterios cubiertos:
        - 1.1.1 — Contenido no textual (imágenes sin alt)
        - 1.3.1 — Información y relaciones (jerarquía de encabezados)
        - 1.4.3 — Contraste mínimo (colores inline en hex)
        - 2.4.4 — Propósito de los enlaces (texto descriptivo)
        - 3.1.1 — Idioma de la página (atributo lang)
        - 3.3.2 — Etiquetas o instrucciones (inputs con label asociado)
    """

    def validar_html_accesible(self, html_str: str) -> dict:
        """Valida todos los criterios WCAG 2.1 implementados sobre el HTML.

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "WCAG 2.1",
                "hallazgos": [{"criterio": "1.1.1", "mensaje": "..."}, ...],
                "criterios_ok": ["1.1.1", "3.1.1", ...]
            }
        """
        soup = BeautifulSoup(html_str, "html.parser")
        hallazgos = []
        criterios_ok = []

        checks = [
            ("1.1.1", self._check_1_1_1_alt_text),
            ("1.3.1", self._check_1_3_1_headings),
            ("1.4.3", self._check_1_4_3_contraste),
            ("2.4.4", self._check_2_4_4_enlaces),
            ("3.1.1", self._check_3_1_1_lang),
            ("3.3.2", self._check_3_3_2_labels),
        ]

        for criterio, fn in checks:
            fallos = fn(soup)
            if fallos:
                for mensaje in fallos:
                    hallazgos.append({"criterio": criterio, "mensaje": mensaje})
            else:
                criterios_ok.append(criterio)

        return {
            "estado": "fallo" if hallazgos else "ok",
            "norma": "WCAG 2.1",
            "hallazgos": hallazgos,
            "criterios_ok": criterios_ok,
        }

    # ── Criterios individuales ────────────────────────────────────────────

    def _check_1_1_1_alt_text(self, soup: BeautifulSoup) -> list[str]:
        """1.1.1 — Imágenes sin atributo alt."""
        fallos = []
        for img in soup.find_all("img"):
            if img.get("alt") is None:
                src = img.get("src", "sin src")
                fallos.append(f"<img> sin atributo alt: '{src}'")
        return fallos

    def _check_1_3_1_headings(self, soup: BeautifulSoup) -> list[str]:
        """1.3.1 — Jerarquía de encabezados: no se pueden saltar niveles."""
        fallos = []
        nivel_anterior = 0
        for tag in soup.find_all(re.compile(r"^h[1-6]$")):
            nivel = int(tag.name[1])
            if nivel_anterior > 0 and nivel > nivel_anterior + 1:
                fallos.append(
                    f"Salto de encabezado de h{nivel_anterior} a h{nivel} "
                    f"(texto: '{tag.get_text(strip=True)[:40]}')"
                )
            nivel_anterior = nivel
        return fallos

    def _check_1_4_3_contraste(self, soup: BeautifulSoup) -> list[str]:
        """1.4.3 — Contraste mínimo 4.5:1 para texto normal (solo colores hex inline)."""
        fallos = []
        for tag in soup.find_all(style=True):
            style = tag.get("style", "")
            color = self._extraer_color_hex(style, "color")
            bg = self._extraer_color_hex(style, "background-color")
            if color and bg:
                ratio = self._ratio_contraste(self._luminancia(*color), self._luminancia(*bg))
                if ratio < 4.5:
                    texto_preview = tag.get_text(strip=True)[:30]
                    fallos.append(
                        f"Contraste insuficiente {ratio:.2f}:1 (mínimo 4.5:1) "
                        f"en '{texto_preview}'"
                    )
        return fallos

    def _check_2_4_4_enlaces(self, soup: BeautifulSoup) -> list[str]:
        """2.4.4 — Texto de enlace no descriptivo ("click aquí", "más", etc.)."""
        fallos = []
        for a in soup.find_all("a", href=True):
            texto = a.get_text(strip=True).lower()
            if texto in _TEXTOS_NO_DESCRIPTIVOS:
                href = a.get("href", "")[:40]
                fallos.append(f"Enlace no descriptivo: texto='{texto}', href='{href}'")
        return fallos

    def _check_3_1_1_lang(self, soup: BeautifulSoup) -> list[str]:
        """3.1.1 — Atributo lang en el elemento <html>."""
        html_tag = soup.find("html")
        if html_tag and not html_tag.get("lang"):
            return ["Elemento <html> sin atributo lang (ej. lang='es')"]
        return []

    def _check_3_3_2_labels(self, soup: BeautifulSoup) -> list[str]:
        """3.3.2 — Inputs de formulario sin label asociado."""
        fallos = []
        tipos_ignorados = {"submit", "reset", "button", "hidden", "image"}
        for inp in soup.find_all("input"):
            tipo = inp.get("type", "text").lower()
            if tipo in tipos_ignorados:
                continue
            inp_id = inp.get("id")
            aria_label = inp.get("aria-label") or inp.get("aria-labelledby")
            # Tiene label explícito via for/id
            label_explicito = False
            if inp_id:
                label_explicito = bool(soup.find("label", attrs={"for": inp_id}))
            # Está dentro de un <label>
            en_label = bool(inp.find_parent("label"))

            if not label_explicito and not en_label and not aria_label:
                nombre = inp.get("name") or inp.get("id") or inp.get("placeholder", "sin nombre")
                fallos.append(f"<input name='{nombre}'> sin label asociado")
        return fallos

    # ── Utilidades de contraste ───────────────────────────────────────────

    def _extraer_color_hex(self, style: str, propiedad: str) -> tuple[int, int, int] | None:
        """Extrae el color hex de una propiedad CSS en un atributo style inline."""
        patron = propiedad.replace("-", r"\-") + r"\s*:\s*(#[0-9a-fA-F]{3,6})"
        m = re.search(patron, style, re.IGNORECASE)
        if not m:
            return None
        return self._parsear_hex(m.group(1))

    @staticmethod
    def _parsear_hex(color: str) -> tuple[int, int, int] | None:
        color = color.strip().lstrip("#")
        if len(color) == 3:
            color = "".join(c * 2 for c in color)
        if len(color) != 6:
            return None
        try:
            return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        except ValueError:
            return None

    @staticmethod
    def _luminancia(r: int, g: int, b: int) -> float:
        """Luminancia relativa WCAG (sRGB)."""

        def canal(c: int) -> float:
            v = c / 255.0
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

        return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)

    @staticmethod
    def _ratio_contraste(lum1: float, lum2: float) -> float:
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)
