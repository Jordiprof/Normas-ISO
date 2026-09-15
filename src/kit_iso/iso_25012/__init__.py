"""ISO/IEC 25012 — Calidad de datos: completitud, exactitud y consistencia."""

import re


def _errores_de_valor(valor, reglas: dict) -> list[str]:
    """Aplica las reglas de exactitud (tipo, min, max, patron) a un valor no nulo."""
    tipo = reglas.get("tipo")
    if tipo and not isinstance(valor, tipo):
        return [f"tipo esperado {tipo.__name__}, recibido {type(valor).__name__}"]
    errores = []
    if "min" in reglas and valor < reglas["min"]:
        errores.append(f"valor {valor} < mínimo {reglas['min']}")
    if "max" in reglas and valor > reglas["max"]:
        errores.append(f"valor {valor} > máximo {reglas['max']}")
    if "patron" in reglas and isinstance(valor, str) and not re.match(reglas["patron"], valor):
        errores.append(f"valor '{valor}' no coincide con el patrón")
    return errores


class ValidadorCalidadDatos:
    """Valida la calidad de datasets o colecciones de registros según ISO 25012.

    Características evaluadas:
        - **Completitud**: campos requeridos presentes y no vacíos.
        - **Exactitud**: tipos, rangos y patrones correctos.
        - **Consistencia**: reglas de negocio entre campos.

    Ejemplo::

        val = ValidadorCalidadDatos()

        registros = [
            {"nombre": "Ana", "edad": 30, "email": "ana@e.com"},
            {"nombre": "", "edad": 200, "email": "no-valido"},
        ]

        r_comp = val.validar_completitud(registros, ["nombre", "email"])
        r_exact = val.validar_exactitud(registros, {
            "edad": {"tipo": int, "min": 0, "max": 150},
            "email": {"tipo": str, "patron": r'^[^@]+@[^@]+\\.[^@]+$'},
        })
        r_cons = val.validar_consistencia(registros, [
            {"descripcion": "edad >= 18 si tiene email",
             "fn": lambda r: r.get("edad", 0) >= 18 or not r.get("email")},
        ])
    """

    def validar_completitud(
        self,
        registros: list[dict],
        campos_requeridos: list[str],
    ) -> dict:
        """Detecta registros con campos requeridos ausentes o vacíos.

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "ISO 25012 — Completitud",
                "total_registros": 100,
                "registros_incompletos": 3,
                "porcentaje_completitud": 97.0,
                "detalle": [{"indice": 5, "campos_faltantes": ["email"]}]
            }
        """
        incompletos = []
        for i, registro in enumerate(registros):
            faltantes = [
                c for c in campos_requeridos if registro.get(c) is None or registro.get(c) == ""
            ]
            if faltantes:
                incompletos.append({"indice": i, "campos_faltantes": faltantes})

        total = len(registros)
        completitud = ((total - len(incompletos)) / total * 100) if total > 0 else 100.0

        return {
            "estado": "ok" if not incompletos else "fallo",
            "norma": "ISO 25012 — Completitud",
            "total_registros": total,
            "registros_incompletos": len(incompletos),
            "porcentaje_completitud": round(completitud, 2),
            "detalle": incompletos,
        }

    def validar_exactitud(
        self,
        registros: list[dict],
        esquema: dict[str, dict],
    ) -> dict:
        """Valida tipos, rangos y patrones según un esquema.

        Esquema de ejemplo::

            {
                "edad":   {"tipo": int, "min": 0, "max": 150},
                "email":  {"tipo": str, "patron": r'^[^@]+@[^@]+$'},
                "activo": {"tipo": bool},
            }

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "ISO 25012 — Exactitud",
                "total_registros": 100,
                "registros_con_errores": 2,
                "porcentaje_exactitud": 98.0,
                "detalle": [{"indice": 1, "campo": "edad", "error": "valor 200 > máximo 150"}]
            }
        """
        errores = []
        for i, registro in enumerate(registros):
            for campo, reglas in esquema.items():
                valor = registro.get(campo)
                if valor is None:
                    continue  # la completitud lo valida aparte
                errores += [
                    {"indice": i, "campo": campo, "error": e}
                    for e in _errores_de_valor(valor, reglas)
                ]

        total = len(registros)
        indices_error = {e["indice"] for e in errores}
        exactitud = ((total - len(indices_error)) / total * 100) if total > 0 else 100.0

        return {
            "estado": "ok" if not errores else "fallo",
            "norma": "ISO 25012 — Exactitud",
            "total_registros": total,
            "registros_con_errores": len(indices_error),
            "porcentaje_exactitud": round(exactitud, 2),
            "detalle": errores,
        }

    def validar_consistencia(
        self,
        registros: list[dict],
        reglas: list[dict],
    ) -> dict:
        """Valida reglas de negocio entre campos (consistencia cruzada).

        ``reglas`` es una lista de dicts con:
            - ``descripcion``: texto explicativo de la regla.
            - ``fn``: callable que recibe un registro y devuelve ``True`` si es consistente.

        Ejemplo de reglas::

            [
                {
                    "descripcion": "fecha_fin >= fecha_inicio",
                    "fn": lambda r: r.get("fecha_fin", "") >= r.get("fecha_inicio", ""),
                },
                {
                    "descripcion": "precio > 0 si activo es True",
                    "fn": lambda r: not r.get("activo") or r.get("precio", 0) > 0,
                },
            ]

        Returns::

            {
                "estado": "ok" | "fallo",
                "norma": "ISO 25012 — Consistencia",
                "total_registros": 100,
                "registros_con_violaciones": 1,
                "porcentaje_consistencia": 99.0,
                "detalle": [{"indice": 7, "regla": "precio > 0 si activo es True"}]
            }
        """
        violaciones = []
        for i, registro in enumerate(registros):
            for regla in reglas:
                # La regla es un lambda del usuario: cualquier fallo se reporta, no crashea.
                try:
                    if not regla["fn"](registro):
                        violaciones.append({"indice": i, "regla": regla["descripcion"]})
                except Exception as exc:  # noqa: BLE001
                    violaciones.append(
                        {
                            "indice": i,
                            "regla": regla["descripcion"],
                            "error_evaluacion": str(exc),
                        }
                    )

        total = len(registros)
        indices_violados = {v["indice"] for v in violaciones}
        consistencia = ((total - len(indices_violados)) / total * 100) if total > 0 else 100.0

        return {
            "estado": "ok" if not violaciones else "fallo",
            "norma": "ISO 25012 — Consistencia",
            "total_registros": total,
            "registros_con_violaciones": len(indices_violados),
            "porcentaje_consistencia": round(consistencia, 2),
            "detalle": violaciones,
        }
