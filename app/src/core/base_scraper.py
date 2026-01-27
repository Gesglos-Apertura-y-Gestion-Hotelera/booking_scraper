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
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo: {e}")
            nombre = hotel_data.hotel
            precio = "0"
            calificacion = "No disponible"

        return HotelResult(
            nombre=nombre,
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

    def extract_rating(self) -> str:
        """Extrae calificación"""
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR, '[data-testid="review-score"]'
            ).text
        except Exception:
            return "No disponible"

    @abstractmethod
    def run(self) -> List[dict]:
        """Método abstracto que cada scraper debe implementar"""
        pass