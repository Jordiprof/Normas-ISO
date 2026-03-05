# Importamos el módulo de expresiones regulares para buscar patrones en el texto.
import re

# Definimos la clase que se encargará de validar reglas de la norma ISO 27001.
class ValidadorSeguridad:
    # El método inicializador (constructor) de la clase.
    def __init__(self):
        # Creamos una lista de patrones prohibidos (Secretos/Passwords expuestos).
        # Esto cumple con el control de criptografía y gestión de secretos[cite: 66].
        self.patrones_criticos = [
            r'password\s*=\s*[\'"].+[\'"]',  # Busca contraseñas escritas directamente.
            r'api_key\s*=\s*[\'"].+[\'"]',   # Busca claves de API expuestas.
            r'secret\s*=\s*[\'"].+[\'"]'      # Busca secretos de aplicación.
        ]

    # Método para analizar un archivo de código fuente.
    def analizar_codigo(self, contenido_codigo: str):
        # Iniciamos una lista vacía para guardar los fallos encontrados.
        hallazgos = []
        
        # Recorremos cada patrón de nuestra lista de seguridad.
        for patron in self.patrones_criticos:
            # Si encontramos el patrón prohibido dentro del código...
            if re.search(patron, contenido_codigo, re.IGNORECASE):
                # ...añadimos un mensaje de error a nuestra lista de hallazgos.
                hallazgos.append(f"RIESGO ISO 27001: Se detectó un secreto expuesto (patrón: {patron})")
        
        # Devolvemos la lista de fallos (si está vacía, el código es seguro).
        return hallazgos

# Ejemplo de uso interno (para que el agente sepa cómo llamarlo).
# validador = ValidadorSeguridad()
# errores = validador.analizar_codigo("password = '123'")