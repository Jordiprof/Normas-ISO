"""ToolkitSeguridad — encriptación simétrica Fernet con clave gestionada fuera del código (ISO 27001)."""

import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Variable de entorno donde vive la clave de encriptación.
VAR_CLAVE = "KIT_ISO_CLAVE"


class ToolkitSeguridad:
    """Encripta y desencripta datos con una clave persistente.

    La clave se toma del argumento ``clave`` o de la variable de entorno
    ``KIT_ISO_CLAVE``. Nunca se genera una clave implícita: si cada proceso
    generara la suya, todo lo encriptado sería irrecuperable tras un reinicio.
    """

    def __init__(self, clave: bytes | str | None = None):
        clave = clave or os.getenv(VAR_CLAVE)
        if not clave:
            raise ValueError(
                f"No hay clave de encriptación. Define la variable de entorno {VAR_CLAVE} "
                "(genera una con ToolkitSeguridad.generar_clave()) o pasa clave= al constructor. "
                "No se genera una clave implícita: los datos encriptados serían irrecuperables."
            )
        if isinstance(clave, str):
            clave = clave.encode()
        self._fernet = Fernet(clave)  # valida el formato de la clave al construir
        logger.info("Toolkit de Seguridad inicializado.")

    @staticmethod
    def generar_clave() -> bytes:
        """Genera una clave Fernet nueva.

        Guárdala en tu gestor de secretos o en la variable de entorno
        KIT_ISO_CLAVE. Si la pierdes, los datos encriptados con ella son
        irrecuperables; si se expone, rota la clave y re-encripta.
        """
        return Fernet.generate_key()

    def encriptar_datos(self, datos: str) -> bytes:
        token = self._fernet.encrypt(datos.encode())
        logger.info("Datos encriptados.")  # nunca se loguea el dato en claro
        return token

    def desencriptar_datos(self, encriptados: bytes) -> str:
        return self._fernet.decrypt(encriptados).decode()
