"""
Scraper Ad-Hoc para búsqueda de clientes en rango de fechas
Hereda y reutiliza ClientesDiarioScraper
"""
import os
import re
import time
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.cleaner import DataCleaner
from utils.enviar_sheets import enviar_sheets
from utils.logger import logger

WEBAPP_URL = os.environ.get('WEBAPP_URL')

class ClientesDiarioScraperAdHoc(BookingBaseScraper):
    """
    Scraper Ad-Hoc para búsqueda de hoteles en rango de fechas personalizado.
    Reutiliza toda la lógica de BookingBaseScraper.
    """

    def __init__(self, driver, hoteles: list, check_in: datetime, check_out: datetime):
        """
        Args:
            driver: Instancia de Selenium WebDriver
            hoteles: Lista de dicts con 'hotel'/'Hotel' y 'ciudad'/'Ciudad'
            check_in: Fecha inicial (datetime)
            check_out: Fecha final (datetime)
        """
        super().__init__(driver)
        self.hoteles = hoteles
        self.check_in = check_in
        self.check_out = check_out

    def run(self) -> list:
        """
        Ejecuta scraping para todos los hoteles en el rango de fechas.
        Itera día por día desde check_in hasta check_out.
        """
        results = []

        # Iterar sobre cada día en el rango de fechas
        fecha_actual = self.check_in

        while fecha_actual < self.check_out:
            siguiente_dia = fecha_actual + timedelta(days=1)
            checkin_str = fecha_actual.strftime('%Y-%m-%d')
            checkout_str = siguiente_dia.strftime('%Y-%m-%d')

            logger.info(f"📅 Procesando: {checkin_str} → {checkout_str}")

            # Iterar sobre cada hotel
            for hotel_data in self.hoteles:
                if not isinstance(hotel_data, dict):
                    logger.error(f"❌ Elemento no es dict: {type(hotel_data)}")
                    continue

                # Normalizar claves (mayúsculas o minúsculas)
                Hotel = hotel_data.get('hotel', '')
                ciudad = hotel_data.get('ciudad', '')

                if Hotel == '' or ciudad == '':
                    logger.warning(f"⚠️ Datos incompletos: {hotel_data}")
                    continue

                # Construir búsqueda
                hotel_ciudad = f"{Hotel} - {ciudad}"
                hotel_ciudad = re.sub(r"\s{1,10}", "+", hotel_ciudad)

                # Usar el metodo heredado de BookingBaseScraper
                url = self.build_search_url(hotel_ciudad, checkin_str, checkout_str)
                logger.info(f"🔍 {Hotel} | {checkin_str}")
                logger.info(f"url: {url}")
                self.driver.get(url)
                time.sleep(1)
                self.close_popup()
                time.sleep(1)

                # Extraer datos usando métodos heredados
                try:
                    nombre = self.extract_name()
                    precio = self.extract_price()
                    print(f"precio {precio}")
                    calificacion = self.extract_rating_details()
                except Exception as e:
                    logger.warning(f"⚠️ {Hotel} ({checkin_str}): {e}")
                    nombre = Hotel
                    precio = "0"
                    calificacion = "No disponible"
                print(f"precio {precio}")
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
                    'check_in': checkin_str,
                    'check_out': checkout_str
                })
            import  pprint as pp
            print(f"results: {pp.pprint(results)}")
            # Avanzar al siguiente día
            fecha_actual = siguiente_dia
            logger.info(f"✅ ✅ pasando a la siguiente fecha: {fecha_actual}")
        return results


def buscar_reservas_adhoc(hoteles: list, check_in: datetime, check_out: datetime, webapp_url: str = os.environ.get('WEBAPP_URL')):
    """
    Función principal para ejecutar el scraper ad-hoc.

    Args:
        hoteles: Lista de hoteles a buscar
        check_in: Fecha inicial
        check_out: Fecha final
        webapp_url: URL opcional para enviar resultados a Google Sheets
    """
    logger.info("🚀 SCRAPING CLIENTES DIARIO AD-HOC")
    logger.info(f"📅 Rango: {check_in.strftime('%Y-%m-%d')} → {check_out.strftime('%Y-%m-%d')}")
    logger.info(f"🏨 Hoteles: {len(hoteles)}")

    driver = None
    try:
        # Crear driver
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        # Ejecutar scraping
        scraper = ClientesDiarioScraperAdHoc(driver, hoteles, check_in, check_out)
        results = scraper.run()

        logger.info(f"📤 Enviando {len(results)} resultados a Sheets")
        enviar_sheets(results, os.environ.get('WEBAPP_URL'), sheet_name='clientes')

        logger.info(f"✅ COMPLETADO: {len(results)} registros")
        return results

    except Exception as e:
        logger.error(f"💥 ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        pass
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # codigo para pruebas unitarias

    # Datos de prueba
    fake_hoteles = [
        {'Hotel': 'Hotel Dann Carlton Bogotá', 'Ciudad': 'Bogotá'},
        {'Hotel': 'Hilton Bogotá Corferias', 'Ciudad': 'Bogotá'},
        {'Hotel': 'Hotel Tequendama', 'Ciudad': 'Bogotá'},
    ]

    # Rango de 3 días desde hoy
    fecha_inicio = datetime.now()
    fecha_fin = datetime.now() + timedelta(days=3)

    # Ejecutar
    resultados = buscar_reservas_adhoc(
        hoteles=fake_hoteles,
        check_in=fecha_inicio,
        check_out=fecha_fin,
        webapp_url=os.environ.get('WEBAPP_URL')
    )

    # Mostrar resultados
    print(f"\n{'=' * 80}")
    print(f"Total de resultados: {len(resultados)}")
    print(f"{'=' * 80}\n")

    for hotel in resultados:
        print(f"🏨 {hotel['nombre']}")
        print(f"   📍 {hotel['ciudad']}")
        print(f"   💰 {hotel['precio']}")
        print(f"   ⭐ {hotel['calificacion']}")
        print(f"   📅 {hotel['check_in']} → {hotel['check_out']}")
        print("-" * 80)