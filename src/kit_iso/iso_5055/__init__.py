"""ISO/IEC 5055 — Calidad de código automatizada: mapeo de hallazgos de bandit a CWE."""

import json
import subprocess  # nosec B404 — uso controlado: solo ejecuta bandit con argumentos fijos

# Mapeo bandit test_id → CWE-ID (selección de las debilidades más comunes).
# Referencia: https://cwe.mitre.org/ + https://bandit.readthedocs.io/
_BANDIT_A_CWE: dict[str, str] = {
    "B101": "CWE-617",  # assert usada en código de producción
    "B102": "CWE-78",  # exec
    "B103": "CWE-732",  # permisos de archivo inseguros
    "B105": "CWE-259",  # contraseña hardcodeada
    "B106": "CWE-259",  # contraseña hardcodeada en función
    "B107": "CWE-259",  # contraseña hardcodeada como argumento
    "B108": "CWE-377",  # archivo temporal inseguro
    "B110": "CWE-390",  # except: pass (error swallowed)
    "B201": "CWE-94",  # Flask debug=True
    "B301": "CWE-502",  # pickle.loads — deserialización insegura
    "B302": "CWE-502",  # marshal.loads
    "B303": "CWE-327",  # MD2/MD4/MD5/SHA1 (hash débil)
    "B304": "CWE-327",  # DES/RC2/RC4 (cifrado débil)
    "B305": "CWE-327",  # ECB mode
    "B307": "CWE-78",  # eval
    "B308": "CWE-79",  # mark_safe (XSS)
    "B310": "CWE-601",  # urllib: redirección abierta potencial
    "B311": "CWE-330",  # random no criptográfico
    "B312": "CWE-676",  # telnetlib (protocolo inseguro)
    "B313": "CWE-611",  # xml.etree (XXE)
    "B314": "CWE-611",  # xml.etree.cElementTree (XXE)
    "B315": "CWE-611",  # expat (XXE)
    "B316": "CWE-611",  # xml.sax (XXE)
    "B317": "CWE-611",  # minidom (XXE)
    "B318": "CWE-611",  # pulldom (XXE)
    "B319": "CWE-611",  # lxml (XXE)
    "B321": "CWE-319",  # ftp (texto claro)
    "B323": "CWE-295",  # unverified_context (TLS sin verificar)
    "B324": "CWE-327",  # hashlib débil
    "B401": "CWE-319",  # import telnetlib
    "B402": "CWE-319",  # import ftplib
    "B403": "CWE-502",  # import pickle
    "B404": "CWE-78",  # import subprocess
    "B405": "CWE-611",  # import xml
    "B501": "CWE-295",  # ssl sin verificar certificado
    "B502": "CWE-326",  # ssl protocolo débil
    "B505": "CWE-326",  # clave criptográfica débil
    "B506": "CWE-20",  # yaml.load (inyección)
    "B507": "CWE-295",  # ssh sin strict host key checking
    "B601": "CWE-78",  # paramiko exec_command
    "B602": "CWE-78",  # subprocess shell=True
    "B603": "CWE-78",  # subprocess sin shell (parcial path)
    "B605": "CWE-78",  # start_process path parcial
    "B607": "CWE-78",  # start_process sin shell
    "B608": "CWE-89",  # SQL hardcodeado (inyección SQL)
    "B609": "CWE-78",  # wildcard injection
    "B610": "CWE-89",  # Django extra raw SQL
    "B611": "CWE-89",  # Django RawSQL
    "B701": "CWE-94",  # Jinja2 autoescape=False
    "B702": "CWE-79",  # Mako sin escape
    "B703": "CWE-94",  # Django mark_safe
}

# Categorías ISO 5055 (estructura de las cuatro características críticas).
CATEGORIAS_ISO5055 = {
    "seguridad": [
        "CWE-89",
        "CWE-78",
        "CWE-79",
        "CWE-94",
        "CWE-502",
        "CWE-611",
        "CWE-327",
        "CWE-295",
        "CWE-330",
        "CWE-601",
        "CWE-20",
        "CWE-319",
        "CWE-259",
        "CWE-326",
    ],
    "fiabilidad": ["CWE-390", "CWE-391", "CWE-617", "CWE-732", "CWE-377"],
    "mantenibilidad": [],  # cubierta por radon (iso_25010)
    "rendimiento": [],  # cubierta por medir_performance (iso_25010)
}


