#!/usr/bin/env python3
"""
Main orchestrator - Instancia dinámicamente scrapers según script_key
"""
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import dotenv

from core.chrome_driver import ChromeDriverFactory
from core.scraper_registry import SCRAPER_REGISTRY
from utils.enviar_sheets import enviar_sheets
from utils.get_script_key import get_script_key
from utils.get_dates import get_dates
from utils.get_sheet_data import get_sheet_data
from utils.logger import logger


dotenv.load_dotenv()

def import_scraper_class(module_name: str, class_name: str):
    """
    Importa dinámicamente una clase de scraper

    Args:
        module_name: Nombre del módulo (ej: 'Web_Scraping_Clientes')
        class_name: Nombre de la clase (ej: 'ClientesDiarioScraper')

    Returns:
        La clase importada
    """
    try:
        # Importar módulo dinámicamente
        module = __import__(f'{module_name}', fromlist=[class_name])
        scraper_class = getattr(module, class_name)
        logger.info(f"import: {module_name} -> {class_name}")
        return scraper_class
    except (ImportError, AttributeError) as e:
        logger.error(f"❌ Error importando {class_name} desde {module_name}: {e}")
        raise


def run_scraper(
        script_key: str,
        sheet_data: list,
        check_in: Optional[datetime] = None,
        check_out: Optional[datetime] = None
):
    """
    Instancia y ejecuta el scraper correspondiente

    Args:
        script_key: Clave del scraper a ejecutar
        sheet_data: Datos de hoteles/competencia
        check_in: Fecha de inicio (opcional, según scraper)
        check_out: Fecha de fin (opcional, según scraper)
    """
    if script_key not in SCRAPER_REGISTRY:
        logger.error(f"❌ Script key '{script_key}' no válido")
        logger.info(f"📋 Opciones válidas: {', '.join(SCRAPER_REGISTRY.keys())}")
        raise ValueError(f"Script key inválido: {script_key}")

    scraper_config = SCRAPER_REGISTRY.get(script_key) 
    logger.info(f"🚀 Iniciando: {scraper_config.get('description')}")
    logger.info(f"📍 📍 📍 📦 📍 📍 📍  Módulo: {scraper_config.get('module')}")
    logger.info(f"🏷️ Clase: {scraper_config.get('class')}")
    logger.info(f"📊 Sheet destino: {scraper_config.get('sheet_name')}")
    logger.info(f"🏨 Registros a procesar: {len(sheet_data)}")

    # Validar fechas si son requeridas
    if scraper_config.get('requires_dates'):
        if not check_in or not check_out:
            logger.error("❌ Este scraper requiere fechas check_in y check_out")
            raise ValueError("Fechas requeridas para este scraper")

        if isinstance(check_in, str) or isinstance(check_out, str):
            # Convertir strings a objetos datetime
            check_in = datetime.strptime(check_in, '%Y-%m-%d')
            check_out = datetime.strptime(check_out, '%Y-%m-%d')
        logger.info(f"📅 Rango: {check_in.strftime('%Y-%m-%d')} → {check_out.strftime('%Y-%m-%d')}")

    driver = None
    try:
        # Importar clase dinámicamente
        ScraperClass = import_scraper_class(scraper_config['module'], scraper_config['class'])

        # Crear driver
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        # Obtener el nombre del parámetro de datos (hoteles vs competidores)
        data_param_name = scraper_config['data_param']
        logger.info(f"data param:{data_param_name}\n config:{scraper_config}")

        # Instanciar scraper según tipo
        if scraper_config['requires_dates']:
            # Scrapers que requieren rango de fechas
            scraper = ScraperClass(
                driver=driver,
                **{data_param_name: sheet_data},
                check_in=check_in,
                check_out=check_out
            )
        else:
            # Scrapers diarios (solo necesitan hoteles/competidores)
            scraper = ScraperClass(
                driver=driver,
                **{data_param_name: sheet_data}
            )

        # Ejecutar scraping
        logger.info("⚙️  Ejecutando scraping...")
        results = scraper.run()

        logger.info(f"📤 Enviando {len(results)} resultados a Sheets")

        WEBAPP_URL = os.environ.get('WEBAPP_URL', '').strip()
        if not WEBAPP_URL:
            logger.error("💥 ERROR WEBAPP_URL es None")

        enviar_sheets(lista_datos=results,
                        url_apps_script=WEBAPP_URL,
                        sheet_name=scraper_config['sheet_name'])
        return results


    except Exception as e:
        logger.error(f"💥 ERROR durante ejecución: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

    finally:
        if driver:
            logger.info("🔌 Cerrando driver...")
            driver.quit()


def main():
    """Función principal del orchestrator"""

    # codigo para pruebas unitarias
    logger.info("=" * 80)
    logger.info("🎬 INICIANDO ORCHESTRATOR DE SCRAPERS")
    logger.info("=" * 80)
    script_key = ""
    sheet_data = []
    try:
        # Obtener parámetros
        script_key = get_script_key()
    except ValueError as e:
        logger.error(f"❌ No{e}")
    except Exception as e:
        logger.error(f"❌ No{e}")

    try:
        sheet_data = get_sheet_data()
        if not sheet_data:
            logger.error("❌ No hay datos de hoteles para procesar")
            return
    except EnvironmentError as e:
        logger.error(f"❌ No hay parametros {e}")


    scripts_sin_fechas = ["clientes_diario",
                          "competencia_diario",
                          "seguimiento_diario"]
    check_in, check_out = None, None
    try:
        if script_key not in scripts_sin_fechas:
            check_in, check_out = get_dates()
    except Exception as e:
        if script_key not in scripts_sin_fechas:
            logger.error(f"⚠️  No se proporcionaron fechas: {e}")


    try:
        # Ejecutar scraper
        results = run_scraper(
            script_key=script_key,
            sheet_data=sheet_data,
            check_in=check_in,
            check_out=check_out
        )

        # Resumen final
        logger.info("=" * 80)
        logger.info(f"✅ PROCESO COMPLETADO EXITOSAMENTE")
        import pprint as pp
        logger.info(f"📊 Total de registros: {len(results)} resultados: {pp.pprint(results)}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"💥 PROCESO TERMINADO CON ERRORES")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        raise


if __name__ == "__main__":
    main()