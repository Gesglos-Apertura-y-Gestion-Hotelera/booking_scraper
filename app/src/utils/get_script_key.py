import os
import sys

from .logger import  logger


def get_script_key()->str:
    # Acepta 1 O MÁS parámetros
    script_key = os.getenv('SCRIPT_KEY')
    if not script_key:
        try:
            logger.error(f" ** Var ENV script_key : ->{script_key}<-")
            args = sys.argv[1:]  # Todos los parámetros
            script_key = args[0]

        except Exception:
            logger.error(f" ** script key error: ->{script_key}<-")
            pass
    return script_key
