"""
Clase base para scrapers de Booking.com
"""
import time
from typing import List
from abc import ABC, abstractmethod

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from utils.logger import logger
from .data_models import HotelSearchData, HotelResult


class BookingBaseScraper(ABC):
    """Clase base abstracta para scrapers de Booking"""

    BOOKING_BASE_URL = 'https://www.booking.com'

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def search_hotel(self, hotel_data: HotelSearchData, checkin: str, checkout: str) -> HotelResult:
        """
        Busca un hotel y extrae información
        Template Method Pattern
        """
        url = self.build_search_url(hotel_data.hotel, checkin, checkout)
        logger.info(f"🔍 {hotel_data.hotel} ({checkin} → {checkout})")

        self.driver.get(url)
        time.sleep(5)

        self.close_popup()
        time.sleep(2)

        return self.extract_hotel_data(hotel_data, checkin, checkout)

    def build_search_url(self, hotel: str, checkin: str, checkout: str) -> str:
        """Construye URL de búsqueda"""
        url = (
            f'{self.BOOKING_BASE_URL}/searchresults.es.html?'
            f'ss={hotel}'
            f'&checkin={checkin}'
            f'&checkout={checkout}'
            f'&group_adults=2'
            f'&no_rooms=1'
            f'&group_children=0'
            f'&selected_currency=COP'
            f'&changed_currency=1'
            f'&top_currency=1'
        )
        return url

    def close_popup(self):
        """Cierra popup de login si existe"""
        try:
            button = self.driver.find_element(
                By.XPATH,
                '//button[@aria-label="Ignorar información sobre el inicio de sesión."]'
            )
            button.click()
            time.sleep(2)
            logger.debug("Popup cerrado")
        except Exception:
            pass  # No hay popup

    def extract_hotel_data(self, hotel_data: HotelSearchData, checkin: str, checkout: str) -> HotelResult:
        """Extrae datos del hotel de la página"""
        try:
            nombre = self.extract_name()
            precio = self.extract_price()
            calificacion = self.extract_rating()
            logger.info(f"hotel::  {nombre}\n precio:  {precio}\n calificacion:  {calificacion}")
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo: {e}")
            nombre = hotel_data.hotel
            precio = "0"
            calificacion = "No disponible"

        return HotelResult(
            hotel=nombre,
            precio=precio,
            calificacion=calificacion,
            ciudad=hotel_data.ciudad,
            check_in=checkin,
            check_out=checkout
        )

    def extract_name(self) -> str:
        """Extrae nombre del hotel"""
        return self.driver.find_element(
            By.CSS_SELECTOR, '[data-testid="title"]'
        ).text

    def extract_price(self) -> str:
        """Extrae precio con prioridades"""
        # Precio "Desde"
        try:
            element = self.driver.find_element(
                By.CSS_SELECTOR, 'div.abf093bdfe.fc23698243'
            )
            return element.text.replace("Desde ", "").strip()
        except Exception:
            pass

        # Precio con descuento
        try:
            element = self.driver.find_element(
                By.XPATH, '//span[@data-testid="price-and-discounted-price"]'
            )
            return element.text.strip()
        except Exception:
            pass

        # Precio base
        try:
            element = self.driver.find_element(
                By.CSS_SELECTOR, '[data-testid="price"]'
            )
            return element.text.strip()
        except Exception:
            return "0"

    def extract_rating_details(self) -> dict:
        """
        Extrae detalles de calificación usando selectores CSS específicos.

        Returns:
            dict con  'puntuacion', 'calificacion_cualitativa', 'comentarios'
        """
        import re

        puntuacion = "No disponible"
        calificacion_cualitativa = "No disponible"
        comentarios = "0"

        try:
            # Extraer puntuación numérica del div con clase bc946a29db
            # Ejemplo: "Puntuación: 9,9"
            try:
                puntuacion_element = self.driver.find_element(
                    By.CSS_SELECTOR,
                    'div.bc946a29db'
                )
                puntuacion_text = puntuacion_element.text
                # Extraer solo el número (ej: "Puntuación: 9,9" -> "9,9")
                puntuacion_match = re.search(r'(\d+[.,]\d+)', puntuacion_text)
                if puntuacion_match:
                    puntuacion = puntuacion_match.group(1)
                    logger.debug(f"Puntuación extraída: {puntuacion}")
            except Exception as e:
                logger.debug(f"No se pudo extraer puntuación: {e}")


            # Extraer calificación cualitativa "Fantástico" con clases hashed
            try:
                # Opción 1: Selector directo por texto exacto (robusto para cambios de clase)
                calificacion_element = self.driver.find_element(
                    By.XPATH, "//div[contains(text(), 'Fantástico')]"
                )
                calificacion_cualitativa = calificacion_element.text.strip()
                logger.debug(f"Calificación cualitativa extraída: {calificacion_cualitativa}")
            except Exception:
                # Opción 2: Por clases parciales conocidas (si conoces patrón)
                try:
                    calificacion_element = self.driver.find_element(
                        By.CSS_SELECTOR, 'div[class*="f63b14ab7a"], div[class*="f546354b44"]'
                    )
                    calificacion_cualitativa = calificacion_element.text.strip()
                    logger.debug(f"Calificación por clases parciales: {calificacion_cualitativa}")
                except Exception:
                    # Fallback: regex en page_source (tu original mejorado)
                    cualitativa_match = re.search(
                        r'\b(Fantástico|Excelente|Muy\s+bueno|Bueno|Agradable)\b',
                        self.driver.page_source, re.IGNORECASE
                    )
                    if cualitativa_match:
                        calificacion_cualitativa = cualitativa_match.group(1)
                        logger.debug(f"Calificación por regex: {calificacion_cualitativa}")
                    else:
                        logger.debug("No se encontró calificación cualitativa")

            # Extraer número de comentarios
            # Buscar patrones como: "102 comentarios" o "5 comentario" o "1.234 comentarios"
            try:
                comentarios_match = re.search(
                    r'([\d.,]+)\s*comentarios?',
                    self.driver.page_source,
                    re.IGNORECASE
                )
                if comentarios_match:
                    comentarios_raw = comentarios_match.group(1)
                    # Limpiar puntos y comas (ej: "1.234" -> "1234")
                    comentarios = re.sub(r'[.,]', '', comentarios_raw)
                    logger.debug(f"Comentarios extraídos: {comentarios}")
            except Exception as e:
                logger.debug(f"No se pudieron extraer comentarios: {e}")

            return {
                'puntuacion': puntuacion,
                'calificacion_cualitativa': calificacion_cualitativa,
                'comentarios': comentarios
            }

        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo rating: {e}")
            return {
                'puntuacion': "No disponible",
                'calificacion_cualitativa': "No disponible",
                'comentarios': "0"
            }

    @abstractmethod
    def run(self) -> List[dict]:
        """Método abstracto que cada scraper debe implementar"""
        pass