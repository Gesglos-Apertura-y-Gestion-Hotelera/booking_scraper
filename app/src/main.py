import subprocess

from utils.get_script_key import get_script_key
from utils.logger import logger


SCRIPTS = {
    'clientes_diario': 'Web_Scraping_Clientes.py',
    'clientes_prevision': 'Web_Scraping_Clientes_Adhoc.py',
    'competencia_diario': 'Web_Scraping_Competencia.py',
    'competencia_prevision': 'Web_Scraping_Competencia_Adhoc.py',
    'seguimiento_diario': 'Web_Scraping_Daily_Tracking.py',
    'personalizado': 'Web_Scryping_Booking.py'
}


def run_script(script_name):
    """Ejecuta script pasando sheet_data como variable de entorno"""
    cmd = ['python', f"src/{script_name}"]

    logger.info(f'-------- Ejecutando script {script_name} ----------')
    logger.info(f'Variables de entorno:')

    subprocess.run(cmd, timeout=1800)


def main():
    script_key = get_script_key()

    if script_key not in SCRIPTS:
        logger.error("ERROR: Script key not valid")
        return

    script = SCRIPTS[script_key]
    run_script(script)
    logger.info('✅ Main finalizado')


if __name__ == "__main__":
    main()