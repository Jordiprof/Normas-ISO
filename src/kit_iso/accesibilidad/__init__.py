# Importamos BeautifulSoup para parsear HTML.
from bs4 import BeautifulSoup

class HerramientasAccesibilidad:
    
    def validar_html_accesible(self, html_str: str) -> dict:
        """
        Valida accesibilidad básica WCAG 2.1 sobre un HTML.
        
        Retorna:
            {
                "estado": "ok" | "fallo",
                "norma": "WCAG 2.1",
                "criterio": "1.1.1",
                "descripcion": "...",
                "hallazgos": ["...", "..."]  # lista vacía si todo ok
            }
        """
        soup = BeautifulSoup(html_str, 'html.parser')
        hallazgos = []

        # ✅ Check WCAG 1.1.1 — imágenes sin texto alternativo.
        for img in soup.find_all('img'):
            if not img.get('alt'):
                src = img.get('src', 'sin src')
                hallazgos.append(f"Img sin atributo alt: '{src}'")

        # ✅ Devolvemos dict estructurado — fácil de procesar por otros módulos.
        if hallazgos:
            return {
                "estado": "fallo",
                "norma": "WCAG 2.1",
                "criterio": "1.1.1",
                "descripcion": "Se encontraron imágenes sin texto alternativo.",
                "hallazgos": hallazgos
            }
        
        return {
            "estado": "ok",
            "norma": "WCAG 2.1",
            "criterio": "1.1.1",
            "descripcion": "Validación básica de accesibilidad superada.",
            "hallazgos": []
        }