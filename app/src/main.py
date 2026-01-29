#!/usr/bin/env python3
import sys
import os
import subprocess
from utils.logger import logger


SCRIPTS = {
    'clientes_diario': 'Web_Scraping_Clientes.py',
    'clientes_prevision': 'Web_Scraping_Clientes_Adhoc.py',
    'competencia_diario': 'Web_Scraping_Competencia.py',
    'competencia_prevision': 'Web_Scraping_Competencia_Adhoc.py',
    'seguimiento_diario': 'Web_Scraping_Daily_Tracking.py',
    'personalizado': 'Web_Scryping_Booking.py'
}


def run_script(script_name, sheet_data, check_in, check_out):
    """Ejecuta script pasando sheet_data como variable de entorno"""
    cmd = ['python', f"src/{script_name}"]

    env = os.environ.copy()

    # Pasar datos como variables de entorno
    if sheet_data:
        env['SHEET_DATA'] = sheet_data
    if check_in:
        env['CHECK_IN'] = check_in
    if check_out:
        env['CHECK_OUT'] = check_out

    logger.info(f'-------- Ejecutando script {script_name} ----------')
    logger.info(f'Variables de entorno:')
    logger.info(f'  SHEET_DATA: {sheet_data[:100] if sheet_data else "vacío"}...')
    logger.info(f'  CHECK_IN: {check_in}')
    logger.info(f'  CHECK_OUT: {check_out}')

    subprocess.run(cmd, env=env, timeout=1800)


def main():
    # Acepta 1 O MÁS parámetros
    args = sys.argv[1:]  # Todos los parámetros

    logger.info(f'Argumentos recibidos: {args}')
    logger.info(f'Variables de entorno: SHEET_DATA={os.getenv("SHEET_DATA", "no definida")}')

    if len(args) < 1:
        logger.error('❌ Falta script_key')
        sys.exit(1)

    script_key = args[0]

    # Leer sheet_data de variable de entorno (prioritario) o argumento
    sheet_data = os.getenv('SHEET_DATA', '')

    # Leer check_in y check_out de variables de entorno o argumentos
    check_in = os.getenv('CHECK_IN', '')
    if not check_in:
        check_in = args[1]

    check_out = os.getenv('CHECK_OUT', '')
    if not check_out:
        check_out = args[2]

    if script_key not in SCRIPTS:
        logger.error(f'❌ Script inválido: {script_key}')
        logger.error(f'Opciones: {list(SCRIPTS.keys())}')
        sys.exit(1)

    logger.info(f'Script: {script_key}')
    logger.info(f'Sheet data length: {len(sheet_data)}')
    logger.info(f'Check-in: {check_in}')
    logger.info(f'Check-out: {check_out}')

    script = SCRIPTS[script_key]
    run_script(script, sheet_data, check_in, check_out)
    logger.info('✅ Main finalizado')


if __name__ == "__main__":
    main()