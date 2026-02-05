"""
Clase base para scrapers de Booking.com
"""
import json
import re
import time
from abc import ABC, abstractmethod
from typing import List, Dict

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from utils.cleaner import DataCleaner
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
            logger.info(f"1 falló extraccion de precio")
            pass
        
        try:
            element = self.driver.find_element(
                By.CSS_SELECTOR, 'div.fff1944c52.e1ca2942a5'
            )
            element = element.text.replace("Desde ", "").strip()
            return element.text.replace(".", "").strip()
        except Exception:
            logger.info(f"2 falló extraccion de precio")
            pass

        # Precio con descuento
        try:
            element = self.driver.find_element(
                By.XPATH, '//span[@data-testid="price-and-discounted-price"]'
            )
            return element.text.strip()
        except Exception:
            logger.info(f"3 falló extraccion de precio")
            pass

        # Precio base
        try:
            element = self.driver.find_element(
                By.CSS_SELECTOR, '[data-testid="price"]'
            )
            return element.text.strip()
        except Exception:
            logger.info(f"4 falló extraccion de precio")
            return "0"

    def extract_puntuacion(self) -> str:
        """
        Extrae la puntuación numérica del hotel.

        Returns:
            str: Puntuación (ej: "9,9") o "No disponible"
        """
        import re

        try:
            puntuacion_element = self.driver.find_element(
                By.CSS_SELECTOR,
                'div.bc946a29db'
            )
            puntuacion_text = puntuacion_element.text
            logger.info(f"1 ⚠️ ⚠️ ⚠️puntuacion: {puntuacion_text}")
            # Extraer solo el número (ej: "Puntuación: 9,9" -> "9,9")
            puntuacion_match = re.search(r'(\d+[.,]\d+)', puntuacion_text)
            if puntuacion_match:
                puntuacion = puntuacion_match.group(1)
                logger.debug(f"Puntuación extraída: {puntuacion}")
                return puntuacion

        except Exception as e:
            logger.debug(f"No se pudo extraer puntuación: {e}")

        try:
            puntuacion_element = self.driver.find_element(
                By.CSS_SELECTOR,
                'div.f63b14ab7a.dff2e52086'

            )
            puntuacion_text = puntuacion_element.text
            logger.info(f"2 ⚠️ ⚠️ ⚠️puntuacion: {puntuacion_text}")
            # Extraer solo el número (ej: "Puntuación: 9,9" -> "9,9")
            puntuacion_match = re.search(r'(\d+[.,]\d+)', puntuacion_text)
            if puntuacion_match:
                puntuacion = puntuacion_match.group(1)
                logger.debug(f"Puntuación extraída: {puntuacion}")
                return puntuacion

        except Exception as e:
            logger.debug(f"No se pudo extraer puntuación: {e}")
            return "No disponible"

    def extract_calificacion_cualitativa(self) -> str:
        """
        Extrae la calificación cualitativa del hotel.

        Returns:
            str: Calificación (ej: "Fantástico", "Excelente") o "No disponible"
        """
        import re

        # Opción 1: Selector directo por texto exacto
        try:
            calificacion_element = self.driver.find_element(
                By.XPATH,
                "//div[contains(text(), 'Fantástico') or contains(text(), 'Excelente') or "
                "contains(text(), 'Muy bueno') or contains(text(), 'Bueno') or "
                "contains(text(), 'Agradable')]"
            )

            calificacion = calificacion_element.text.strip()
            if calificacion is not None:

                calificacion_match = re.search(r"(\w+\S\w+)\:", calificacion, re.IGNORECASE)
                calificacion_str = calificacion_match.group(1)
                cleaner = DataCleaner()
                calificacion = cleaner.quitar_tildes(calificacion_str)
                logger.info(f"1 ⚠️ ⚠️️ ⚠️ calificacion: {calificacion}")
                logger.debug(f"Calificación cualitativa extraída: {calificacion}")
                return calificacion
        except Exception as e:
            logger.error(f"ERROR: extraer calificacion ha fallado {e}")
            pass

        # Opción 2: Por clases parciales conocidas
        try:
            calificacion_element = self.driver.find_element(
                By.CSS_SELECTOR,
                'div.f63b14ab7a.f546354b44'
            )
            calificacion = calificacion_element.text.strip()
            logger.info(f"2 ⚠️️ ⚠️ ⚠️ calificacion: {calificacion}")
            logger.debug(f"Calificación por clases parciales: {calificacion}")
            if calificacion is not None:
                return calificacion
        except Exception:
            pass

        # Opción 2.5: Por clases parciales conocidas
        try:
            calificacion_element = self.driver.find_element(
                By.CSS_SELECTOR,
                'div[class="f63b14ab7a f546354b44 becbee2f63"]'
            )
            calificacion = calificacion_element.text.strip()
            logger.info(f"3 ⚠️ ⚠️ ⚠️ calificacion: {calificacion}")
            logger.debug(f"Calificación por clases parciales: {calificacion}")
            if calificacion is not None:
                return calificacion
        except Exception:
            pass

        # Opción 3: Fallback con regex en page_source
        try:
            cualitativa_match = re.search(
                r'\b(Fantástico|Excelente|Muy\s+bueno|Bueno|Agradable|Fabuloso|Excepcional|Sobresaliente)\b',
                self.driver.page_source,
                re.IGNORECASE
            )
            if cualitativa_match:
                calificacion = cualitativa_match.group(1)
                logger.debug(f"4️ ⚠️️ ⚠️️ ⚠️ Calificación por regex: {calificacion}")
                return calificacion
        except Exception:
            pass

        logger.debug("No se encontró calificación cualitativa")
        return "No disponible"

    def extract_comentarios(self) -> str:
        """
        Extrae el número de comentarios/reviews del hotel.

        Returns:
            str: Número de comentarios (ej: "102") o "0"
        """
        import re
        try:
            comentarios_matches = self.driver.find_element(
                By.CSS_SELECTOR,
                'div[class="fff1944c52 fb14de7f14 eaa8455879"]'
            )
            comentarios = comentarios_matches.text.strip()
            comentarios.replace("comentarios", "")
            comentarios = re.sub(r"\s*comentarios", "", comentarios)
            comentarios = re.sub(r'[.,]', '', comentarios)
            logger.info(f"3 ⚠️ ⚠️ ⚠️ Coments: {comentarios}")
            logger.debug(f"coments por clases parciales: {comentarios}")
            if comentarios is not None:
                return comentarios
        except Exception:
            pass

        try:
            comentarios_matches = re.findall(
                r'\b(\d{1,3}(?:[.,]\d{3})*|\d{1,6})\s*comentarios?\b',
                self.driver.page_source,
                re.IGNORECASE
            )
            if comentarios_matches and len(comentarios_matches) > 1:
                comentarios_raw = comentarios_matches[1]  # Segunda coincidencia
                comentarios = re.sub(r'[.,]', '', comentarios_raw)
                logger.debug(f"Comentarios extraídos (2da match): {comentarios}")
                if comentarios is not None:
                    return comentarios
        except Exception as e:
            logger.debug(f"No se pudieron extraer comentarios: {e}")

        return "0"

    def extract_rating_details(self) -> dict:
        """
        Extrae detalles completos de calificación del hotel.
        Orquesta las 3 funciones de extracción específicas.

        Returns:
            dict con 'puntuacion', 'calificacion_cualitativa', 'comentarios'
        """
        try:
            returned = {
                'puntuacion': self.extract_puntuacion(),
                'calificacion_cualitativa': self.extract_calificacion_cualitativa(),
                'comentarios': self.extract_comentarios()
            }
            logger.info(f"extract_rating_details: {json.dumps(returned)}")
            return returned
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo rating: {e}")
            return {
                'puntuacion': "No disponible",
                'calificacion_cualitativa': "No disponible",
                'comentarios': "0"
            }

    def extract_hotels_from_city(self, ciudad: str, checkin: str, checkout: str) -> List[Dict]:
        """
        Extrae información de todos los hoteles disponibles en una ciudad

        Args:
            ciudad: Nombre de la ciudad
            checkin: Fecha de check-in
            checkout: Fecha de check-out

        Returns:
            Lista de diccionarios con información de hoteles
        """
        logger.info(f"🏨 Procesando ciudad: {ciudad}")

        url = self.build_city_search_url(ciudad, checkin, checkout)
        logger.info(f"URL: {url}")

        hotels_data = []

        try:
            # Cargar página
            self.driver.get(url)
            time.sleep(5)

            # Cerrar popup si aparece
            self.close_popup()
            time.sleep(2)

            # Buscar todos los elementos de hoteles
            hotels_elements = self.driver.find_elements(
                By.XPATH,
                '//div[@data-testid="property-card"]'
            )

            if not hotels_elements:
                logger.warning(f"⚠️ No se encontraron hoteles para {ciudad}")
                return hotels_data

            logger.info(f"📊 Encontrados {len(hotels_elements)} hoteles en {ciudad}")

            # Extraer información de cada hotel
            for hotel_element in hotels_elements:
                hotel_info = self._extract_hotel_info(hotel_element, ciudad, checkin, checkout)
                if hotel_info:
                    hotels_data.append(hotel_info)

            logger.info(f"✅ {ciudad}: {len(hotels_data)} hoteles procesados")

        except Exception as e:
            logger.error(f"❌ Error procesando {ciudad}: {e}")

        return hotels_data

    def _extract_reviews_count(self, hotel_element) -> str:
        """
        Extrae el número de comentarios usando múltiples estrategias

        Args:
            hotel_element: Elemento WebDriver del hotel

        Returns:
            Número de comentarios como string, "0" si no se encuentra
        """
        # Estrategia 1: Buscar en la estructura típica de review-score
        try:
            reviews_text = hotel_element.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]/div[2]/div[2]'
            ).text

            # Extraer número con regex (más robusto que split)
            match = re.search(r'(\d+(?:\.\d+)?)', reviews_text)
            if match:
                return match.group(1)
        except NoSuchElementException:
            pass

        # Estrategia 2: Buscar en toda la sección de review-score
        try:
            review_section = hotel_element.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]'
            )

            # Buscar texto que contenga "comentarios" o "opiniones"
            review_text = review_section.text

            # Regex para encontrar número antes de "comentarios" u "opiniones"
            match = re.search(r'(\d+(?:\.\d+)?)\s*(?:comentarios|opiniones|reviews)',
                              review_text, re.IGNORECASE)
            if match:
                return match.group(1)
        except NoSuchElementException:
            pass

        # Estrategia 3: Buscar cualquier elemento que contenga "comentarios"
        try:
            reviews_element = hotel_element.find_element(
                By.XPATH,
                './/*[contains(text(), "comentarios") or contains(text(), "opiniones")]'
            )

            reviews_text = reviews_element.text

            # Extraer el número usando regex
            match = re.search(r'(\d+(?:\.\d+)?)', reviews_text)
            if match:
                return match.group(1)
        except NoSuchElementException:
            pass

        # Si ninguna estrategia funcionó, retornar "0"
        logger.debug("No se pudieron extraer comentarios, retornando '0'")
        return "0"

    def _extract_hotel_info(
            self,
            hotel_element,
            ciudad: str,
            checkin: str,
            checkout: str
    ) -> Dict:
        """
        Extrae información de un elemento de hotel individual

        Args:
            hotel_element: Elemento WebDriver del hotel
            ciudad: Nombre de la ciudad
            checkin: Fecha de check-in
            checkout: Fecha de check-out

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

        # Precio (intentar con descuento primero, luego precio base)
        try:
            precio_raw = hotel_element.find_element(
                By.XPATH,
                './/span[@data-testid="price-and-discounted-price"]'
            ).text
        except NoSuchElementException:
            try:
                precio_raw = hotel_element.find_element(
                    By.XPATH,
                    './/span[@data-testid="price"]'
                ).text
            except NoSuchElementException:
                precio_raw = "0"

        # Limpiar precio
        cleaner = DataCleaner()
        divisa, precio = cleaner.limpiar_precio(precio_raw)
        hotel_data['divisa'] = divisa
        hotel_data['precio'] = precio

        # Puntuación numérica
        try:
            hotel_data['puntuacion'] = hotel_element.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]/div[1]'
            ).text
        except NoSuchElementException:
            hotel_data['puntuacion'] = "No disponible"

        # Reseña promedio (calificación cualitativa)
        try:
            hotel_data['review_promedio'] = hotel_element.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]/div[2]/div[1]'
            ).text
        except NoSuchElementException:
            hotel_data['review_promedio'] = "No disponible"

        # Número de comentarios - Estrategia robusta
        hotel_data['comentarios'] = self._extract_reviews_count(hotel_element)

        # Agregar información contextual
        hotel_data['ciudad'] = ciudad
        hotel_data['check_in'] = checkin
        hotel_data['check_out'] = checkout

        return hotel_data

    def build_city_search_url(self, ciudad: str, checkin: str, checkout: str) -> str:
        """
        Construye URL de búsqueda para una ciudad específica

        Args:
            ciudad: Nombre de la ciudad
            checkin: Fecha de check-in (YYYY-MM-DD)
            checkout: Fecha de check-out (YYYY-MM-DD)

        Returns:
            URL completa de búsqueda
        """
        base_url = "https://www.booking.com/searchresults.es.html"
        params = [
            f"ss={ciudad}",
            f"checkin={checkin}",
            f"checkout={checkout}",
            f"group_adults=2",
            f"no_rooms=1",
            f"group_children=0"
        ]
        return f"{base_url}?{'&'.join(params)}"

    @abstractmethod
    def run(self) -> List[dict]:
        """Método abstracto que cada scraper debe implementar"""
        pass