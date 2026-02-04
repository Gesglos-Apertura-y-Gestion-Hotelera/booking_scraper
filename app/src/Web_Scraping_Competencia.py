#!/usr/bin/env python3
"""
Web Scraping Competencia Diario
Scraping diario de precios de competidores en Booking.com
"""
import os
import re
import sys
import time
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.cleaner import DataCleaner
from utils.enviar_sheets import enviar_sheets
from utils.get_sheet_data import get_sheet_data
from utils.logger import logger


class CompetenciaDiarioScraper(BookingBaseScraper):
    """Scraper para búsqueda diaria de competidores"""

    def __init__(self, driver, competidores: list):
        """
        Args:
            driver: Instancia de Selenium WebDriver
            competidores: Lista de dicts con 'competidor'/'Competidor' y 'ciudad'/'Ciudad'
        """
        super().__init__(driver)
        self.competidores = competidores

    def run(self) -> list:
        """Ejecuta scraping para todos los competidores"""
        checkin = datetime.now().strftime('%Y-%m-%d')
        checkout = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        logger.info(f"📅 Check-in: {checkin} | Check-out: {checkout}")

        results = []
        for comp_data in self.competidores:
            if not isinstance(comp_data, dict):
                logger.error(f"❌ Elemento no es dict: {type(comp_data)}")
                continue

            # Normalizar claves (mayúsculas o minúsculas)
            competidor = comp_data.get('competidor') or comp_data.get('Competidor') or ''
            ciudad = comp_data.get('ciudad') or comp_data.get('Ciudad') or ''
            hotel = comp_data.get('hotel') or comp_data.get('Hotel') or ''
            buscar = comp_data.get('buscar') or comp_data.get('Buscar') or ''

            if not competidor or not ciudad:
                logger.warning(f"⚠️ Datos incompletos: {comp_data}")
                continue

            # Construir búsqueda: "Nombre Competidor Ciudad"
            competidor_ciudad = f"{competidor} - {ciudad}"
            competidor_ciudad = re.sub(r"\s{1,10}", "+", competidor_ciudad)

            url = self.build_search_url(competidor_ciudad, checkin, checkout)
            logger.info(f"🔍 URL: {url}")

            self.driver.get(url)
            time.sleep(5)
            self.close_popup()
            time.sleep(2)

            rating_details = None
            try:
                nombre = self.extract_name()
                precio = self.extract_price()
                rating_details = self.extract_rating_details()

            except Exception as e:
                logger.warning(f"⚠️ {competidor} ({checkin}): {e}")
                nombre = competidor
                precio = "0"
                rating_details = {
                'puntuacion': 0,
                'calificacion_cualitativa': "",
                'comentarios': None
            }
            cleaner = DataCleaner()
            divisa, precio = cleaner.limpiar_precio(precio)

            results.append({
                'hotel': nombre,
                'precio': precio,
                'divisa': divisa,
                'puntuacion': rating_details['puntuacion'],
                'competidor': competidor,
                'review_promedio': rating_details['calificacion_cualitativa'],
                'ciudad': ciudad,
                'check_in': checkin,
                'check_out': checkout,
                'comentarios': rating_details['comentarios'],
            })

            logger.info(f"✅  rating_details {rating_details} ")

        return results


def buscar_competencia_hoy():
    """Función principal para ejecutar el scraper diario de competencia"""
    logger.info("🚀 SCRAPING COMPETENCIA DIARIO")

    driver = None
    try:
        # Obtener datos de competidores
        competidores = get_sheet_data()

        # Ejecutar scraping
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        scraper = CompetenciaDiarioScraper(driver, competidores)
        results = scraper.run()

        # Enviar a Sheets
        logger.info(f"📤 Enviando {len(results)} resultados")
        enviar_sheets(results, os.environ.get('WEBAPP_URL'), sheet_name='competencia')

        logger.info(f"✅ COMPLETADO: {len(results)} competidores")

    except Exception as e:
        logger.error(f"💥 ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # codigo para pruebas unitarias
    buscar_competencia_hoy()