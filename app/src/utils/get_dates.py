import os
import sys

from typing import Tuple
from datetime import datetime

from .logger import logger


def get_dates()->Tuple[datetime,datetime]:
    # Acepta 1 O MÁS parámetros
    args = sys.argv[1:]  # Todos los parámetros
    logger.info(f'Argumentos recibidos: {args}')
    logger.info(f'Variables de entorno: SHEET_DATA={os.getenv("SHEET_DATA", "no definida")}')

    # Leer check_in y check_out de variables de entorno o argumentos
    check_in = os.getenv('CHECK_IN', '')
    if not check_in:
        check_in = args[2]
        check_in = datetime.strptime(check_in, '%Y-%m-%d')

    check_out = os.getenv('CHECK_OUT', '')
    if not check_out:
        check_out = args[3]
        check_out = datetime.strptime(check_out, '%Y-%m-%d')

    return check_in, check_out