# Importamos BeautifulSoup para parse HTML (gratuito).
from bs4 import BeautifulSoup

class HerramientasAccesibilidad:
    def validar_html_accesible(self, html_str: str):
        # Parseamos el HTML.
        soup = BeautifulSoup(html_str, 'html.parser')
        # Check básico WCAG: alt en imgs.
        for img in soup.find_all('img'):
            if not img.get('alt'):
                return "Fallo: Img sin alt (WCAG 1.1.1)."
        return "OK: Básico accesible."