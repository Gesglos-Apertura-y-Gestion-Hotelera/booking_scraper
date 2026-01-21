#!/usr/bin/env python3
import sys
import os
import subprocess
from logger import logger


os.environ['PYTHONWARNINGS'] = 'ignore'

# Mapeo directo de parámetro → script
SCRIPTS = {
    'clientes_diario': 'Web_Scraping_Clientes.py',
    'clientes_prevision': 'Web_Scraping_Clientes_Adhoc.py',
    'competencia_diario': 'Web_Scraping_Competencia.py',
    'competencia_prevision': 'Web_Scraping_Competencia_Adhoc.py',
    'seguimiento_diario': 'Web_Scraping_Daily_Tracking.py',
    'personalizado': 'Web_Scryping_Booking.py',
    'update_df': 'Update_DF.py'
}


def run_script(script_name):
    """Ejecuta script en background completamente silencioso"""
    cmd = ['python', f"src/{script_name}"]
    logger.info(f'-------- Ejecutando script {script_name} ----------')
    subprocess.run(cmd,
                   # stdout=subprocess.DEVNULL,  # Silenciar STDOUT
                   # stderr=subprocess.DEVNULL,  # Silenciar STDERR
                   timeout=1800)  # 30 min timeout


def main():
    # Acepta 1 O MÁS parámetros
    args = sys.argv[1:]  # Todos los parámetros

    if not args:
        # Sin parámetros → default
        script_key = 'clientes_diario'
    else:
        # Primer parámetro (o todos si quieres procesarlos)
        script_key = args[0]

    # Validar y ejecutar
    if script_key not in SCRIPTS:
        sys.exit(1)

    script = SCRIPTS[script_key]
    run_script(script)
    logger.info('Main finalizado')

if __name__ == "__main__":
    main()