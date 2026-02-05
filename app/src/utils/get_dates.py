import os
import sys

from typing import Tuple
from datetime import datetime

def get_dates() -> Tuple[datetime, datetime]:
    args = sys.argv[1:]

    # 1. Obtener los valores (prioridad env, luego args)
    check_in_raw = os.getenv('CHECK_IN', '')
    if not check_in_raw:
        check_in_raw = args[2]

    check_out_raw = os.getenv('CHECK_OUT', '')
    if not check_out_raw:
        check_out_raw = args[3]

    check_in = datetime.strptime(check_in_raw, '%Y-%m-%d')
    check_out = datetime.strptime(check_out_raw, '%Y-%m-%d')

    return check_in, check_out