class AnalizadorISO5055:
    """Analiza código fuente y mapea hallazgos de bandit a CWE (ISO/IEC 5055).

    ISO 5055 define cuatro categorías de debilidades críticas que afectan a la
    calidad del software: Seguridad, Fiabilidad, Mantenibilidad y Rendimiento.
    Esta clase cubre Seguridad y Fiabilidad mediante el mapeo bandit → CWE.

    Requiere ``bandit`` instalado (incluido en las dependencias dev del kit).

    Ejemplo::

        an = AnalizadorISO5055()
        resultado = an.analizar_directorio("src/")
        for h in resultado["hallazgos_cwe"]:
            print(h["cwe"], h["descripcion"])
    """

    def analizar_directorio(self, directorio: str) -> dict:
        """Ejecuta bandit y mapea cada hallazgo a su CWE correspondiente.

        Returns::

            {
                "estado": "ok" | "fallo" | "error",
                "norma": "ISO/IEC 5055",
                "hallazgos_cwe": [{"cwe": "CWE-89", "bandit_id": "B608", ...}],
                "resumen_por_cwe": {"CWE-89": 2, ...},
                "resumen_por_categoria": {"seguridad": 5, "fiabilidad": 1}
            }
        """
        try:
            proc = subprocess.run(  # nosec B603 B607 — comando fijo sin shell; `directorio` es un argumento posicional, no código
                ["bandit", "-r", directorio, "-f", "json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            # bandit devuelve exit 1 si encuentra issues (normal) — parseamos igualmente.
            datos = json.loads(proc.stdout or '{"results": []}')
        except subprocess.TimeoutExpired:
            return {"estado": "error", "error": "timeout al ejecutar bandit", "hallazgos_cwe": []}
        except json.JSONDecodeError as e:
            return {"estado": "error", "error": f"salida JSON inválida: {e}", "hallazgos_cwe": []}
        except FileNotFoundError:
            return {
                "estado": "error",
                "error": "bandit no encontrado — instala con: pip install bandit",
                "hallazgos_cwe": [],
            }

        hallazgos_cwe = []
        for r in datos.get("results", []):
            test_id = r.get("test_id", "")
            cwe = _BANDIT_A_CWE.get(test_id, f"CWE-desconocido ({test_id})")
            hallazgos_cwe.append(
                {
                    "cwe": cwe,
                    "bandit_id": test_id,
                    "descripcion": r.get("issue_text", ""),
                    "severidad": r.get("issue_severity", ""),
                    "archivo": r.get("filename", ""),
                    "linea": r.get("line_number", 0),
                }
            )

        return {
            "estado": "ok" if not hallazgos_cwe else "fallo",
            "norma": "ISO/IEC 5055 — Seguridad + Fiabilidad (CWE mapping)",
            "directorio": directorio,
            "hallazgos_cwe": hallazgos_cwe,
            "resumen_por_cwe": self._contar_cwe(hallazgos_cwe),
            "resumen_por_categoria": self._categorizar(hallazgos_cwe),
        }

    @staticmethod
    def _contar_cwe(hallazgos: list[dict]) -> dict[str, int]:
        resumen: dict[str, int] = {}
        for h in hallazgos:
            cwe = h["cwe"]
            resumen[cwe] = resumen.get(cwe, 0) + 1
        return resumen

    @staticmethod
    def _categorizar(hallazgos: list[dict]) -> dict[str, int]:
        conteo = {cat: 0 for cat in CATEGORIAS_ISO5055}
        for h in hallazgos:
            for cat, cwes in CATEGORIAS_ISO5055.items():
                if h["cwe"] in cwes:
                    conteo[cat] += 1
        return conteo
