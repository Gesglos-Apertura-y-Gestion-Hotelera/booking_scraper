#!/usr/bin/env python3
"""
Web Scraping Booking - Scraper Personalizado
Scraping de hoteles en rango de fechas para múltiples ciudades
Lee datos desde variable de entorno SHEET_DATA
"""
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.scraper import BookingBaseScraper
from utils.cleaner import DataCleaner
from utils.logger import logger


class BookingScraperPersonalizado(BookingBaseScraper):
    """
    Scraper personalizado para búsqueda de hoteles por ciudad en rango de fechas
    
    Características:
    - Acepta rango de fechas (check_in, check_out)
    - Itera día por día dentro del rango
    - Procesa múltiples ciudades
    - Compatible con main.py
    """

    def __init__(self, driver, hoteles: list, check_in: datetime, check_out: datetime):
        """
        Inicializa el scraper personalizado
        
        Args:
            driver: WebDriver de Selenium
            hoteles: Lista de diccionarios con información de ciudades
                    Formato esperado: [{'ciudad': 'Bogotá', ...}, ...]
            check_in: Fecha de inicio del rango (datetime)
            check_out: Fecha de fin del rango (datetime)
        """
        super().__init__(driver)
        self.hoteles = hoteles
        
        # Convertir a datetime si vienen como string
        if isinstance(check_in, str):
            self.check_in = datetime.strptime(check_in, '%Y-%m-%d')
        else:
            self.check_in = check_in
            
        if isinstance(check_out, str):
            self.check_out = datetime.strptime(check_out, '%Y-%m-%d')
        else:
            self.check_out = check_out

    def run(self) -> list:
        """
        Ejecuta scraping para todas las ciudades en thodo el rango de fechas
        
        Returns:
            Lista de diccionarios con información de todos los hoteles
        """
        logger.info(f"🚀 INICIANDO SCRAPING PERSONALIZADO")
        logger.info(f"📅 Rango: {self.check_in.strftime('%Y-%m-%d')} → {self.check_out.strftime('%Y-%m-%d')}")
        
        # Extraer ciudades únicas
        ciudades = self.extract_cities()
        
        if not ciudades:
            logger.warning("⚠️ No se encontraron ciudades para procesar")
            return []
        
        # Generar pares de fechas (día a día)
        date_pairs = self.generate_date_range()
        
        if not date_pairs:
            logger.warning("⚠️ No se generaron fechas válidas")
            return []
        
        # Procesar cada ciudad con cada par de fechas
        results = []
        total_searches = len(ciudades) * len(date_pairs)
        current_search = 0
        
        for ciudad in ciudades:
            logger.info(f"\n{'='*60}")
            logger.info(f"🏙️ Procesando ciudad: {ciudad}")
            logger.info(f"{'='*60}")
            
            for checkin_date, checkout_date in date_pairs:
                current_search += 1
                logger.info(f"[{current_search}/{total_searches}] Búsqueda en progreso...")
                
                # Buscar hoteles para esta ciudad y este par de fechas
                hotels = self.search_hotels_for_date(ciudad, checkin_date, checkout_date)
                results.extend(hotels)
                
                # Pequeña pausa entre búsquedas para evitar rate limiting
                time.sleep(2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESUMEN FINAL")
        logger.info(f"{'='*60}")
        logger.info(f"🏙️ Ciudades procesadas: {len(ciudades)}")
        logger.info(f"📅 Días procesados: {len(date_pairs)}")
        logger.info(f"🔍 Búsquedas totales: {total_searches}")
        logger.info(f"🏨 Hoteles encontrados: {len(results)}")
        logger.info(f"{'='*60}\n")
        
        return results
