#!/usr/bin/env python3
"""
Web Scraping Competencia Adhoc
Uso: python script.py '[{...}]' '2025-02-01' '2025-02-10'
"""
import sys
import json
import time
from datetime import datetime, timedelta
from typing import List

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.logger import logger
from utils.enviar_sheets_clientes_diario import enviar_sheets_diario

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyPzxk_tlVrVvQlZg0k8M0g_lIRifVqgf5EdA7EsdeMGdoHPYwNsZAiRN0Zk0U6EUbl/exec"


class CompetenciaAdhocScraper(BookingBaseScraper):
    """Scraper adhoc para competencia con rango de fechas"""

    def __init__(self, driver, competidores: List[dict], fecha_inicio: datetime, fecha_fin: datetime):
        super().__init__(driver)
        self.competidores = competidores
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

    def run(self) -> List[dict]:
        """Ejecuta scraping para rango de fechas"""
        results = []
        fecha = self.fecha_inicio

        while fecha < self.fecha_fin:
            siguiente = fecha + timedelta(days=1)
            checkin = fecha.strftime('%Y-%m-%d')
            checkout = siguiente.strftime('%Y-%m-%d')

            logger.info(f"📅 {checkin}")

            for comp in self.competidores:
                # Validar que sea dict
                if not isinstance(comp, dict):
                    logger.error(f"❌ Elemento no es dict: {type(comp)} - {comp}")
                    continue

                competidor = comp.get('competidor') or comp.get('Competidor') or comp.get('hotel') or comp.get(
                    'Hotel') or ''
                ciudad = comp.get('ciudad') or comp.get('Ciudad') or ''

                if not competidor or not ciudad:
                    logger.warning(f"⚠️ Datos incompletos: {comp}")
                    continue

                # Buscar (competidor + ciudad)
                search_term = f"{competidor}%20{ciudad}"
                url = self.build_search_url(search_term, checkin, checkout)

                self.driver.get(url)
                time.sleep(5)
                self.close_popup()
                time.sleep(2)

                # Extraer
                try:
                    nombre = self.extract_name()
                    precio = self.extract_price()
                    calificacion = self.extract_rating()
                except Exception as e:
                    logger.warning(f"⚠️ {competidor}: {e}")
                    nombre = competidor
                    precio = "0"
                    calificacion = "0"

                results.append({
                    'nombre': nombre,
                    'precio': precio,
                    'calificacion': calificacion,
                    'competidor': competidor,
                    'ciudad': ciudad,
                    'check_in': checkin,
                    'check_out': checkout
                })

                logger.info(f"✅ {nombre} - {precio}")

            fecha = siguiente

        return results

def main():
    if len(sys.argv) < 4:
        logger.error("❌ Uso: script.py '[{...}]' 'YYYY-MM-DD' 'YYYY-MM-DD'")
        sys.exit(1)

    try:
        parametros_json_str = sys.argv[1]
        logger.info(f"📊 JSON recibido (primeros 100 chars): {parametros_json_str[:100]}")

        competidores = json.loads(parametros_json_str)

        if not isinstance(competidores, list):
            logger.error(f"❌ JSON no es lista: {type(competidores)}")
            sys.exit(1)

        logger.info(f"✅ JSON parseado: {len(competidores)} competidores")
        logger.info(f"Primer elemento: {competidores[0] if competidores else 'vacío'}")

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando JSON: {e}")
        logger.error(f"JSON recibido: {parametros_json_str}")
        sys.exit(1)

    fecha_inicio = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    fecha_fin = datetime.strptime(sys.argv[3], '%Y-%m-%d')

    logger.info(f"📅 {fecha_inicio.date()} → {fecha_fin.date()}")

    # Ejecutar
    driver = ChromeDriverFactory.create_headless_driver()
    ChromeDriverFactory.setup_booking_cookies(driver)

    try:
        scraper = CompetenciaAdhocScraper(driver, competidores, fecha_inicio, fecha_fin)
        results = scraper.run()

        # Enviar a Sheets
        logger.info(f"📤 Enviando {len(results)} resultados")
        # TODO: configurar si este es el lugar correcto para enviar la informacion del scraper o si debe ir a otro archivo
        enviar_sheets_diario(results, WEBAPP_URL)
        logger.info("✅ COMPLETADO")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()