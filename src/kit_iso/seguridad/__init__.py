# Importamos Fernet, que es un estándar de encriptación simétrica seguro.
from cryptography.fernet import Fernet
# Importamos el módulo de logging nativo de Python para registrar eventos.
import logging

# Configuramos el sistema de logs para que muestre la hora, el nivel de alerta y el mensaje.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Creamos un objeto 'logger' asociado a este archivo específico.
logger = logging.getLogger(__name__)

# Definimos la clase principal para nuestras herramientas de seguridad.
class ToolkitSeguridad:
    # El método __init__ se ejecuta automáticamente al crear un objeto de esta clase.
    def __init__(self):
        # Generamos y guardamos una clave secreta en la variable 'self.key'.
        self.key = self.generar_clave()
        # Registramos en el log que el toolkit se ha iniciado (útil para auditorías ISO 27001).
        logger.info("Toolkit de Seguridad inicializado correctamente.")

    # Método para generar una clave criptográfica nueva.
    def generar_clave(self) -> bytes:
        # Usamos Fernet para generar una clave segura de 32 bytes en base64.
        return Fernet.generate_key()

    # Método para encriptar un texto (recibe un string, devuelve bytes).
    def encriptar_datos(self, datos: str) -> bytes:
        # Creamos una instancia de Fernet usando nuestra clave secreta.
        fernet = Fernet(self.key)
        # Convertimos el string 'datos' a bytes (.encode()) y lo encriptamos.
        datos_encriptados = fernet.encrypt(datos.encode())
        # Registramos la acción (sin revelar el dato) para trazabilidad.
        logger.info("Datos encriptados con éxito.")
        # Devolvemos el resultado ilegible.
        return datos_encriptados

    # Método para desencriptar (recibe bytes, devuelve el string original).
    def desencriptar_datos(self, encriptados: bytes) -> str:
        # Creamos la instancia de Fernet con la misma clave.
        fernet = Fernet(self.key)
        # Desencriptamos y luego convertimos los bytes a string (.decode()).
        return fernet.decrypt(encriptados).decode()