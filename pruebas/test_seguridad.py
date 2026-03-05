# Importamos pytest para ejecutar tests automatizados (calidad ISO 25010).
import pytest
# Importamos el módulo de usabilidad.
from kit_iso.usabilidad import HerramientasUsabilidad

# Instanciamos la clase para los tests.
hu = HerramientasUsabilidad()

# Test para validar input de usuario.
def test_validar_input():
    # Probamos un input válido.
    assert hu.validar_input_usuario("Entrada válida") == "Entrada válida"
    # Probamos un input inválido (debe fallar con error).
    with pytest.raises(ValueError):
        hu.validar_input_usuario("Entrada; con; ataque;")  # Simula inyección, pero se sanitiza.

# Test para generar feedback.
def test_generar_feedback():
    # Probamos feedback de éxito.
    assert hu.generar_feedback(True) == "Operación completada con éxito."
    # Probamos feedback de fallo.
    assert "Ocurrió un error" in hu.generar_feedback(False)