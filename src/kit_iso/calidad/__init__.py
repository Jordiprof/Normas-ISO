import pytest
import time

class HerramientasCalidad:
    def medir_performance(self, func, *args):
        # Mide tiempo (eficiencia 25010).
        inicio = time.time()
        result = func(*args)
        duracion = time.time() - inicio
        return result, duracion
    
    def run_tests(self):
        # Ejecuta pytest (calidad).
        pytest.main(['pruebas/'])