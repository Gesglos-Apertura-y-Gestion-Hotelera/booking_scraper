"""
Clase base para scrapers de Booking.com
Versión optimizada - Elimina redundancias y consolida lógica común
"""
import re
import time
from abc import ABC, abstractmethod
from datetime import timedelta, datetime
from typing import List, Dict, Tuple

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from utils.cleaner import DataCleaner
from utils.logger import logger


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
                logger.info(f"Trying {selector} with text: {text}")
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
        search_url = f'{self.BOOKING_BASE_URL}/searchresults.es.html?{param_string}'
        search_url = re.sub(r"\s+", "+", search_url)
        logger.info(f"search_url: {search_url}")
        return search_url

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

    def extract_name(self) -> str:
        """Extrae nombre del hotel"""
        return self.driver.find_element(By.CSS_SELECTOR, '[data-testid="title"]').text

    def extract_price(self) -> str:
        """Extrae precio de página individual con múltiples estrategias"""
        selectors = [
            ('//span[@data-testid="price-and-discounted-price"]', 'XPATH'),
            ('[data-testid="price"]', 'CSS'),
            ('.//span[@data-testid="price-alternative"]', 'XPATH'),
            ('.//span[@data-testid="price"]', 'XPATH'),
            ('div.abf093bdfe.fc23698243', 'CSS'),
            ('div.fff1944c52.e1ca2942a5', 'CSS'),
        ]

        def clean_price(text):
            return text.replace("Desde ", "").replace(".", "").strip() if text else None

        property_cards=None

        try:
            # Primera estrategia, busque por posibles sitios con Selectors
            property_cards = self.driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')

            for card in property_cards:  # ✅ Ahora card es un WebElement individual
                result=self._try_extract(card, selectors, clean_price, "0")
                if result:
                    return result
        except Exception as e:
            logger.error(f" Strategie 1 Failed to extract price: {e}")

        # segunda estrategia, buscar todos los precios con COP al comienzo y devolver la primera
        if property_cards:
            for i, card in enumerate(property_cards[:1], 1):
                try:
                    precios_cop = [el.text.strip() for el in
                                   card.find_elements(By.XPATH, './/*[contains(text(), "COP")]') if el.text.strip()]

                    if precios_cop:
                        precio_principal = precios_cop[0]  # Primer precio COP
                        if "Desde" in precio_principal:
                            precio_cop=re.sub(r"Desde ", "", precio_principal, flags=re.IGNORECASE)
                        return precio_cop
                    else:
                        logger.warning("    ❌ Ningún precio COP encontrado")
                except Exception as e:
                    logger.warning(f"error {e}")
                    pass

    def extract_puntuacion(self) -> str:
        """
        Extrae puntuación numérica con estrategias robustas
        Basado en análisis de HTML real de Booking.com
        """
        punctuations=[]
        # ESTRATEGIA 1: Por data-testid (más estable)
        try:
            score_section = self.driver.find_element(
                By.XPATH,
                './/div[@data-testid="review-score"]'
            )
            score_element = score_section.find_element(By.XPATH, './div[1]')
            text = score_element.text.strip()
            punctuations.append(text)
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
                    punctuations.append(aria_label)
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
                punctuations.append(text)
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

        if "Nuevo en Booking.com" in punctuations:
            return "Hotel Nuevo: No Score"
        logger.warning("⚠️ No se pudo extraer puntuación")
        return "No disponible"

    def extract_calificacion_cualitativa(self) -> str:
        """Extrae calificación cualitativa"""

        # Estrategia 1: Por clases CSS
        class_selectors = [
            ('div.f63b14ab7a.f546354b44', 'CSS'),
            ('div[class="f63b14ab7a f546354b44 becbee2f63"]', 'CSS'),
        ]
        result = self._try_extract(self.driver, class_selectors, default=None)
        if result:
            return result

        # Estrategia 2: Regex en page_source
        pattern = r'\b(' + '|'.join(self.QUALITATIVE_KEYWORDS) + r')\b'
        match = re.search(pattern, self.driver.page_source, re.IGNORECASE)
        if match:
            logger.info(f"📤📤📤rescatado calificacion 2: {match.group(1)}")
            return match.group(1) if match else "No disponible"

        # Estrategia 3: Por texto con palabras clave
        keywords_xpath = " or ".join([f"contains(text(), '{kw}')" for kw in self.QUALITATIVE_KEYWORDS])
        text_selectors = [(f"//div[{keywords_xpath}]", 'XPATH')]

        result_3 = self._extract_with_regex(
            self.driver,
            text_selectors,
            r"(\w+\s*\w+)\s*:",
            default=None
        )

        if result_3:
            logger.info(f"📤📤📤rescatado calificacion 3: {result_3}")
            return result_3

        if "Nuevo en Booking.com" in self.driver.page_source:
            return "Hotel Nuevo: No Score"

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
        url = self.build_search_url(ciudad, checkin, checkout)

        try:
            self.open_url(url)

            cards = self.driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')

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
        hotel_name = self._extract_hotel_name(card)

        # Precio (múltiples estrategias)
        divisa, precio = self._extract_price_info(card)

        # Puntuación - Estrategias mejoradas
        puntuacion = self._extract_puntuacion_from_card(card)

        # Calificación cualitativa
        review_promedio = self._extract_review_text(card)

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

    def open_url(self, url:str):
        self.driver.get(url)
        time.sleep(5)
        self.close_popup()
        time.sleep(2)
        #self.take_screenshot()

    def take_screenshot(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="price-and-discounted-price"]')))

        self.driver.save_screenshot("debug_booking.png")

    # *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=
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
                    logger.info(f" ✅   ✅   ✅ Hotel info {hotel_info}")
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

        # Cada responsabilidad en su propio méthodo
        hotel_data['hotel'] = self._extract_hotel_name(hotel_element)
        hotel_data['divisa'], hotel_data['precio'] = self._extract_price_info(hotel_element)
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

        cleaner = DataCleaner()
        for selector in price_selectors:
            try:
                precio_element = hotel_element.find_element(By.CSS_SELECTOR, selector)
                precio_raw = precio_element.text.strip()

                # Filtrar textos no-numéricos
                if self._is_valid_price_text(precio_raw):
                    divisa, precio = cleaner.limpiar_precio(precio_raw)
                    logger.info(f"divisa: {divisa}  precio: {precio}")
                    return divisa, str(precio)

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

        # 🎯 2. FALLBACK: Regex directo en thodo el texto de la card
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

    # *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=
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
