"""HerramientasCalidad — métricas ISO 25010: rendimiento, complejidad y cobertura."""

import time

import pytest

try:
    from radon.complexity import cc_rank, cc_visit

    _radon_disponible = True
except ImportError:
    _radon_disponible = False

try:
    import coverage as coverage_lib

    _coverage_disponible = True
except ImportError:
    _coverage_disponible = False


class HerramientasCalidad:
    """Métricas de calidad ISO 25010: rendimiento, complejidad ciclomática y cobertura.

    Parámetros configurables:

        umbral_complejidad — complejidad de McCabe máxima aceptable por función (defecto: 10).
            A-C (1-10): mantenible; D-F (11+): refactorizar.
        umbral_cobertura — porcentaje mínimo de cobertura de tests (defecto: 80.0).

    Ejemplo::

        hc = HerramientasCalidad(umbral_complejidad=8, umbral_cobertura=90.0)
        resultado, duracion = hc.medir_performance(mi_funcion, arg1)
        informe = hc.medir_complejidad(open("src/modulo.py").read())
        cobertura = hc.medir_cobertura("src/mi_paquete", "pruebas/")

    Requiere: ``pip install radon`` (complejidad) · ``pip install coverage`` (cobertura).
    """

    def __init__(
        self,
        umbral_complejidad: int = 10,
        umbral_cobertura: float = 80.0,
    ):
        self.umbral_complejidad = umbral_complejidad
        self.umbral_cobertura = umbral_cobertura

    def medir_performance(self, func, *args):
        """Mide tiempo de ejecución (ISO 25010 — Eficiencia de rendimiento).

        Returns:
            (resultado_de_func, duracion_en_segundos)
        """
        inicio = time.time()
        resultado = func(*args)
        duracion = time.time() - inicio
        return resultado, duracion

    def medir_complejidad(self, codigo_fuente: str) -> dict:
        """Calcula complejidad ciclomática de McCabe por función/método (ISO 25010 — Mantenibilidad).

        Requiere ``radon`` (``pip install radon``).

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "ISO 25010 — Mantenibilidad",
                "umbral": 10,
                "bloques": [{"nombre": "...", "complejidad": 3, "rango": "A", "linea": 5}, ...],
                "sobre_umbral": ["func_compleja (línea 42): complejidad 15 > 10"]
            }

        Rangos McCabe: A (1-5) · B (6-10) · C (11-15) · D (16-20) · E (21-25) · F (26+)
        """
        if not _radon_disponible:
            raise ImportError("radon no está instalado — instálalo con: pip install radon")

        bloques = cc_visit(codigo_fuente)
        resultados = []
        sobre_umbral = []

        for bloque in bloques:
            rango = cc_rank(bloque.complexity)
            resultados.append(
                {
                    "nombre": bloque.name,
                    "complejidad": bloque.complexity,
                    "rango": rango,
                    "linea": bloque.lineno,
                }
            )
            if bloque.complexity > self.umbral_complejidad:
                sobre_umbral.append(
                    f"{bloque.name} (línea {bloque.lineno}): "
                    f"complejidad {bloque.complexity} > {self.umbral_complejidad}"
                )

        return {
            "estado": "ok" if not sobre_umbral else "fallo",
            "norma": "ISO 25010 — Mantenibilidad",
            "umbral": self.umbral_complejidad,
            "bloques": resultados,
            "sobre_umbral": sobre_umbral,
        }

    def medir_cobertura(self, directorio_fuente: str, directorio_pruebas: str) -> dict:
        """Ejecuta pytest con coverage y devuelve el porcentaje de cobertura (ISO 25010 — Fiabilidad).

        Requiere ``coverage`` (``pip install coverage``).

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "ISO 25010 — Fiabilidad",
                "cobertura": 85.4,
                "umbral": 80.0,
                "tests_exitosos": True
            }
        """
        if not _coverage_disponible:
            raise ImportError("coverage no está instalado — instálalo con: pip install coverage")

        cov = coverage_lib.Coverage(source=[directorio_fuente])
        cov.start()

        exit_code = pytest.main([directorio_pruebas, "-q", "--tb=no"])

        cov.stop()
        cov.save()

        # report() imprime a stdout y devuelve el total como float.
        porcentaje = cov.report(show_missing=False)

        return {
            "estado": "ok" if porcentaje >= self.umbral_cobertura else "fallo",
            "norma": "ISO 25010 — Fiabilidad",
            "cobertura": round(porcentaje, 2),
            "umbral": self.umbral_cobertura,
            "tests_exitosos": exit_code == 0,
        }

    def run_tests(self):
        """Ejecuta pytest sobre el directorio de pruebas estándar."""
        pytest.main(["pruebas/"])
