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
                self.open_url(url)

                # Extraer datos usando métodos heredados
                try:
                    nombre = self.extract_name()
                    precio = self.extract_price()
                    calificacion = self.extract_rating_details()
                except Exception as e:
                    logger.warning(f"⚠️ {Hotel} ({checkin_str}): {e}")
                    nombre = Hotel
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
                    'check_in': checkin_str,
                    'check_out': checkout_str
                })

            fecha_actual = siguiente_dia
            logger.info(f"✅ ✅ pasando a la siguiente fecha: {fecha_actual}")
        return results
