import os
import sys

from typing import Tuple
from datetime import datetime

from .logger import logger

def get_dates() -> Tuple[datetime, datetime]:
    args = sys.argv[1:]

    check_in_raw = os.getenv('CHECK_IN', '')
    if not check_in_raw:
        logger.error(f"check_in_raw env variable not found: ->{check_in_raw}<-")
        try:
            check_in_raw = args[2]
        except IndexError:
            logger.error(f"check_in_raw env variable not found: ->{check_in_raw}")
            pass
        except EnvironmentError as err:
            logger.error(f" ENV var CHECK_OUT not found : {err}")
            pass

    check_out_raw = os.getenv('CHECK_OUT', '')
    if not check_out_raw:
        logger.error(f"check_out_raw env variable not found: ->{check_out_raw}")
        try:
            check_out_raw = args[3]
        except IndexError:
            logger.error(f"check_out_raw env variable not found: ->{check_out_raw}")
        except EnvironmentError as err:
            logger.error(f" ENV var CHECK_OUT not found : {err}")
            pass

    check_in = None
    check_out = None
    if check_in_raw :
        check_in = datetime.strptime(check_in_raw, '%Y-%m-%d')
    if check_out_raw :
        check_out = datetime.strptime(check_out_raw, '%Y-%m-%d')

    return check_in, check_out

