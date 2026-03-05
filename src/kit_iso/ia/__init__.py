# Importamos usabilidad para validar interacciones en flujos de IA.
from kit_iso.usabilidad import HerramientasUsabilidad

usabilidad = HerramientasUsabilidad()

# Función para chain segura con usabilidad.
def chain_ia_segura(input_datos: str):
    # Validamos input con usabilidad (integra seguridad interna).
    input_valido = usabilidad.validar_input_usuario(input_datos)
    # ... (resto de tu chain con LangGraph)
    # Medimos eficiencia.
    return usabilidad.medir_eficiencia_interaccion(tu_funcion_ia, input_valido)