import os
import sys
from typing import Tuple
from datetime import datetime, date, timedelta

from .logger import logger


def get_dates() -> Tuple[datetime, datetime]:
    args = sys.argv[1:]

    # 1. Env vars
    check_in_raw = os.getenv('CHECK_IN') or ''
    check_out_raw = os.getenv('CHECK_OUT') or ''
    check_in_raw = check_in_raw.strip() if check_in_raw else ''
    check_out_raw = check_out_raw.strip() if check_out_raw else ''

    # 2. Args FALLBACK (individual)
    if len(args) >= 4:
        if not check_in_raw:
            check_in_raw = args[2].strip() if len(args) > 2 else date.today().strftime('%Y-%m-%d')
        if not check_out_raw:
            check_out_raw = args[3].strip() if len(args) > 3 else (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    if not check_in_raw or not check_out_raw:
        logger.error(f"Faltan fechas: check_in_raw='{check_in_raw}', check_out_raw='{check_out_raw}'")
        sys.exit(1)

    try:
        check_in = datetime.strptime(check_in_raw, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_raw, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Formato inválido: {check_in_raw}, {check_out_raw}")
        sys.exit(1)

    today = date.today()
    if check_in.date() < today:
        logger.error(f"check_in pasado: {check_in_raw}")
        sys.exit(1)

    if check_out <= check_in:
        logger.error(f"check_out <= check_in: {check_out_raw} <= {check_in_raw}")
        sys.exit(1)

    logger.info(f"Fechas OK: {check_in_raw} → {check_out_raw}")
    return check_in, check_out