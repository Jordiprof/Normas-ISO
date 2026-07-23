# Importamos logging para registrar interacciones de usuario de forma auditada (ISO 9001 / 7.5.3.1).
import logging

# Importamos re para validaciones de patrones en inputs (usabilidad básica, ISO 9241).
import re

# Import RELATIVO para evitar dependencia circular con kit_iso/__init__.py (ISO 27001 A.14.2.5).
# ValidadorSeguridad detecta patrones peligrosos (api_key, password, secret) en cualquier string.
from ..seguridad.validador import ValidadorSeguridad

# Configuramos el logger específico para usabilidad (trazabilidad ISO 9001).
logger = logging.getLogger(__name__)
# Instancia de ValidadorSeguridad a nivel de módulo (reutilizable, sin estado mutable).
_validador_seguridad = ValidadorSeguridad()


# Definimos la clase principal para herramientas de usabilidad (ISO 9241).
class HerramientasUsabilidad:
    # Método inicializador de la clase (constructor).
    def __init__(self):
        # Inicializamos un diccionario vacío para almacenar métricas de usabilidad
        # (efectividad, eficiencia, satisfacción) — ISO 9241-11.
        self.metricas = {}

    # Método para validar inputs de usuario (ergonómico + seguro).
    def validar_input_usuario(self, input_str: str, longitud_max: int = 100):
        # ── Paso 1: Longitud (usabilidad — eficiencia, ISO 9241) ──────────────
        if len(input_str) > longitud_max:
            logger.warning(f"Input excede longitud máxima: {len(input_str)} > {longitud_max}")
            raise ValueError("El input es demasiado largo. Por favor, reduce su tamaño.")

        # ── Paso 2: Patrón de caracteres permitidos (ISO 9241-210) ───────────
        if not re.match(r"^[a-zA-Z0-9\s]+$", input_str):
            logger.warning("Input contiene caracteres no permitidos.")
            raise ValueError("Input inválido: solo se permiten letras, números y espacios.")

        # ── Paso 3: Escaneo de secretos expuestos (ISO 27001 A.10.1) ─────────
        # ValidadorSeguridad detecta credenciales embebidas (contraseñas, claves API)
        # en el propio input — previene que se envíen credenciales por error.
        hallazgos = _validador_seguridad.analizar_codigo(input_str)
        if hallazgos:
            logger.warning(
                f"Input rechazado — contiene patrones de seguridad prohibidos: {hallazgos}"
            )
            raise ValueError(
                "Input rechazado: contiene patrones de seguridad prohibidos (ISO 27001 A.10.1 — ZERO-SECRETS)."
            )

        # Si los 3 pasos pasan, el input es válido y seguro.
        return input_str

    # Método para medir la eficiencia de una interacción (tiempo de ejecución).
    def medir_eficiencia_interaccion(self, funcion, *args, **kwargs):
        # Importamos time dentro del método para no cargar módulos innecesarios al inicio.
        import time

        # Registramos el inicio de la medición (auditoría integrada).
        logger.info("Iniciando medición de eficiencia de interacción.")
        # Capturamos el tiempo de inicio.
        inicio = time.time()
        # Ejecutamos la función proporcionada (ej. un flujo de app o IA).
        resultado = funcion(*args, **kwargs)
        # Capturamos el tiempo de fin.
        fin = time.time()
        # Calculamos la duración total.
        duracion = fin - inicio
        # Almacenamos la métrica en el diccionario.
        self.metricas["eficiencia"] = duracion
        # Registramos el resultado en logs.
        logger.info(f"La interacción tomó {duracion} segundos.")
        # Devolvemos el resultado de la función original.
        return resultado

    # Método para generar feedback al usuario (cumple diseño centrado en humano).
    def generar_feedback(
        self,
        exito: bool,
        mensaje_exito: str = "Operación completada con éxito.",
        mensaje_fallo: str = "Ocurrió un error.",
    ):
        # Verificamos si fue un éxito.
        if exito:
            # Registramos el feedback positivo.
            logger.info("Generado feedback positivo.")
            # Devolvemos el mensaje de éxito.
            return mensaje_exito
        else:
            # Registramos el feedback negativo.
            logger.warning("Generado feedback negativo.")
            # Devolvemos el mensaje de fallo amigable.
            return mensaje_fallo + " Intenta nuevamente o contacta soporte."
