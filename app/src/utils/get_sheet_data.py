import json
import os
import sys

from .logger import logger
from .fix_json_quotes import fix_json_quotes


def get_sheet_data() -> list[dict]:
    """
    Lee SHEET_DATA desde variable de entorno o argumentos.
    Prioridad:
    1. Variable de entorno SHEET_DATA
    2. sys.argv[2] (formato antiguo: script_key sheet_data)
    3. sys.argv[1] (formato nuevo: solo sheet_data)
    """
    # Leer sheet_data de variable de entorno primero
    json_str = os.getenv('SHEET_DATA', '').strip()

    # Si no está en env, intentar desde argumentos
    if not json_str:
        # Intentar sys.argv[2] primero (formato antiguo)
        if len(sys.argv) > 2:
            json_str = sys.argv[2]
            logger.info("📊 SHEET_DATA leída desde sys.argv[2]")
        # Si no, intentar sys.argv[1] (formato nuevo o cuando solo se pasa sheet_data)
        elif len(sys.argv) > 1:
            # Verificar que argv[1] sea JSON y no un script_key
            try:
                test_parse = json.loads(sys.argv[1])
                if isinstance(test_parse, list):
                    json_str = sys.argv[1]
                    logger.info("📊 SHEET_DATA leída desde sys.argv[1]")
            except (json.JSONDecodeError, ValueError):
                # argv[1] no es JSON válido, probablemente es script_key
                pass
    else:
        logger.info("📊 SHEET_DATA leída desde variable de entorno")

    # Validar que tenemos datos
    if not json_str:
        logger.error("❌ No se recibió SHEET_DATA")
        logger.error("❌ Debe enviarse como variable de entorno SHEET_DATA o como argumento")
        logger.error(f"📋 DEBUG - SHEET_DATA env: '{os.getenv('SHEET_DATA', 'NOT SET')}'")
        logger.error(f"📋 DEBUG - sys.argv: {sys.argv}")
        sys.exit(1)

    # Corregir comillas simples a dobles
    try:
        json_str = fix_json_quotes(json_str)
    except ValueError as e:
        logger.error(f"❌ JSON conversion failed: {e}")
        logger.error(f"❌ JSON original: {json_str[:200]}...")
        sys.exit(1)

    try:
        hoteles = json.loads(json_str)

        if not isinstance(hoteles, list):
            logger.error(f"❌ JSON no es lista: {type(hoteles)}")
            logger.error(f"❌ Contenido: {hoteles}")
            sys.exit(1)

        if not hoteles:
            logger.error("❌ Lista de hoteles vacía")
            sys.exit(1)

        logger.info(f"✅ SHEET_DATA parseada: {len(hoteles)} hoteles")
        return hoteles

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando JSON: {e}")
        logger.error(f"❌ JSON recibido: {json_str[:500]}...")
        sys.exit(1)