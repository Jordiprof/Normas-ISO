"""BaseDatosSegura — acceso a PostgreSQL/MySQL con parametrización obligatoria y datos encriptados (ISO 27001)."""

import logging
from typing import Any

# Los drivers son opcionales (extra `kit-iso[bd]`): importar el kit no debe exigirlos.
# ImportError cubre también "DLL load failed" en Windows con políticas de control de aplicaciones.
try:
    import psycopg2
except ImportError:  # pragma: no cover — depende del entorno
    psycopg2 = None
try:
    import mysql.connector
except ImportError:  # pragma: no cover — depende del entorno
    mysql = None  # type: ignore[assignment]

# Import relativo: evita la dependencia circular con kit_iso/__init__.py.
from ..seguridad import ToolkitSeguridad

logger = logging.getLogger(__name__)

# Whitelist por defecto de identificadores SQL (ISO 27001 A.14.2).
# Los identificadores no se pueden parametrizar, así que se validan contra esta lista.
TABLAS_PERMITIDAS = {"usuarios", "registros", "auditorias", "documentos"}
COLUMNAS_PERMITIDAS = {"datos", "contenido", "valor", "texto"}

_MSG_DRIVER = (
    "El driver '{driver}' no está disponible. Instala el extra de base de datos: "
    'pip install "kit-iso[bd]"'
)


class BaseDatosSegura:
    """Conexión segura a BD. Uso recomendado como context manager:

        with BaseDatosSegura("postgres", host, usuario, password, nombre_bd) as db:
            db.almacenar_encriptado("registros", "contenido", "dato sensible")

    Lecturas → ``consulta_segura`` · Escrituras → ``ejecutar_segura`` (hace commit).
    """

    def __init__(
        self,
        tipo_bd: str,
        host: str,
        usuario: str,
        password: str,
        nombre_bd: str,
        *,
        tablas_permitidas: set[str] | None = None,
        columnas_permitidas: set[str] | None = None,
        seguridad: ToolkitSeguridad | None = None,
    ):
        self.tipo_bd = tipo_bd
        self.tablas_permitidas = set(tablas_permitidas) if tablas_permitidas else TABLAS_PERMITIDAS
        self.columnas_permitidas = (
            set(columnas_permitidas) if columnas_permitidas else COLUMNAS_PERMITIDAS
        )
        # Se puede inyectar un ToolkitSeguridad ya configurado (p. ej. con clave explícita).
        self.seguridad = seguridad or ToolkitSeguridad()
        # Any: el tipo de conexión difiere entre psycopg2 y mysql.connector (dos drivers).
        self.conexion: Any = None
        self._conectar(host, usuario, password, nombre_bd)

    def _conectar(self, host, usuario, password, nombre_bd):
        if self.tipo_bd == "postgres":
            if psycopg2 is None:
                raise ImportError(_MSG_DRIVER.format(driver="psycopg2"))
            self.conexion = psycopg2.connect(
                host=host, user=usuario, password=password, dbname=nombre_bd
            )
        elif self.tipo_bd == "mysql":
            if mysql is None:
                raise ImportError(_MSG_DRIVER.format(driver="mysql.connector"))
            self.conexion = mysql.connector.connect(
                host=host, user=usuario, password=password, database=nombre_bd
            )
        else:
            raise ValueError(
                f"Tipo de base de datos no soportado: '{self.tipo_bd}' (usa 'postgres' o 'mysql')."
            )

    # ── Context manager: garantiza que la conexión se cierra ──────────────
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.cerrar()

    def cerrar(self):
        if self.conexion is not None:
            self.conexion.close()
            self.conexion = None

    # ── Operaciones ────────────────────────────────────────────────────────
    def consulta_segura(self, query: str, parametros: tuple):
        """SELECT parametrizado. Para escrituras usa ``ejecutar_segura``."""
        cursor = self.conexion.cursor()
        try:
            cursor.execute(query, parametros)
            return cursor.fetchall()
        finally:
            cursor.close()

    def ejecutar_segura(self, query: str, parametros: tuple) -> int:
        """INSERT/UPDATE/DELETE parametrizado con commit (rollback si falla).

        Devuelve el número de filas afectadas.
        """
        cursor = self.conexion.cursor()
        try:
            cursor.execute(query, parametros)
            self.conexion.commit()
            return cursor.rowcount
        except Exception:
            self.conexion.rollback()
            raise
        finally:
            cursor.close()

    def _validar_identificadores(self, tabla: str, columna: str):
        """Valida tabla y columna contra la whitelist (ISO 27001 A.14.2)."""
        if tabla not in self.tablas_permitidas:
            logger.error("Intento de acceso a tabla no permitida: '%s'", tabla)
            raise ValueError(
                f"Tabla '{tabla}' no permitida. Tablas válidas: {sorted(self.tablas_permitidas)}"
            )
        if columna not in self.columnas_permitidas:
            logger.error("Intento de acceso a columna no permitida: '%s'", columna)
            raise ValueError(
                f"Columna '{columna}' no permitida. Columnas válidas: {sorted(self.columnas_permitidas)}"
            )

    def almacenar_encriptado(self, tabla: str, columna: str, datos: str):
        """Encripta y persiste un dato (ISO 27001 A.10.1)."""
        self._validar_identificadores(tabla, columna)
        encriptado = self.seguridad.encriptar_datos(datos)
        # Los identificadores no se pueden parametrizar en SQL: van validados contra
        # la whitelist justo arriba; el valor sí va parametrizado.
        query = f"INSERT INTO {tabla} ({columna}) VALUES (%s)"  # nosec B608
        self.ejecutar_segura(query, (encriptado,))
        logger.info("Datos encriptados almacenados en %s.%s", tabla, columna)
