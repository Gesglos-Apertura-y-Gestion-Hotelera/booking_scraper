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
            logger.info(f"hotel ciudad: {hotel_ciudad}, ciudad: {ciudad}, hotel: {hotel}, checkin: {checkin}, checkout: {checkout}")
            url = self.build_search_url(search_term=hotel_ciudad, checkin=checkin, checkout=checkout)
            self.open_url(url)

            try:
                nombre = self.extract_name()
            except Exception as e:
                logger.warning(f"⚠️ [{hotel}] Falló extracción de NOMBRE: {e}")
                nombre = "no disponible"

            try:
                precio = self.extract_price()
            except Exception as e:
                logger.warning(f"⚠️ [{hotel}] Falló extracción de PRECIO: {e}")
                precio = "no disponible"

            try:
                review_promedio = self.extract_calificacion_cualitativa()
            except Exception as e:
                logger.warning(f"⚠️ [{hotel}] Falló extracción de REVIEW_PROMEDIO: {e}")
                review_promedio = "no disponible"
            try:
                opiniones = self.extract_comentarios()
            except Exception as e:
                logger.warning(f"⚠️ [{hotel}] Falló extracción de OPINIONES: {e}")
                opiniones = "no disponible"

            try:
                puntuacion = self.extract_puntuacion()
            except Exception as e:
                logger.warning(f"⚠️ [{hotel}] Falló extracción de PUNTUACION: {e}")
                puntuacion = "no disponible"

            cleaner = DataCleaner()
            divisa, precio = cleaner.limpiar_precio(precio)
            results.append({
                'hotel': nombre,
                'divisa': divisa,
                'precio': precio,
                'review_promedio': review_promedio,
                'opiniones': opiniones,
                'puntuacion': puntuacion,
                'ciudad': ciudad,
                'check_in': checkin,
                'check_out': checkout
            })

        return results
