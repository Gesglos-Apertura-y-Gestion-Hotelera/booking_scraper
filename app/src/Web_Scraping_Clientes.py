#!/usr/bin/env python3
"""
Web Scraping Clientes - Búsqueda Diaria (1 noche)
"""
import sys
import json
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd

from utils.logger import logger
from utils.enviar_sheets_clientes_diario import enviar_sheets_diario
from core.chrome_driver import ChromeDriverFactory
from core.scraper import BookingBaseScraper
from core.data_models import HotelSearchData

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyPzxk_tlVrVvQlZg0k8M0g_lIRifVqgf5EdA7EsdeMGdoHPYwNsZAiRN0Zk0U6EUbl/exec"


class ClientesDiarioScraper(BookingBaseScraper):
    """Scraper para búsqueda diaria de clientes"""

    def __init__(self, driver, hotels_data: List[HotelSearchData]):
        super().__init__(driver)
        self.hotels_data = hotels_data

    def run(self) -> List[dict]:
        """Ejecuta scraping para todos los hoteles"""
        # Fechas automáticas: hoy + 1 día
        checkin = datetime.now().strftime('%Y-%m-%d')
        checkout = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        logger.info(f"📅 Check-in: {checkin} | Check-out: {checkout}")

        results = []
        for hotel_data in self.hotels_data:
            try:
                result = self.search_hotel(hotel_data, checkin, checkout)
                results.append(result.to_dict())
                logger.info(f"✅ {result.nombre} - {result.precio}")
            except Exception as e:
                logger.error(f"❌ Error con {hotel_data.hotel}: {e}")
                results.append({
                    'nombre': hotel_data.hotel,
                    'precio': '0',
                    'calificacion': 'Error',
                    'ciudad': hotel_data.ciudad,
                    'check_in': checkin,
                    'check_out': checkout
                })

        return results


def load_data(json_str: Optional[str] = None) -> List[HotelSearchData]:
    """Carga datos desde JSON o Excel"""
    if json_str:
        data = json.loads(json_str)
        logger.info(f"✅ JSON cargado: {len(data)} hoteles")
        return [HotelSearchData.from_dict(item) for item in data]
    return []


def main():
    """Función principal"""
    logger.info("🚀 SCRAPING CLIENTES DIARIO")

    driver = None
    try:
        # Cargar datos
        json_data = sys.argv[1] if len(sys.argv) > 1 else None
        hotels_data = load_data(json_data)

        # Configurar driver
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        # Ejecutar scraping
        scraper = ClientesDiarioScraper(driver, hotels_data)
        results = scraper.run()

        # Enviar resultados
        logger.info(f"📤 Enviando {len(results)} resultados")
        enviar_sheets_diario(results, WEBAPP_URL)

        logger.info(f"✅ COMPLETADO: {len(results)} hoteles")

    except Exception as e:
        logger.error(f"💥 ERROR: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()