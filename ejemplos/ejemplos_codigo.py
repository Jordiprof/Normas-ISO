# Ejemplos de código para el kit ISO
# Importamos FastAPI para demo full-stack.
from fastapi import FastAPI
# Importamos módulos ISO.
from kit_iso.base_datos import BaseDatosSegura
from kit_iso.usabilidad import HerramientasUsabilidad

app = FastAPI()  # App simple.

@app.get("/demo")
def demo(input: str):
    # Validamos usabilidad.
    hu = HerramientasUsabilidad()
    input_valido = hu.validar_input_usuario(input)
    # Conectamos DB segura (usa tus creds).
    db = BaseDatosSegura('postgres', 'localhost', 'user', 'pass', 'db')
    db.almacenar_encriptado('tabla', 'columna', input_valido)
    return {"mensaje": hu.generar_feedback(True)}

# Ejecuta: uvicorn ejemplos.ejemplos_codigo:app --reload