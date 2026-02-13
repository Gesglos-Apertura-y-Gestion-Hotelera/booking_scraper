#!/usr/bin/env python3
"""
Web Scraping Competencia Diario
Scraping diario de precios de competidores en Booking.com
"""
import re

from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from utils.cleaner import DataCleaner
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
        checkin_str = datetime.now().strftime('%Y-%m-%d')
        checkout_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        logger.info(f"📅 Check-in: {checkin_str} | Check-out: {checkout_str}")
        cleaner = DataCleaner()
        results = []
        for comp_data in self.competidores:
            if not isinstance(comp_data, dict):
                logger.error(f"❌ Elemento no es dict: {type(comp_data)}")
                continue

            # Normalizar claves (mayúsculas o minúsculas)
            competidor = comp_data.get('competidor') or comp_data.get('Competidor') or ''
            ciudad = comp_data.get('ciudad') or comp_data.get('Ciudad') or ''
            hotel = comp_data.get('hotel') or comp_data.get('Hotel') or ''

            if not competidor or not ciudad:
                logger.warning(f"⚠️ Datos incompletos: {comp_data}")
                continue

            # Construir búsqueda: "Nombre Competidor Ciudad"
            competidor_ciudad = f"{competidor} - {ciudad}"
            competidor_ciudad = re.sub(r"\s{1,10}", "+", competidor_ciudad)

            url = self.build_search_url(competidor_ciudad, checkin_str, checkout_str)

            self.open_url(url)

            # Extraer datos usando métodos heredados
            try:
                nombre_competidor = self.extract_name()
                precio = self.extract_price()
                puntuacion = self.extract_puntuacion()
                calificacion_cualitativa = self.extract_calificacion_cualitativa()
                comentarios = self.extract_comentarios()
            except Exception as e:
                logger.warning(f"⚠️ {competidor} ({checkin_str}): {e}")
                nombre_competidor = competidor
                precio = "0"
                calificacion_cualitativa = "No disponible"
                puntuacion = "0"
                comentarios = "No disponible"

            divisa, precio = cleaner.limpiar_precio(precio)
            results.append({
                'hotel': hotel,
                'divisa': divisa,
                'precio': precio,
                'review_promedio': calificacion_cualitativa,
                'comentarios': comentarios,
                'puntuacion': puntuacion,
                'competidor': nombre_competidor,
                'ciudad': ciudad,
                'check_in': checkin_str,
                'check_out': checkout_str
            })

        return results
