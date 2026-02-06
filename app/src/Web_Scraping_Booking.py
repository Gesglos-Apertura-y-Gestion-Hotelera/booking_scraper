#!/usr/bin/env python3
"""
Web Scraping Booking - Scraper Personalizado
Scraping de hoteles en rango de fechas para múltiples ciudades
Lee datos desde variable de entorno SHEET_DATA
"""
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.cleaner import DataCleaner
from utils.enviar_sheets import enviar_sheets
from utils.get_sheet_data import get_sheet_data
from utils.logger import logger


WEBAPP_URL = os.environ.get('WEBAPP_URL')


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

    def extract_cities(self) -> List[str]:
        """
        Extrae ciudades únicas de la lista de hoteles
        
        Returns:
            Lista de ciudades únicas procesadas
        """
        ciudades = set()
        
        for hotel_data in self.hoteles:
            if not isinstance(hotel_data, dict):
                logger.warning(f"⚠️ Elemento no es dict: {type(hotel_data)}")
                continue
            
            # Intentar obtener ciudad con diferentes formatos de clave
            ciudad = hotel_data.get('ciudad') or hotel_data.get('Ciudad') or ''
            
            if ciudad and isinstance(ciudad, str):
                # Tomar solo el texto antes de la coma si existe
                ciudad_limpia = ciudad.split(",")[0].strip()
                if ciudad_limpia:
                    ciudades.add(ciudad_limpia)
        
        ciudades_lista = sorted(list(ciudades))
        logger.info(f"🏙️ Ciudades únicas encontradas: {len(ciudades_lista)}")
        logger.info(f"📍 Ciudades: {', '.join(ciudades_lista)}")
        
        return ciudades_lista

    def generate_date_range(self) -> List[tuple]:
        """
        Genera lista de tuplas (check_in, check_out) para cada día del rango
        
        Returns:
            Lista de tuplas con fechas consecutivas
            Ejemplo: [(2026-02-05, 2026-02-06), (2026-02-06, 2026-02-07), ...]
        """
        date_pairs = []
        current_date = self.check_in
        
        while current_date < self.check_out:
            next_date = current_date + timedelta(days=1)
            date_pairs.append((current_date, next_date))
            current_date = next_date
        
        logger.info(f"📅 Rango de fechas generado: {len(date_pairs)} días")
        logger.info(f"   Desde: {self.check_in.strftime('%Y-%m-%d')}")
        logger.info(f"   Hasta: {self.check_out.strftime('%Y-%m-%d')}")
        
        return date_pairs

    def search_hotels_for_date(
        self, 
        ciudad: str, 
        checkin_date: datetime, 
        checkout_date: datetime
    ) -> List[Dict]:
        """
        Busca hoteles para una ciudad y un par de fechas específico
        
        Args:
            ciudad: Nombre de la ciudad
            checkin_date: Fecha de check-in
            checkout_date: Fecha de check-out
            
        Returns:
            Lista de diccionarios con información de hoteles
        """
        checkin_str = checkin_date.strftime('%Y-%m-%d')
        checkout_str = checkout_date.strftime('%Y-%m-%d')
        
        logger.info(f"🔍 {ciudad} | {checkin_str} → {checkout_str}")
        
        # Construir URL de búsqueda
        url = self.build_city_search_url(ciudad, checkin_str, checkout_str)
        
        hotels_data = []
        
        try:
            # Cargar página
            self.driver.get(url)
            time.sleep(1)
            
            # Cerrar popup si aparece
            self.close_popup()
            time.sleep(1)
            
            # Buscar todos los elementos de hoteles
            hotels_elements = self.driver.find_elements(
                By.XPATH, 
                '//div[@data-testid="property-card"]'
            )
            
            if not hotels_elements:
                logger.warning(f"⚠️ No se encontraron hoteles para {ciudad} en {checkin_str}")
                return hotels_data
            
            logger.debug(f"📊 Encontrados {len(hotels_elements)} hoteles")
            
            # Extraer información de cada hotel
            for hotel_element in hotels_elements:
                hotel_info = self.extract_hotel_info_from_card(
                    hotel_element, 
                    ciudad, 
                    checkin_str, 
                    checkout_str
                )
                if hotel_info:
                    hotels_data.append(hotel_info)
            
            logger.info(f"✅ {len(hotels_data)} hoteles procesados")
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda {ciudad} {checkin_str}: {e}")
        
        return hotels_data

    def extract_hotel_info_from_card(
        self, 
        hotel_element, 
        ciudad: str, 
        checkin: str, 
        checkout: str
    ) -> Dict:
        """
        Extrae información de un elemento de hotel (property-card)
        
        Args:
            hotel_element: Elemento WebDriver del hotel
            ciudad: Nombre de la ciudad
            checkin: Fecha de check-in (YYYY-MM-DD)
            checkout: Fecha de check-out (YYYY-MM-DD)
            
        Returns:
            Diccionario con información del hotel
        """
        hotel_data = {}
        
        # Nombre del hotel
        try:
            hotel_data['hotel'] = hotel_element.find_element(
                By.XPATH, 
                './/div[@data-testid="title"]'
            ).text
        except NoSuchElementException:
            hotel_data['hotel'] = "No disponible"
        
        # Precio - Estrategia con múltiples fallbacks
        precio_raw = self._extract_price_from_card(hotel_element)
        
        # Limpiar precio
        cleaner = DataCleaner()
        divisa, precio = cleaner.limpiar_precio(precio_raw)
        hotel_data['divisa'] = divisa
        hotel_data['precio'] = precio
        
        # Puntuación numérica
        try:
            puntuacion = hotel_element.find_element(
                By.XPATH, 
                './/div[@data-testid="review-score"]/div[1]'
            ).text
            import re
            puntuacion = re.findall(r'\d+[,.]?\d*', puntuacion)[0]


            hotel_data['puntuacion'] = puntuacion
        except NoSuchElementException:
            hotel_data['puntuacion'] = "No disponible"
        
        # Reseña promedio (calificación cualitativa)
        try:
            review = hotel_element.find_element(
                By.XPATH, 
                './/div[@data-testid="review-score"]/div[2]/div[1]'
            ).text
            logger.info(f"✅ ✅ ✅ ✅ ✅ ✅ Review: {review}")
            hotel_data['review_promedio'] = review
        except NoSuchElementException:
            hotel_data['review_promedio'] = "No disponible"
        
        # Número de comentarios usando estrategia robusta heredada
        hotel_data['comentarios'] = self._extract_reviews_count(hotel_element)
        
        # Agregar información contextual
        hotel_data['ciudad'] = ciudad
        hotel_data['check_in'] = checkin
        hotel_data['check_out'] = checkout
        
        return hotel_data

    def _extract_price_from_card(self, hotel_element) -> str:
        """
        Extrae precio con múltiples estrategias de fallback
        
        Args:
            hotel_element: Elemento WebDriver del hotel
            
        Returns:
            Precio como string, "0" si no se encuentra
        """
        # Estrategia 1: Precio con descuento
        try:
            precio = hotel_element.find_element(
                By.XPATH, 
                './/span[@data-testid="price-and-discounted-price"]'
            ).text
            return precio
        except NoSuchElementException:
            pass
        
        # Estrategia 2: Precio alternativo
        try:
            precio = hotel_element.find_element(
                By.XPATH, 
                './/span[@data-testid="price-alternative"]'
            ).text
            return precio
        except NoSuchElementException:
            pass
        
        # Estrategia 3: Precio base
        try:
            precio = hotel_element.find_element(
                By.XPATH, 
                './/span[@data-testid="price"]'
            ).text
            return precio
        except NoSuchElementException:
            pass
        
        # Si ninguna estrategia funcionó
        logger.debug("No se pudo extraer precio de la card")
        return "0"

    def run(self) -> list:
        """
        Ejecuta scraping para todas las ciudades en todo el rango de fechas
        
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


def buscar_hoteles_personalizado():
    """
    Función standalone para ejecutar el scraper personalizado
    Requiere variables de entorno: SHEET_DATA, CHECK_IN, CHECK_OUT
    """
    logger.info("🚀 SCRAPING PERSONALIZADO DE BOOKING")

    driver = None
    try:
        # Obtener datos de ciudades
        hoteles = get_sheet_data()
        
        if not hoteles:
            logger.error("❌ No hay datos de ciudades para procesar")
            sys.exit(1)
        
        # Obtener fechas desde variables de entorno
        check_in_str = os.environ.get('CHECK_IN')
        check_out_str = os.environ.get('CHECK_OUT')
        
        if not check_in_str or not check_out_str:
            logger.error("❌ Se requieren las variables CHECK_IN y CHECK_OUT")
            logger.error("   Ejemplo: CHECK_IN='2026-02-05' CHECK_OUT='2026-02-10'")
            sys.exit(1)
        
        # Convertir strings a datetime
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d')
        
        # Validar rango
        if check_in >= check_out:
            logger.error("❌ CHECK_IN debe ser anterior a CHECK_OUT")
            sys.exit(1)

        # Ejecutar scraping
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        scraper = BookingScraperPersonalizado(driver, hoteles, check_in, check_out)
        results = scraper.run()

        # Enviar a Sheets
        logger.info(f"📤 Enviando {len(results)} resultados a Google Sheets")
        enviar_sheets(results, WEBAPP_URL, sheet_name='cliente')

        logger.info(f"✅ COMPLETADO: {len(results)} hoteles procesados")

    except Exception as e:
        logger.error(f"💥 ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if driver:
            logger.info("🔌 Cerrando driver...")
            driver.quit()


if __name__ == "__main__":
    # Código para pruebas unitarias
    buscar_hoteles_personalizado()
