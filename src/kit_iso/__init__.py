# Importamos el módulo nativo de logging para rastrear la actividad del kit (ISO 27001)[cite: 43, 59].
import logging
# Importamos submódulos para acceso fácil (simplifica imports, práctica estándar).
from .seguridad import HerramientasSeguridad  # Ejemplo.
from .usabilidad import HerramientasUsabilidad
from .base_datos import BaseDatosSegura
# ... (agrega más según avances).
# Definimos la versión actual de nuestro toolkit de cumplimiento normativo[cite: 155].
__version__ = "0.1.0"

# Configuramos el formato básico de los mensajes que el agente verá en la consola[cite: 45].
# Esto incluye la hora, el nivel de importancia (INFO, WARNING, ERROR) y el mensaje técnico.
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Creamos un objeto 'logger' principal para que todo el kit pueda emitir reportes estructurados[cite: 45].
logger = logging.getLogger("KitISO")

# Registramos un mensaje inicial para confirmar que el núcleo operativo se ha cargado con éxito.
logger.info("El Kit de Cumplimiento ISO ha sido inicializado correctamente.")

# Este archivo asegura que Antigravity reconozca la carpeta 'kit_iso' como un paquete de habilidades[cite: 40, 154].