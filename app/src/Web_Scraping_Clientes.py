#!/usr/bin/env python3
"""
Web Scraping Clientes Diario
Lee JSON desde variable de entorno SHEET_DATA o argumento
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.logger import logger
from utils.enviar_sheets_clientes_diario import enviar_sheets_diario

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyPzxk_tlVrVvQlZg0k8M0g_lIRifVqgf5EdA7EsdeMGdoHPYwNsZAiRN0Zk0U6EUbl/exec"


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
                calificacion = self.extract_rating()
            except Exception as e:
                logger.warning(f"⚠️ {hotel}: {e}")
                nombre = hotel
                precio = "0"
                calificacion = "No disponible"

            results.append({
                'nombre': nombre,
                'precio': precio,
                'calificacion': calificacion,
                'ciudad': ciudad,
                'check_in': checkin,
                'check_out': checkout
            })

            logger.info(f"✅ {nombre} - {precio}")

        return results


def fix_json_quotes(json_str: str) -> str:
    """
    Convierte JSON malformado a JSON válido
    Casos:
    - Comillas simples → dobles
    - Sin comillas en propiedades → con comillas
    """

    # 1. Reemplazar comillas simples por dobles
    json_str = json_str.replace("'", '"')

    # 2. Agregar comillas a propiedades sin comillas
    # Patrón: {palabra: o ,palabra:
    json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*):', r'\1"\2"\3:', json_str)

    return json_str


def main():
    logger.info("🚀 SCRAPING CLIENTES DIARIO")

    driver = None
    try:
        # Leer sheet_data de variable de entorno o argumento
        json_str = os.getenv('SHEET_DATA', '')

        if not json_str and len(sys.argv) > 1:
            json_str = sys.argv[1]

        if not json_str:
            logger.error("❌ No se recibió SHEET_DATA")
            logger.error("Debe enviarse como variable de entorno o primer argumento")
            sys.exit(1)

        logger.info(f"📊 JSON original (150 chars): {json_str[:150]}")

        # Corregir comillas simples a dobles
        json_str = fix_json_quotes(json_str)
        logger.info(f"🔧 JSON corregido (150 chars): {json_str[:150]}")

        try:
            hoteles = json.loads(json_str)

            if not isinstance(hoteles, list):
                logger.error(f"❌ JSON no es lista: {type(hoteles)}")
                sys.exit(1)

            if not hoteles:
                logger.error("❌ Lista de hoteles vacía")
                sys.exit(1)

            logger.info(f"✅ {len(hoteles)} hoteles parseados")
            logger.info(f"Primer hotel: {hoteles[0]}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            logger.error(f"JSON recibido: {json_str}")
            sys.exit(1)

        # Ejecutar scraping
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        scraper = ClientesDiarioScraper(driver, hoteles)
        results = scraper.run()

        # Enviar a Sheets
        logger.info(f"📤 Enviando {len(results)} resultados")
        enviar_sheets_diario(results, WEBAPP_URL)

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
    main()