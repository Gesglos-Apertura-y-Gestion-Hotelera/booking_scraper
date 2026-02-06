import json
import os
import sys

from .logger import logger
from .fix_json_quotes import fix_json_quotes

def get_sheet_data()->list[str]:
    # Leer sheet_data de variable de entorno o argumento
    json_str = os.getenv('SHEET_DATA', '')
    try:
        if not json_str and len(sys.argv) > 1:
            json_str = sys.argv[2]

        if not json_str:
            logger.error("❌ No se recibió SHEET_DATA")
            logger.error("❌ Debe enviarse como variable de entorno o primer argumento")
            sys.exit(1)
    except IndexError:
        logger.error(f"❌ Sheet data extract from args FAILED {json_str} ")
        sys.exit(1)

    try:
        # Corregir comillas simples a dobles
        json_str = fix_json_quotes(json_str)
    except ValueError as e:
        logger.error(f"❌ JSON conversion failed {e}")

    try:
        hoteles = json.loads(json_str)

        if not isinstance(hoteles, list):
            logger.error(f"❌ JSON no es lista: {type(hoteles)}")
            sys.exit(1)

        if not hoteles:
            logger.error("❌ Lista de hoteles vacía")
            sys.exit(1)

        return hoteles

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando JSON: {e}")
        logger.error(f"❌ JSON recibido: {json_str}")
        sys.exit(1)
