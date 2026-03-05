# Importamos logging para registrar interacciones de usuario de forma auditada (integra con seguridad).
import logging
# Importamos re para validaciones de patrones en inputs (usabilidad básica).
import re
# Importamos el módulo de seguridad para integración obligatoria (ISO 27001 en cada módulo).
from kit_iso.seguridad import HerramientasSeguridad

# Configuramos el logger específico para usabilidad (para trazabilidad).
logger = logging.getLogger(__name__)
# Instanciamos herramientas de seguridad (empezamos por seguridad, como pediste).
seguridad = HerramientasSeguridad()

# Definimos la clase principal para herramientas de usabilidad (ISO 9241).
class HerramientasUsabilidad:
    # Método inicializador de la clase (constructor).
    def __init__(self):
        # Inicializamos un diccionario vacío para almacenar métricas de usabilidad (efectividad, eficiencia, satisfacción).
        self.metricas = {}  # Cumple con ISO 9241-11: definición de usabilidad.
    
    # Método para validar inputs de usuario (asegura interacción ergonómica y segura).
    def validar_input_usuario(self, input_str: str, longitud_max: int = 100):
        # Primero, aplicamos validación segura del módulo de seguridad (integra ISO 27001).
        input_seguro = seguridad.validar_input_seguro(input_str)  # Asume método en seguridad/validador.py; si no, adáptalo desde validador.py.
        # Verificamos la longitud para evitar sobrecargas (usabilidad: eficiencia).
        if len(input_seguro) > longitud_max:
            # Registramos el evento en logs para auditoría.
            logger.warning(f"Input excede longitud máxima: {len(input_seguro)} > {longitud_max}")
            # Lanzamos un error amigable al usuario (feedback claro, ISO 9241-210).
            raise ValueError("El input es demasiado largo. Por favor, reduce su tamaño.")
        # Validamos patrón básico (solo caracteres permitidos, para simplicidad y seguridad).
        if not re.match(r'^[a-zA-Z0-9\s]+$', input_seguro):
            # Registramos el fallo en logs.
            logger.warning("Input contiene caracteres no permitidos.")
            # Error amigable para el usuario.
            raise ValueError("Input inválido: solo se permiten letras, números y espacios.")
        # Si todo pasa, devolvemos el input validado.
        return input_seguro
    
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
        self.metricas['eficiencia'] = duracion
        # Registramos el resultado en logs.
        logger.info(f"La interacción tomó {duracion} segundos.")
        # Devolvemos el resultado de la función original.
        return resultado
    
    # Método para generar feedback al usuario (cumple diseño centrado en humano).
    def generar_feedback(self, exito: bool, mensaje_exito: str = "Operación completada con éxito.", mensaje_fallo: str = "Ocurrió un error."):
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