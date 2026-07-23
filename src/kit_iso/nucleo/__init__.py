# Nucleo del sistema ISO
import logging

# Logger global (reusable en módulos).
logger = logging.getLogger("kit_iso")
logger.setLevel(logging.INFO)


def config_comun(key: str):
    # Placeholder para configs seguras (ej. env vars).
    import os

    return os.getenv(key, "default")
