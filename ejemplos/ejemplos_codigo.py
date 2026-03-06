# ============================================================
# ejemplos_codigo.py
# Demostración de integración completa del kit-cumplimiento-iso
# Todas las credenciales se cargan desde variables de entorno
# ============================================================

import os
# Cargamos las variables de entorno desde el archivo .env
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
# Importamos los módulos del kit
from kit_iso.base_datos import BaseDatosSegura
from kit_iso.usabilidad import HerramientasUsabilidad
from kit_iso.accesibilidad import HerramientasAccesibilidad
from kit_iso.seguridad import ToolkitSeguridad
from kit_iso.nucleo import logger

# ✅ Cargamos el .env al arrancar — nunca credenciales en el código
load_dotenv()

# ✅ Leemos las credenciales desde el entorno, con validación al inicio
def cargar_config_bd() -> dict:
    """
    Carga y valida la configuración de BD desde variables de entorno.
    Lanza un error claro si falta alguna variable obligatoria.
    """
    variables_requeridas = ["DB_TIPO", "DB_HOST", "DB_USUARIO", "DB_PASSWORD", "DB_NOMBRE"]
    config = {}
    variables_faltantes = []

    for var in variables_requeridas:
        valor = os.getenv(var)
        if not valor:
            variables_faltantes.append(var)
        else:
            config[var.lower()] = valor

    if variables_faltantes:
        raise EnvironmentError(
            f"Faltan variables de entorno obligatorias: {variables_faltantes}\n"
            f"Copia .env.example a .env y rellena los valores."
        )

    return config

# ============================================================
# Inicialización de la app y servicios
# ============================================================

app = FastAPI(
    title="Kit Cumplimiento ISO — Demo",
    description="API de ejemplo que integra todos los módulos del kit",
    version="0.1.0"
)

# Instanciamos las herramientas del kit
hu = HerramientasUsabilidad()
ha = HerramientasAccesibilidad()
seg = ToolkitSeguridad()

# ============================================================
# Endpoints de demostración
# ============================================================

@app.get("/demo/almacenar")
def demo_almacenar(dato: str):
    """
    Flujo completo:
    1. Valida el input del usuario (usabilidad)
    2. Conecta a la BD con credenciales desde .env (seguridad)
    3. Almacena el dato encriptado (ISO 27001 A.10.1)
    4. Devuelve feedback estructurado (usabilidad)
    """
    try:
        # Paso 1 — Validamos el input
        input_valido = hu.validar_input_usuario(dato)

        # Paso 2 — Cargamos config desde entorno, nunca hardcodeada
        config = cargar_config_bd()

        # Paso 3 — Conectamos y almacenamos de forma segura
        db = BaseDatosSegura(
            tipo_bd=config["db_tipo"],
            host=config["db_host"],
            usuario=config["db_usuario"],
            password=config["db_password"],
            nombre_bd=config["db_nombre"]
        )
        db.almacenar_encriptado("registros", "contenido", input_valido)

        # Paso 4 — Feedback estructurado al usuario
        logger.info(f"Dato almacenado correctamente en la BD.")
        return {
            "estado": "ok",
            "mensaje": hu.generar_feedback(True)
        }

    except EnvironmentError as e:
        # Error de configuración — problema del servidor, no del usuario
        logger.error(f"Error de configuración: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except ValueError as e:
        # Error de validación — problema del input del usuario
        logger.warning(f"Input rechazado: {str(e)}")
        raise HTTPException(status_code=400, detail=hu.generar_feedback(False))


@app.get("/demo/accesibilidad")
def demo_accesibilidad(html: str):
    """
    Valida un fragmento HTML contra WCAG 2.1.
    Devuelve un informe estructurado con los hallazgos.
    """
    resultado = ha.validar_html_accesible(html)
    
    if resultado["estado"] == "fallo":
        logger.warning(f"Fallos de accesibilidad detectados: {resultado['hallazgos']}")
        raise HTTPException(status_code=422, detail=resultado)
    
    return resultado


@app.get("/demo/encriptar")
def demo_encriptar(dato: str):
    """
    Muestra el ciclo completo de encriptación/desencriptación (ISO 27001).
    Solo para demostración — en producción nunca expongas este endpoint.
    """
    input_valido = hu.validar_input_usuario(dato)
    encriptado = seg.encriptar_datos(input_valido)
    desencriptado = seg.desencriptar_datos(encriptado)

    return {
        "original": input_valido,
        "encriptado": encriptado.decode(),
        "desencriptado_correctamente": desencriptado == input_valido
    }


# ============================================================
# Arranque
# Ejecuta: uvicorn ejemplos.ejemplos_codigo:app --reload
# ============================================================