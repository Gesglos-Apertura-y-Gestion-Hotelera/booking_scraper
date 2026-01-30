#!/usr/bin/env python3
"""
Main orchestrator - Instancia dinámicamente scrapers según script_key
"""

from datetime import datetime
from typing import Optional

from core.chrome_driver import ChromeDriverFactory
from utils.get_script_key import get_script_key
from utils.get_dates import get_dates
from utils.get_sheet_data import get_sheet_data
from utils.logger import logger

# Mapeo de script_key a clases de scraper
SCRAPER_REGISTRY = {
    'clientes_diario': {
        'module': 'Web_Scraping_Clientes',
        'class': 'ClientesDiarioScraper',
        'requires_dates': False,
        'description': 'Scraping diario de clientes (hoy)'
    },
    'clientes_prevision': {
        'module': 'Web_Scraping_Clientes_Adhoc',
        'class': 'ClientesDiarioScraperAdHoc',
        'requires_dates': True,
        'description': 'Scraping de clientes en rango de fechas'
    },
    'competencia_diario': {
        'module': 'Web_Scraping_Competencia',
        'class': 'CompetenciaDiarioScraper',
        'requires_dates': False,
        'description': 'Scraping diario de competencia (hoy)'
    },
    'competencia_prevision': {
        'module': 'Web_Scraping_Competencia_Adhoc',
        'class': 'CompetenciaDiarioScraperAdHoc',
        'requires_dates': True,
        'description': 'Scraping de competencia en rango de fechas'
    },
    'seguimiento_diario': {
        'module': 'Web_Scraping_Daily_Tracking',
        'class': 'DailyTrackingScraper',
        'requires_dates': False,
        'description': 'Scraping de seguimiento diario'
    },
    'personalizado': {
        'module': 'Web_Scryping_Booking',
        'class': 'BookingScraperPersonalizado',
        'requires_dates': True,
        'description': 'Scraping personalizado de Booking'
    }
}


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
        webapp_url: URL para enviar resultados (opcional)
    """
    if script_key not in SCRAPER_REGISTRY:
        logger.error(f"❌ Script key '{script_key}' no válido")
        logger.info(f"📋 Opciones válidas: {', '.join(SCRAPER_REGISTRY.keys())}")
        raise ValueError(f"Script key inválido: {script_key}")

    config = SCRAPER_REGISTRY[script_key]
    logger.info(f"🚀 Iniciando: {config['description']}")
    logger.info(f"📦 Módulo: {config['module']}")
    logger.info(f"🏷️  Clase: {config['class']}")
    logger.info(f"🏨 Hoteles a procesar: {len(sheet_data)}")
    logger.info(f"📋 check in: {check_in}")
    logger.info(f"📋 Check out: {check_out}")

    # Validar fechas si son requeridas
    if config['requires_dates']:
        if not check_in or not check_out:
            logger.error("❌ Este scraper requiere fechas check_in y check_out")
            raise ValueError("Fechas requeridas para este scraper")
        logger.info(f"📅 Rango: {check_in.strftime('%Y-%m-%d')} → {check_out.strftime('%Y-%m-%d')}")

    driver = None
    try:
        # Importar clase dinámicamente
        ScraperClass = import_scraper_class(config['module'], config['class'])

        # Crear driver
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        # Instanciar scraper según tipo
        if config['requires_dates']:
            # Scrapers que requieren rango de fechas
            scraper = ScraperClass(
                driver=driver,
                hoteles=sheet_data,
                check_in=check_in,
                check_out=check_out
            )
        else:
            # Scrapers diarios (solo necesitan hoteles)
            scraper = ScraperClass(
                driver=driver,
                hoteles=sheet_data
            )

        # Ejecutar scraping
        logger.info("⚙️  Ejecutando scraping...")
        results = scraper.run()

        logger.info(f"✅ Scraping completado: {len(results)} registros")
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
    logger.info("=" * 80)
    logger.info("🎬 INICIANDO ORCHESTRATOR DE SCRAPERS")
    logger.info("=" * 80)

    try:
        # Obtener parámetros
        script_key = get_script_key()
        sheet_data = get_sheet_data()

        # Obtener fechas (pueden ser None si no se proporcionan)
        try:
            check_in, check_out = get_dates()
        except Exception as e:
            logger.warning(f"⚠️  No se proporcionaron fechas: {e}")
            check_in, check_out = None, None

        # Validar datos
        if not sheet_data:
            logger.error("❌ No hay datos de hoteles para procesar")
            return

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
        logger.info(f"📊 Total de registros: {len(results)}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"💥 PROCESO TERMINADO CON ERRORES")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        raise


if __name__ == "__main__":
    main()