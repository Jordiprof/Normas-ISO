# Importamos la librería para conectarnos a bases de datos PostgreSQL.
import psycopg2
# Importamos la librería para conectarnos a bases de datos MySQL.
import mysql.connector
# Importamos nuestro propio toolkit de seguridad creado en el paso anterior.
from kit_iso.seguridad import ToolkitSeguridad
# Importamos el logger para registrar eventos.
from kit_iso import logger

# Tablas y columnas permitidas (whitelist de seguridad ISO 27001 A.14.2).
TABLAS_PERMITIDAS = {"usuarios", "registros", "auditorias", "documentos"}
COLUMNAS_PERMITIDAS = {"datos", "contenido", "valor", "texto"}

# Definimos la clase para manejar conexiones seguras a bases de datos.
class BaseDatosSegura:
    # Método inicializador que recibe los credenciales de la base de datos.
    def __init__(self, tipo_bd: str, host: str, usuario: str, password: str, nombre_bd: str):
        # Guardamos el tipo de base de datos (ej: 'postgres' o 'mysql').
        self.tipo_bd = tipo_bd
        # Iniciamos la variable de conexión vacía (None).
        self.conexion = None
        # Instanciamos nuestras herramientas de encriptación.
        self.seguridad = ToolkitSeguridad()
        # Llamamos al método interno para establecer la conexión real.
        self.conectar(host, usuario, password, nombre_bd)

    # Método interno para abrir la conexión.
    def conectar(self, host, usuario, password, nombre_bd):
        # Si el tipo indicado es postgres...
        if self.tipo_bd == 'postgres':
            # ...usamos psycopg2 para establecer la conexión.
            self.conexion = psycopg2.connect(host=host, user=usuario, password=password, dbname=nombre_bd)
        # Si el tipo indicado es mysql...
        elif self.tipo_bd == 'mysql':
            # ...usamos mysql.connector para conectar.
            self.conexion = mysql.connector.connect(host=host, user=usuario, password=password, database=nombre_bd)
        # Si no es ninguno de los dos...
        else:
            # ...lanzamos un error para detener la ejecución.
            raise ValueError("Tipo de base de datos no ha soportado por el toolkit.")

    # Método para ejecutar consultas seguras (Evita Inyecciones SQL).
    def consulta_segura(self, query: str, parametros: tuple):
        # Creamos un 'cursor' que es el objeto que ejecuta comandos en la BD.
        cursor = self.conexion.cursor()
        # Ejecutamos la query pasando los parámetros de forma separada (parametrización).
        cursor.execute(query, parametros)
        # Obtenemos todos los resultados de la consulta.
        resultado = cursor.fetchall()
        # Cerramos el cursor para liberar recursos de memoria.
        cursor.close()
        # Devolvemos los datos obtenidos al usuario.
        return resultado

    #  Método privado que valida tabla y columna contra la whitelist.
    def _validar_identificadores(self, tabla: str, columna: str):
        """Valida que tabla y columna estén en la whitelist (ISO 27001 A.14.2)."""
        if tabla not in TABLAS_PERMITIDAS:
            logger.error(f"Intento de acceso a tabla no permitida: '{tabla}'")
            raise ValueError(f"Tabla '{tabla}' no permitida. Tablas válidas: {TABLAS_PERMITIDAS}")
        if columna not in COLUMNAS_PERMITIDAS:
            logger.error(f"Intento de acceso a columna no permitida: '{columna}'")
            raise ValueError(f"Columna '{columna}' no permitida. Columnas válidas: {COLUMNAS_PERMITIDAS}")
        
    # Método para almacenar datos encriptados (renombrado a español, con mejoras).
    def almacenar_encriptado(self, tabla: str, columna: str, datos: str):
        # Documentación: Almacena datos encriptados (A.10.1 de ISO 27001).
        """Almacena datos encriptados de forma segura en la BD."""
        # Intentamos la operación con manejo de errores (mejora: robustez).
        try:
            # Encriptamos los datos usando el módulo de seguridad.
            self._validar_identificadores(tabla, columna)
            encriptado = self.seguridad.encriptar_datos(datos)  # Asume método renombrado en seguridad.
            # Creamos la query SQL parametrizada (segura contra inyecciones).
            query = f"INSERT INTO {tabla} ({columna}) VALUES (%s)"
            # Ejecutamos la query segura.
            self.consulta_segura(query, (encriptado,))
            # Registramos éxito.
            logger.info(f"Datos encriptados almacenados en {tabla}.{columna}")
        except ValueError:
            raise    
        # Si hay error...
        except Exception as e:
            # Registramos el error para auditoría.
            logger.error(f"Error al almacenar: {str(e)}")
            # Lanzamos excepción amigable (integra usabilidad: feedback claro).
            raise ValueError(f"No se pudo almacenar: {str(e)}. Verifica conexión.")