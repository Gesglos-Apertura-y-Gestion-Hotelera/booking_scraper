#!/usr/bin/env python3
"""
Web Scraping Clientes Diario
Lee JSON desde variable de entorno SHEET_DATA o argumento
"""
import os
import re
import sys

import time
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.cleaner import DataCleaner
from utils.logger import logger
from utils.enviar_sheets import enviar_sheets
from utils.get_sheet_data import get_sheet_data


WEBAPP_URL = os.environ.get('WEBAPP_URL')

class ClientesDiarioScraper(BookingBaseScraper):
    """Scraper para búsqueda diaria de clientes"""

    def __init__(self, driver, hoteles: list):
        super().__init__(driver)
        self.hoteles = hoteles

    def run(self) -> list:
        """Ejecuta scraping para todos los hoteles"""
        checkin = datetime.now().strftime('%Y-%m-%d')
        checkout = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        logger.info(f"📅 Check-in: {checkin} | Check-out: {checkout}")

        results = []
        for hotel_data in self.hoteles:
            if not isinstance(hotel_data, dict):
                logger.error(f"❌ Elemento no es dict: {type(hotel_data)}")
                continue

            hotel = hotel_data.get('hotel') or hotel_data.get('Hotel') or ''
            ciudad = hotel_data.get('ciudad') or hotel_data.get('Ciudad') or ''

            if not hotel or not ciudad:
                logger.warning(f"⚠️ Datos incompletos: {hotel_data}")
                continue

            hotel_ciudad = f"{hotel} - {ciudad}"
            hotel_ciudad = re.sub(r"\s{1,10}", "+", hotel_ciudad)

            url = self.build_search_url(hotel_ciudad, checkin, checkout)
            logger.info(f"URL: {url}")

            self.driver.get(url)
            time.sleep(5)
            self.close_popup()
            time.sleep(2)

            try:
                nombre = self.extract_name()
                precio = self.extract_price()
                calificacion = self.extract_rating_details()
                import pprint as pp
                print("*******************")
                pp.pprint(calificacion)
                
            except Exception as e:
                logger.warning(f"⚠️ {hotel}: {e}")
                nombre = hotel
                precio = "0"
                calificacion = "No disponible"

            cleaner = DataCleaner()
            divisa, precio = cleaner.limpiar_precio(precio)
            results.append({
                'hotel': nombre,
                'divisa': divisa,
                'precio': precio,
                'review_promedio': calificacion.get("calificacion_cualitativa"),
                'opiniones': calificacion.get("comentarios"),
                'puntuacion': calificacion.get("puntuacion"),
                'ciudad': ciudad,
                'check_in': checkin,
                'check_out': checkout
            })
            print("--------------------------")
            pp.pprint(results)
            logger.info(f"✅ {nombre} - {precio}")

        return results

def buscar_reservas_hoy():
    logger.info("🚀 SCRAPING CLIENTES DIARIO")

    driver = None
    try:
        hoteles = get_sheet_data()

        # Ejecutar scraping
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        scraper = ClientesDiarioScraper(driver, hoteles)
        results = scraper.run()

        # Enviar a Sheets
        logger.info(f"📤 Enviando {len(results)} resultados")
        enviar_sheets(results, WEBAPP_URL, sheet_name='clientes')

        logger.info(f"✅ COMPLETADO: {len(results)} hoteles")

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
    buscar_reservas_hoy()