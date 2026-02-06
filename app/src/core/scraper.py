"""
Clase base para scrapers de Booking.com
Versión optimizada - Elimina redundancias y consolida lógica común
"""
import json
import re
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from utils.cleaner import DataCleaner
from utils.logger import logger
from .data_models import HotelSearchData, HotelResult


class BookingBaseScraper(ABC):
    """Clase base abstracta para scrapers de Booking"""

    BOOKING_BASE_URL = 'https://www.booking.com'
    
    # Palabras clave para calificaciones cualitativas
    QUALITATIVE_KEYWORDS = [
        'Fantástico', 'Excelente', 'Muy bueno', 'Bueno', 'Agradable',
        'Fabuloso', 'Excepcional', 'Sobresaliente'
    ]

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.cleaner = DataCleaner()

    # ============================================================
    # MéthodoS GENÉRICOS DE EXTRACCIÓN (CORE)
    # ============================================================

    def _try_extract(
        self, 
        element_or_driver,
        selectors: List[Tuple[str, str]],
        extract_fn=None,
        default: str = ""
    ) -> str:
        """
        Méthodo genérico para intentar extraer con múltiples selectores
        
        Args:
            element_or_driver: WebElement o WebDriver
            selectors: Lista de tuplas (selector, Méthodo) donde Méthodo es 'CSS', 'XPATH', etc.
            extract_fn: Función opcional para procesar el texto extraído
            default: Valor por defecto si ningún selector funciona
            
        Returns:
            Texto extraído o valor por defecto
            
        Example:
            selectors = [
                ('[data-testid="price"]', 'CSS'),
                ('//span[@data-testid="price-alternative"]', 'XPATH')
            ]
        """
        for selector, method in selectors:
            try:
                if method == 'CSS':
                    elem = element_or_driver.find_element(By.CSS_SELECTOR, selector)
                elif method == 'XPATH':
                    elem = element_or_driver.find_element(By.XPATH, selector)
                else:
                    continue
                
                text = elem.text.strip()
                
                # Aplicar función de procesamiento si existe
                if extract_fn:
                    text = extract_fn(text)

                return text
                    
            except NoSuchElementException:
                continue
        
        return default

    def _extract_with_regex(
        self,
        element_or_driver,
        selectors: List[Tuple[str, str]],
        regex_pattern: str,
        group: int = 1,
        default: str = ""
    ) -> str:
        """
        Extrae usando selectores + regex
        
        Args:
            element_or_driver: WebElement o WebDriver
            selectors: Lista de tuplas (selector, Méthodo)
            regex_pattern: Patrón regex para extraer
            group: Grupo de captura a retornar
            default: Valor por defecto
            
        Returns:
            Texto extraído o valor por defecto
        """
        def extract_fn(text):
            match = re.search(regex_pattern, text, re.IGNORECASE)
            return match.group(group) if match else None
        
        return self._try_extract(element_or_driver, selectors, extract_fn, default)

    # ============================================================
    # NAVEGACIÓN Y URL
    # ============================================================

    def build_search_url(self, search_term: str, checkin: str, checkout: str) -> str:
        """
        Construye URL de búsqueda (versión completa con parámetros de moneda)
        
        Args:
            search_term: Hotel o ciudad
            checkin: Fecha YYYY-MM-DD
            checkout: Fecha YYYY-MM-DD
            
        Returns:
            URL completa
        """
        params = {
            'ss': search_term,
            'checkin': checkin,
            'checkout': checkout,
            'group_adults': '2',
            'no_rooms': '1',
            'group_children': '0',
            'selected_currency': 'COP',
            'changed_currency': '1',
            'top_currency': '1'
        }
        param_string = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'{self.BOOKING_BASE_URL}/searchresults.es.html?{param_string}'

    def build_city_search_url(self, ciudad: str, checkin: str, checkout: str) -> str:
        """Versión simplificada para búsqueda por ciudad"""
        params = [
            f"ss={ciudad}",
            f"checkin={checkin}",
            f"checkout={checkout}",
            f"group_adults=2",
            f"no_rooms=1",
            f"group_children=0"
        ]
        return f"{self.BOOKING_BASE_URL}/searchresults.es.html?{'&'.join(params)}"

    def close_popup(self):
        """Cierra popup de login si existe"""
        try:
            button = self.driver.find_element(
                By.XPATH,
                '//button[@aria-label="Ignorar información sobre el inicio de sesión."]'
            )
            button.click()
            time.sleep(1)
            logger.debug("✓ Popup cerrado")
        except Exception:
            pass

    # ============================================================
    # EXTRACCIÓN DE PÁGINA INDIVIDUAL DE HOTEL
    # ============================================================

    def search_hotel(self, hotel_data: HotelSearchData, checkin: str, checkout: str) -> HotelResult:
        """
        Busca un hotel específico y extrae información
        Template Method Pattern
        """
        url = self.build_search_url(hotel_data.hotel, checkin, checkout)
        logger.info(f"🔍 {hotel_data.hotel} ({checkin} → {checkout})")

        self.driver.get(url)
        time.sleep(1)
        self.close_popup()
        time.sleep(1)

        return self.extract_hotel_data(hotel_data, checkin, checkout)

    def extract_hotel_data(
        self, 
        hotel_data: HotelSearchData, 
        checkin: str, 
        checkout: str
    ) -> HotelResult:
        """Extrae datos del hotel de la página de resultados"""
        try:
            nombre = self.extract_name()
            precio = self.extract_price()
            calificacion = self.extract_rating()
        except Exception as e:
            logger.warning(f"⚠️ Error: {e}")
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
        return self.driver.find_element(By.CSS_SELECTOR, '[data-testid="title"]').text

    def extract_price(self) -> str:
        """Extrae precio de página individual con múltiples estrategias"""
        selectors = [
            ('div.abf093bdfe.fc23698243', 'CSS'),
            ('div.fff1944c52.e1ca2942a5', 'CSS'),
            ('//span[@data-testid="price-and-discounted-price"]', 'XPATH'),
            ('[data-testid="price"]', 'CSS'),
            ('.//span[@data-testid="price-and-discounted-price"]', 'XPATH'),
            ('.//span[@data-testid="price-alternative"]', 'XPATH'),
            ('.//span[@data-testid="price"]', 'XPATH'),
        ]
        
        def clean_price(text):
            return text.replace("Desde ", "").replace(".", "").strip() if text else None
        
        result = self._try_extract(self.driver, selectors, clean_price, "0")

        return result



    def extract_rating(self) -> str:
        """Extrae calificación (compatibilidad - usa extract_rating_details)"""
        return self.extract_rating_details().get('calificacion_cualitativa', '')

    def extract_rating_details(self) -> Dict[str, str]:
        """Extrae puntuación, calificación cualitativa y comentarios"""
        try:
            return {
                'puntuacion': self.extract_puntuacion(),
                'calificacion_cualitativa': self.extract_calificacion_cualitativa(),
                'comentarios': self.extract_comentarios()
            }
        except Exception as e:
            logger.warning(f"⚠️ Error en rating details: {e}")
            return {
                'puntuacion': "No disponible",
                'calificacion_cualitativa': "No disponible",
                'comentarios': "0"
            }

    def extract_puntuacion(self) -> str:
        """
        Extrae puntuación numérica con estrategias robustas
        Basado en análisis de HTML real de Booking.com
        """

        # ESTRATEGIA 1: Por data-testid (más estable)
        try:
            score_section = self.driver.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]'
            )
            score_element = score_section.find_element(By.XPATH, './div[1]')
            text = score_element.text.strip()
            match = re.search(r'(\d+[.,]\d+)', text)
            if match:
                score = match.group(1)
                return score
        except NoSuchElementException:
            pass
        
        # ESTRATEGIA 2: Por clases CSS conocidas (incluyendo variantes observadas)
        selectors = [
            ('div.bc946a29db', 'CSS'),
            ('div.f63b14ab7a.dff2e52086', 'CSS'),
            ('div.f6e3a11b0d.c46553d73.ab1870d302', 'CSS'),  # De HTML real
            ('div.bc946a29db.a57c0fa20a.c963f481bb', 'CSS'),  # Variante común
            ('div[class*="bc946a29db"]', 'CSS'),              # Partial match
            ('div[class*="f63b14ab7a"]', 'CSS'),              # Partial match
        ]
        result = self._extract_with_regex(
            self.driver, 
            selectors, 
            r'(\d+[.,]\d+)',
            default=None
        )
        if result:
            logger.debug(f"✓ Puntuación por CSS: {result}")
            return result
        
        # ESTRATEGIA 3: Por aria-label
        try:
            elements = self.driver.find_elements(
                By.XPATH,
                './/*[contains(@aria-label, "Puntuación") or contains(@aria-label, "puntuación")]'
            )
            for element in elements:
                aria_label = element.get_attribute('aria-label')
                if aria_label:
                    match = re.search(r'(\d+[.,]\d+)', aria_label)
                    if match:
                        score = match.group(1)
                        logger.debug(f"✓ Puntuación por aria-label: {score}")
                        return score
        except Exception:
            pass
        
        # ESTRATEGIA 4: Buscar divs que contengan SOLO un número decimal
        try:
            divs = self.driver.find_elements(
                By.XPATH,
                './/div[@data-testid="review-score"]//div'
            )
            for div in divs:
                text = div.text.strip()
                if re.match(r'^\d+[.,]\d+$', text):
                    logger.debug(f"✓ Puntuación exacta en div: {text}")
                    return text
        except Exception:
            pass
        
        # ESTRATEGIA 5: Regex en page_source (último recurso)
        try:
            patterns = [
                r'"reviewScore[Value]?"[:\s]*(\d+[.,]\d+)',
                r'data-score[=\s]+"(\d+[.,]\d+)"',
                r'[Pp]untuaci[óo]n[:\s]+(\d+[.,]\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, self.driver.page_source, re.IGNORECASE)
                if match:
                    score = match.group(1)
                    logger.debug(f"✓ Puntuación por regex en HTML: {score}")
                    return score
        except Exception:
            pass
        
        logger.warning("⚠️ No se pudo extraer puntuación")
        return "No disponible"

    def extract_calificacion_cualitativa(self) -> str:
        """Extrae calificación cualitativa"""
        # Estrategia 1: Por texto con palabras clave
        keywords_xpath = " or ".join([f"contains(text(), '{kw}')" for kw in self.QUALITATIVE_KEYWORDS])
        text_selectors = [(f"//div[{keywords_xpath}]", 'XPATH')]
        
        result = self._extract_with_regex(
            self.driver,
            text_selectors,
            r"(\w+\s*\w+)\s*:",
            default=None
        )

        if result:
            return self.cleaner.quitar_tildes(result)
        
        # Estrategia 2: Por clases CSS
        class_selectors = [
            ('div.f63b14ab7a.f546354b44', 'CSS'),
            ('div[class="f63b14ab7a f546354b44 becbee2f63"]', 'CSS'),
        ]
        result = self._try_extract(self.driver, class_selectors, default=None)
        if result:
            return result
        
        # Estrategia 3: Regex en page_source
        pattern = r'\b(' + '|'.join(self.QUALITATIVE_KEYWORDS) + r')\b'
        match = re.search(pattern, self.driver.page_source, re.IGNORECASE)
        return match.group(1) if match else "No disponible"

    def extract_comentarios(self) -> str:
        """Extrae número de comentarios de página individual"""
        # Estrategia 1: Por clase CSS
        selectors = [('div[class="fff1944c52 fb14de7f14 eaa8455879"]', 'CSS')]
        
        def clean_comments(text):
            cleaned = re.sub(r'\s*comentarios?', '', text, flags=re.IGNORECASE)
            cleaned = re.sub(r'[.,]', '', cleaned)
            return cleaned if cleaned.isdigit() else None
        
        result = self._try_extract(self.driver, selectors, clean_comments, None)
        if result:
            return result
        
        # Estrategia 2: Regex en page_source
        matches = re.findall(
            r'\b(\d{1,3}(?:[.,]\d{3})*|\d{1,6})\s*comentarios?\b',
            self.driver.page_source,
            re.IGNORECASE
        )
        if matches and len(matches) > 1:
            return re.sub(r'[.,]', '', matches[1])
        
        return "0"

    # ============================================================
    # EXTRACCIÓN DE LISTADOS (PROPERTY CARDS)
    # ============================================================

    def extract_hotels_from_city(
        self, 
        ciudad: str, 
        checkin: str, 
        checkout: str
    ) -> List[Dict]:
        """
        Extrae todos los hoteles de una ciudad desde property-cards
        
        Args:
            ciudad: Nombre de la ciudad
            checkin: Fecha YYYY-MM-DD
            checkout: Fecha YYYY-MM-DD
            
        Returns:
            Lista de diccionarios con info de hoteles
        """
        logger.info(f"🏨 Procesando: {ciudad}")
        url = self.build_city_search_url(ciudad, checkin, checkout)
        
        try:
            self.driver.get(url)
            time.sleep(1)
            self.close_popup()
            time.sleep(1)
            
            cards = self.driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')
            import pprint as pp
            print(f"\n{' '*30}HTML de CARDs:\n")
            pp.pprint(cards)

            if not cards:
                logger.warning(f"⚠️ No se encontraron hoteles en {ciudad}")
                return []
            
            logger.info(f"📊 Encontrados {len(cards)} hoteles")
            
            hotels_data = []
            for idx, card in enumerate(cards, 1):
                try:
                    hotel_info = self._extract_from_property_card(card, ciudad, checkin, checkout)
                    if hotel_info:
                        hotels_data.append(hotel_info)
                        logger.debug(f"  [{idx}/{len(cards)}] ✓ {hotel_info.get('hotel', 'N/A')}")
                except Exception as e:
                    logger.warning(f"  [{idx}/{len(cards)}] ✗ {e}")
            
            logger.info(f"✅ {ciudad}: {len(hotels_data)} hoteles procesados")
            return hotels_data
            
        except Exception as e:
            logger.error(f"❌ Error al Extraer desde la card property {ciudad}: {e}")
            return []

    def _extract_from_property_card(
        self,
        card,
        ciudad: str,
        checkin: str,
        checkout: str
    ) -> Dict:
        """
        Extrae información de una property-card
        Méthodo unificado que consolida toda la extracción
        
        Args:
            card: WebElement de la property-card
            ciudad: Ciudad
            checkin: Fecha entrada
            checkout: Fecha salida
            
        Returns:
            Diccionario con datos del hotel
        """
        # Nombre
        hotel_name = self._try_extract(
            card,
            [('.//div[@data-testid="title"]', 'XPATH')],
            default="No disponible"
        )
        
        # Precio (múltiples estrategias)
        precio_raw = self._try_extract(
            card,
            [
                ('.//span[@data-testid="price-and-discounted-price"]', 'XPATH'),
                ('.//span[@data-testid="price-alternative"]', 'XPATH'),
                ('.//span[@data-testid="price"]', 'XPATH'),
                ('div.abf093bdfe.fc23698243', 'CSS'),
                ('div.fff1944c52.e1ca2942a5', 'CSS'),
                ('//span[@data-testid="price-and-discounted-price"]', 'XPATH'),
                ('[data-testid="price"]', 'CSS'),
            ],
            default="0"
        )
        if not precio_raw:
            precio_raw = self.extract_price()
        else:
            # no borrar este logger, fallaria PRECIO Y DIVISAS
            logger.info(f"\n\n{' '*20}precio RAW: {precio_raw}\n")

        divisa, precio = self.cleaner.limpiar_precio(precio_raw)
        
        # Puntuación - Estrategias mejoradas
        puntuacion = self._extract_puntuacion_from_card(card)
        
        # Calificación cualitativa
        review_promedio = self._try_extract(
            card,
            [('.//div[@data-testid="review-score"]/div[2]/div[1]', 'XPATH')],
            default=""
        )
        if review_promedio:
            # no borrar este logger, fallaria reviews
            logger.info(f"\n\n{' '*20}review promedio: {review_promedio}\n")
        else:
            review_promedio = self.extract_rating()
        
        # Comentarios (con estrategias robustas)
        comentarios = self._extract_reviews_from_card(card)
        
        return {
            'hotel': hotel_name,
            'divisa': divisa,
            'precio': precio,
            'puntuacion': puntuacion,
            'review_promedio': review_promedio,
            'comentarios': comentarios,
            'ciudad': ciudad,
            'check_in': checkin,
            'check_out': checkout
        }

    def _extract_puntuacion_from_card(self, card) -> str:
        """
        Extrae puntuación de una property-card con múltiples estrategias
        
        Args:
            card: WebElement de la property-card
            
        Returns:
            Puntuación o "No disponible"
        """
        # ESTRATEGIA 1: Ruta estándar de data-testid
        try:
            score = card.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]/div[1]'
            ).text.strip()
            
            if re.match(r'^\d+[.,]\d+$', score):
                logger.debug(f"✓ Puntuación card (data-testid): {score}")
                return score
        except NoSuchElementException:
            pass
        
        # ESTRATEGIA 2: Por clases CSS (incluyendo variantes)
        selectors = [
            ('div.bc946a29db', 'CSS'),
            ('div.f63b14ab7a.dff2e52086', 'CSS'),
            ('div.f6e3a11b0d.c46553d73.ab1870d302', 'CSS'),
            ('div[class*="bc946a29db"]', 'CSS'),
        ]
        result = self._extract_with_regex(
            card,
            selectors,
            r'(\d+[.,]\d+)',
            default=None
        )
        if result:
            logger.debug(f"✓ Puntuación card (CSS): {result}")
            return result
        
        # ESTRATEGIA 3: Buscar en TODOS los divs de review-score
        try:
            review_section = card.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]'
            )
            divs = review_section.find_elements(By.XPATH, './/div')
            
            for div in divs[:5]:  # Revisar los primeros 5 divs
                text = div.text.strip()
                # Buscar SOLO número decimal
                if re.match(r'^\d+[.,]\d+$', text):
                    logger.debug(f"✓ Puntuación card (div exacto): {text}")
                    return text
        except NoSuchElementException:
            pass
        
        # ESTRATEGIA 4: Por aria-label
        try:
            elements = card.find_elements(
                By.XPATH,
                './/*[contains(@aria-label, "Puntuación") or contains(@aria-label, "puntuación")]'
            )
            for element in elements:
                aria_label = element.get_attribute('aria-label')
                if aria_label:
                    match = re.search(r'(\d+[.,]\d+)', aria_label)
                    if match:
                        score = match.group(1)
                        logger.debug(f"✓ Puntuación card (aria-label): {score}")
                        return score
        except Exception():
            pass
        
        logger.debug("⚠️ No se pudo extraer puntuación de la card")
        return "No disponible"

    def _extract_reviews_from_card(self, card) -> str:
        """
        Extrae número de comentarios de una property-card
        Méthodo consolidado con múltiples estrategias
        
        Args:
            card: WebElement de la property-card
            
        Returns:
            Número de comentarios o "0"
        """
        # Estrategia 1: Estructura típica
        result = self._extract_with_regex(
            card,
            [('.//div[@data-testid="review-score"]/div[2]/div[2]', 'XPATH')],
            r'(\d+(?:\.\d+)?)',
            default=None
        )
        if result:
            return result.replace('.', '')
        
        # Estrategia 2: Sección completa de review-score
        result = self._extract_with_regex(
            card,
            [('.//div[@data-testid="review-score"]', 'XPATH')],
            r'(\d+(?:\.\d+)?)\s*(?:comentarios|opiniones|reviews)',
            default=None
        )
        if result:
            return result.replace('.', '')
        
        # Estrategia 3: Cualquier elemento con "comentarios"
        result = self._extract_with_regex(
            card,
            [('.//*[contains(text(), "comentarios") or contains(text(), "opiniones")]', 'XPATH')],
            r'(\d+(?:\.\d+)?)',
            default="0"
        )
        
        return result.replace('.', '')

    # ============================================================
    # ALIAS PARA COMPATIBILIDAD
    # ============================================================

    def _extract_hotel_info(self, *args, **kwargs):
        """Alias para compatibilidad con código existente"""
        return self._extract_from_property_card(*args, **kwargs)
    
    def _extract_reviews_count(self, *args, **kwargs):
        """Alias para compatibilidad con código existente"""
        return self._extract_reviews_from_card(*args, **kwargs)
    
    def _extract_hotel_info_from_card(self, *args, **kwargs):
        """Alias para mantener consistencia de nombres"""
        return self._extract_from_property_card(*args, **kwargs)
    
    def _extract_reviews_count_from_card(self, *args, **kwargs):
        """Alias para mantener consistencia de nombres"""
        return self._extract_reviews_from_card(*args, **kwargs)

    # ============================================================
    # Méthodo ABSTRACTO
    # ============================================================

    @abstractmethod
    def run(self) -> List[dict]:
        """
        Méthodo abstracto que cada scraper debe implementar
        Define el flujo de ejecución específico del scraper
        """
        pass
