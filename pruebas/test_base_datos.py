"""Tests de BaseDatosSegura con la conexión mockeada (el límite del sistema es la BD)."""

from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from kit_iso.base_datos import BaseDatosSegura
from kit_iso.seguridad import ToolkitSeguridad


def _toolkit():
    return ToolkitSeguridad(clave=Fernet.generate_key())


def _db_con_mock(**kwargs):
    # Se parchea el módulo entero: en entornos sin el driver instalado es None.
    with patch("kit_iso.base_datos.psycopg2") as driver:
        conexion = MagicMock()
        driver.connect.return_value = conexion
        db = BaseDatosSegura("postgres", "h", "u", "p", "bd", seguridad=_toolkit(), **kwargs)
    return db, conexion


def test_almacenar_hace_commit():
    # Bug original: el INSERT no hacía commit → datos perdidos en silencio al cerrar.
    db, conexion = _db_con_mock()
    db.almacenar_encriptado("registros", "contenido", "dato")
    conexion.commit.assert_called_once()


def test_almacenar_no_hace_fetchall():
    # Bug original: fetchall() sobre un INSERT lanza ProgrammingError en psycopg2.
    db, conexion = _db_con_mock()
    db.almacenar_encriptado("registros", "contenido", "dato")
    conexion.cursor.return_value.fetchall.assert_not_called()


def test_error_en_escritura_hace_rollback():
    db, conexion = _db_con_mock()
    conexion.cursor.return_value.execute.side_effect = RuntimeError("fallo simulado")
    with pytest.raises(RuntimeError):
        db.ejecutar_segura("INSERT INTO registros (contenido) VALUES (%s)", ("x",))
    conexion.rollback.assert_called_once()


def test_tabla_fuera_de_whitelist_rechazada():
    db, _ = _db_con_mock()
    with pytest.raises(ValueError, match="no permitida"):
        db.almacenar_encriptado("usuarios; DROP TABLE x;--", "contenido", "dato")


def test_columna_fuera_de_whitelist_rechazada():
    db, _ = _db_con_mock()
    with pytest.raises(ValueError, match="no permitida"):
        db.almacenar_encriptado("registros", "columna_inventada", "dato")


def test_whitelist_configurable():
    db, conexion = _db_con_mock(tablas_permitidas={"eventos"}, columnas_permitidas={"payload"})
    db.almacenar_encriptado("eventos", "payload", "dato")
    conexion.commit.assert_called_once()


def test_tipo_bd_invalido_falla_claro():
    with pytest.raises(ValueError, match="no soportado"):
        BaseDatosSegura("oracle", "h", "u", "p", "bd", seguridad=_toolkit())


def test_sin_driver_falla_con_instruccion_de_instalacion():
    with (
        patch("kit_iso.base_datos.psycopg2", None),
        pytest.raises(ImportError, match=r"kit-iso\[bd\]"),
    ):
        BaseDatosSegura("postgres", "h", "u", "p", "bd", seguridad=_toolkit())


def test_context_manager_cierra_conexion():
    with patch("kit_iso.base_datos.psycopg2") as driver:
        conexion = MagicMock()
        driver.connect.return_value = conexion
        with BaseDatosSegura("postgres", "h", "u", "p", "bd", seguridad=_toolkit()):
            pass
    conexion.close.assert_called_once()
