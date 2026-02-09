#!/usr/bin/env python3
"""
Web Scraping Booking - Scraper Personalizado
Scraping de hoteles en rango de fechas para múltiples ciudades
Lee datos desde variable de entorno SHEET_DATA
"""
import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from core.scraper import BookingBaseScraper
from utils.cleaner import DataCleaner
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
        url = self.build_search_url(ciudad, checkin_str, checkout_str)
        
        hotels_data = []
        
        try:
            self.open_url(url)
            
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

    def extract_hotel_info_from_card(self, hotel_element, ciudad: str, checkin: str, checkout: str) -> Dict:
        """
        Orquestador principal que delega cada responsabilidad a métodos específicos.
        """
        hotel_data = {}

        # Cada responsabilidad en su propio método
        hotel_data['hotel'] = self._extract_hotel_name(hotel_element)
        hotel_data['precio'], hotel_data['divisa'] = self._extract_price_info(hotel_element)
        hotel_data['puntuacion'] = self._extract_rating_score(hotel_element)
        hotel_data['review_promedio'] = self._extract_review_text(hotel_element)
        hotel_data['comentarios'] = self._extract_reviews_count(hotel_element)

        # Información contextual
        hotel_data['ciudad'] = ciudad
        hotel_data['check_in'] = checkin
        hotel_data['check_out'] = checkout

        return hotel_data

    def _extract_hotel_name(self, hotel_element) -> str:
        """Extrae el nombre del hotel desde la tarjeta."""
        try:
            nombre_element = hotel_element.find_element(By.CSS_SELECTOR, '[data-testid="title"]')
            name = nombre_element.text.strip()
            return name
        except NoSuchElementException:
            logger.warning("⚠️ Nombre del hotel no encontrado")
            return "No disponible"

    def _extract_price_info(self, hotel_element) -> tuple[str, str | int]:
        """Extrae precio con selectores prioritarios más específicos."""
        price_selectors = [
            '[data-testid="price-and-discounted-price"]',  # Precio tachado/descuento
            '[data-testid="taxes-and-charges"] + div .bc946a29db',  # JUSTO después de impuestos
            '.bc946a29db:has-text("Precio")',  # Contiene "Precio"
            '[data-testid="availability-rate-information"] .bc946a29db',  # Dentro del contenedor de precio
        ]

        for selector in price_selectors:
            try:
                precio_element = hotel_element.find_element(By.CSS_SELECTOR, selector)
                precio_raw = precio_element.text.strip()

                # Filtrar textos no-numéricos
                if self._is_valid_price_text(precio_raw):
                    cleaner = DataCleaner()
                    divisa, precio = cleaner.limpiar_precio(precio_raw)
                    return str(precio), divisa

            except NoSuchElementException:
                logger.error(f"PRECIO NO ENCONTRADO: '{precio_raw}' → {divisa} {precio}")
                continue

        logger.warning("⚠️ Ningún selector de precio funcionó")
        return "No disponible", "No disponible"

    def _is_valid_price_text(self, text: str) -> bool:
        """Valida que el texto contenga un precio real."""
        # Debe contener números + COP o símbolo de moneda
        price_pattern = r'(COP|USD|€|\$|\d+[.,]\d{3})'
        return bool(re.search(price_pattern, text, re.IGNORECASE))

    def _extract_hotel_name(self, hotel_element) -> str:
        """Extrae nombre evitando 'Se abre en una ventana nueva'."""
        try:
            # Selector MÁS ESPECÍFICO: data-testid="title" DENTRO del link del título
            title_link = hotel_element.find_element(By.CSS_SELECTOR, '[data-testid="title-link"]')
            nombre_element = title_link.find_element(By.CSS_SELECTOR, '[data-testid="title"]')
            name = nombre_element.text.strip()

            # Filtrar texto no deseado
            if "Se abre" in name or len(name) < 3:
                raise NoSuchElementException("Texto inválido")

            return name
        except NoSuchElementException:
            logger.warning("⚠️ Nombre del hotel no encontrado")
            return "No disponible"

    def _extract_rating_score(self, hotel_element) -> str:
        """Extrae puntuación con selector + fallback regex ultra-robusto."""

        # 🎯 1. Selector directo (funciona cuando hay puntuación)
        try:
            puntuacion_element = hotel_element.find_element(
                By.CSS_SELECTOR, '[data-testid="review-score"]'
            )
            puntuacion_raw = puntuacion_element.text.strip()

            # Extraer el PRIMER número decimal
            puntuacion = re.search(r'(\d+[,.]\d+|\d+)', puntuacion_raw)
            if puntuacion:
                clean_score = puntuacion.group(1).replace(',', '.')
                return clean_score

        except NoSuchElementException:
            logger.error("❌ No [data-testid='review-score'] - Probando fallback")

        # 🎯 2. FALLBACK: Regex directo en todo el texto de la card
        try:
            card_text = hotel_element.text
            # Busca "Puntuación: X,X" o solo "X,X" cerca de palabras clave
            match = re.search(r'Puntuaci[oó]n[:\s]*(\d+[,.]\d+|\d+)', card_text)
            if match:
                puntuacion = match.group(1).replace(',', '.')
                return puntuacion
        except:
            pass

        # 🎯 3. ULTIMO RESORTE: "Nuevo en Booking.com" = Sin puntuación
        if "Nuevo en Booking.com" in hotel_element.text:
            return "Hotel Nuevo: No Score"

        logger.warning("⚠️ Puntuación no encontrada")
        return "No disponible"

    def _extract_review_text(self, hotel_element) -> str:
        """Extrae la calificación cualitativa (Fantástico, Excelente, etc.)."""
        try:
            review_element = hotel_element.find_element(
                By.CSS_SELECTOR,
                '.becbee2f63'
            )
            review = review_element.text.strip()
            return review
        except NoSuchElementException:
            logger.warning("⚠️ Review cualitativo no encontrado")
            return "No disponible"

    def _extract_reviews_count(self, hotel_element) -> str:
        """Extrae el número de comentarios/reviews."""
        return self._extract_reviews_from_card(hotel_element)

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
