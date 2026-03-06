# Importamos el módulo nativo de logging para rastrear la actividad del kit (ISO 27001)[cite: 43, 59].
import logging
# Importamos submódulos para acceso fácil (simplifica imports, práctica estándar).
from .seguridad import ToolkitSeguridad
from .usabilidad import HerramientasUsabilidad
from .base_datos import BaseDatosSegura
# ... (agrega más según avances).
# Definimos la versión actual de nuestro toolkit de cumplimiento normativo[cite: 155].
__version__ = "0.1.0"

# NullHandler en lugar de basicConfig.
# Las librerías NUNCA deben llamar basicConfig — eso es responsabilidad
# de la aplicación que las usa. NullHandler silencia los logs por defecto
# pero permite que el host los active si quiere (Python logging best practice).
logging.getLogger("KitISO").addHandler(logging.NullHandler())


# Creamos un objeto 'logger' principal para que todo el kit pueda emitir reportes estructurados[cite: 45].
logger = logging.getLogger("KitISO")

# Registramos un mensaje inicial para confirmar que el núcleo operativo se ha cargado con éxito.
logger.info("El Kit de Cumplimiento ISO ha sido inicializado correctamente.")

# Este archivo asegura que Antigravity reconozca la carpeta 'kit_iso' como un paquete de habilidades[cite: 40, 154].