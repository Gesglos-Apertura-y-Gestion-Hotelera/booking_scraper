import sys

from .logger import  logger


def get_script_key()->str:
    # Acepta 1 O MÁS parámetros
    args = sys.argv[1:]  # Todos los parámetros
    script_key = args[0]

    return script_key