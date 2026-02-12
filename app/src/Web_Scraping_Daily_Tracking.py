#!/usr/bin/env python3
"""
Web Scraping Daily Tracking
Scraping de hoteles por ciudad para seguimiento diario
Lee datos de ciudades desde variable de entorno SHEET_DATA
"""
from datetime import datetime, timedelta
from typing import List, Set

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.scraper import BookingBaseScraper
from utils.logger import logger


class DailyTrackingScraper(BookingBaseScraper):
    """Scraper para seguimiento diario de hoteles por ciudad"""

    def __init__(self, driver, hoteles: list):
        """
        Inicializa el scraper de seguimiento diario

        Args:
            driver: WebDriver de Selenium
            hoteles: Lista de diccionarios con información de ciudades
                    Formato esperado: [{'ciudad': 'Bogotá', ...}, ...]
        """
        super().__init__(driver)
        self.hoteles = hoteles

    def extract_cities(self) -> List[str]:
        """
        Extrae ciudades únicas de la lista de hoteles
        Toma solo el texto antes de la coma y elimina duplicados

        Returns:
            Lista de ciudades únicas procesadas
        """
        ciudades: Set[str] = set()

        for hotel_data in self.hoteles:
            if not isinstance(hotel_data, dict):
                logger.warning(f"⚠️ Elemento no es dict: {type(hotel_data)}")
                continue

            # Intentar obtener ciudad con diferentes formatos de clave
            ciudad = hotel_data.get('ciudad') or hotel_data.get('Ciudad') or ''

            if ciudad and isinstance(ciudad, str):
                # Tomar solo el texto antes de la coma
                ciudad_limpia = ciudad.split(",")[0].strip()
                if ciudad_limpia:
                    ciudades.add(ciudad_limpia)

        ciudades_lista = sorted(list(ciudades))
        logger.info(f"🏙️ Ciudades únicas encontradas: {len(ciudades_lista)}")
        logger.info(f"📍 Ciudades: {', '.join(ciudades_lista)}")

        return ciudades_lista


    def run(self) -> list:
        """
        Ejecuta scraping para todas las ciudades

        Returns:
            Lista de diccionarios con información de todos los hoteles
        """
        checkin = datetime.now().strftime('%Y-%m-%d')
        checkout = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        logger.info(f"📅 Check-in: {checkin} | Check-out: {checkout}")

        # Extraer ciudades únicas
        ciudades = self.extract_cities()

        if not ciudades:
            logger.warning("⚠️ No se encontraron ciudades para procesar")
            return []

        # Procesar cada ciudad
        results = []
        for ciudad in ciudades:
            city_hotels = self.extract_hotels_from_city(ciudad, checkin, checkout)
            results.extend(city_hotels)

        logger.info(f"📊 Total de hoteles extraídos: {len(results)}")

        return results
