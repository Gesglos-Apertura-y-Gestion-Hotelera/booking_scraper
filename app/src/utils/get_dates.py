import os
import sys
from typing import Tuple
from datetime import datetime, date

from .logger import logger


def get_dates() -> Tuple[datetime, datetime]:
    args = sys.argv[1:]

    # 1. Env vars (FIX para mocks)
    check_in_raw = os.getenv('CHECK_IN') or ''
    check_out_raw = os.getenv('CHECK_OUT') or ''
    check_in_raw = check_in_raw.strip() if check_in_raw else ''
    check_out_raw = check_out_raw.strip() if check_out_raw else ''

    # 2. Args FALBACK
    if not check_in_raw and not check_out_raw and len(args) >= 4:
        check_in_raw = args[2].strip()
        check_out_raw = args[3].strip()

    # 2. VALIDAR que hay datos
    if not check_in_raw or not check_out_raw:
        logger.error("Faltan fechas: CHECK_IN y CHECK_OUT requeridas")
        sys.exit(1)

    # 3. Parsear fechas (FALLA AQUÍ → ValueError)
    try:
        check_in = datetime.strptime(check_in_raw, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_raw, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Formato de fecha inválido: {check_in_raw}, {check_out_raw}")
        sys.exit(1)

    # 4. AHORA sí validar lógica (check_in/check_out YA EXISTEN)
    today = date.today()

    if check_in.date() < today:
        logger.error(f"check_in en pasado: {check_in_raw}")
        sys.exit(1)

    if check_out <= check_in:
        logger.error(f"check_out ({check_out_raw}) debe ser después de check_in ({check_in_raw})")
        sys.exit(1)

    logger.info(f"Fechas OK: {check_in_raw} → {check_out_raw}")
    return check_in, check_out
