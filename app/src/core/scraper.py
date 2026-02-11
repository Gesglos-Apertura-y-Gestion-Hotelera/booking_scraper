"""
Clase base para scrapers de Booking.com
Versión optimizada - Elimina redundancias y consolida lógica común
"""
import re
import time
from abc import ABC, abstractmethod
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
            # ('[data-testid="price"]', 'CSS'),
            # ('.//span[@data-testid="price-alternative"]', 'XPATH'),
            # ('.//span[@data-testid="price"]', 'XPATH'),
            ('div.abf093bdfe.fc23698243', 'CSS'),
            ('div.fff1944c52.e1ca2942a5', 'CSS'),
        ]

        def clean_price(text):
            return text.replace("Desde ", "").replace(".", "").strip() if text else None

        # property_cards = self.driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')
        # if property_cards:
        #     logger.info("\n=== DETALLES DE LAS CARDS ===")
        #     for i, card in enumerate(property_cards[:1], 1):
        #         try:
        #             nombre = card.find_element(By.CSS_SELECTOR, 'div[data-testid="title"]').text
        #             logger.info(f"[{i}] Hotel: {nombre}")
        #             logger.info(f"    Tag: {card.tag_name}")
        #             precio = card.find_element(By.XPATH, '//span[@data-testid="price-and-discounted-price"]').text
        #             logger.info(f"    Precio 1: {precio}")
        #             precio = card.find_element(By.XPATH, '//span[@data-testid="price-and-discounted-price"]').text
        #             logger.info(f"    Precio 1: {precio}") #<div class="ab607752a2 f6b355237f"><span data-testid="price-and-discounted-price" aria-hidden="true" class="b87c397a13 f2f358d1de ab607752a2">COP&nbsp;280.000</span><span class="fc70cba028 bf44319e7e ca6ff50764 bc7d708ceb" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="50px"><path d="M14.25 15.75h-.75a.75.75 0 0 1-.75-.75v-3.75a1.5 1.5 0 0 0-1.5-1.5h-.75a.75.75 0 0 0 0 1.5h.75V15a2.25 2.25 0 0 0 2.25 2.25h.75a.75.75 0 0 0 0-1.5M11.625 6a1.125 1.125 0 1 0 0 2.25 1.125 1.125 0 0 0 0-2.25.75.75 0 0 0 0 1.5.375.375 0 1 1 0-.75.375.375 0 0 1 0 .75.75.75 0 0 0 0-1.5M22.5 12c0 5.799-4.701 10.5-10.5 10.5S1.5 17.799 1.5 12 6.201 1.5 12 1.5 22.5 6.201 22.5 12m1.5 0c0-6.627-5.373-12-12-12S0 5.373 0 12s5.373 12 12 12 12-5.373 12-12"></path></svg></span></div>
        #             # precio_2 = card.find_element(By.CSS_SELECTOR, '[data-testid="price"]').text
        #             # logger.info(f"    Precio 2: {precio_2}")
        #             precio_21 = self.driver.find_element(By.CSS_SELECTOR, 'div.ab607752a2.f6b355237f').text
        #             logger.info(f"    Precio 21: {precio_21}")
        #             precio_22 = card.find_element(By.CSS_SELECTOR, 'div.fff1944c52.e1ca2942a5').text
        #             logger.info(f"    Precio 22: {precio_22}")
        #             # precio_3 = card.find_element(By.XPATH, '//span[@data-testid="price-alternative"]').text
        #             # logger.info(f"    Precio 3: {precio_3}")
        #             # precio_4 = card.find_element(By.XPATH, './/span[@data-testid="price"]').text
        #             # logger.info(f"    Precio 4: {precio_4}")
        #             logger.info(f"    Visible: {card.is_displayed()}")
        #
        #             try:
        #                 precio_container = card.find_element(By.CSS_SELECTOR,
        #                                                      '[data-testid="price-and-discounted-price"]')
        #                 precio_2 = precio_container.text.strip()  # Captura todo: "US$120/noche total"
        #                 logger.info(f"    Precio 2: {precio_2}")
        #             except Exception as e:
        #                 logger.warning(f"    Precio no encontrado: {e}")
        #         except Exception as e:
        #             logger.warning(f"[{i}] Error: {e}")
        # else:
        #     logger.error("❌ NO se encontraron property cards!")
        # Reemplaza toda la sección de precios con ESTO:

        property_cards = self.driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')
        if property_cards:
            logger.info("\n=== DEBUG COMPLETO ===")
            for i, card in enumerate(property_cards[:1], 1):
                logger.info(f"\n{i}. {card.text}")

                logger.info("=== DEBUG CARD ===")
                logger.info(f"TEXTO VISIBLE: {card.text[:500]}...")  # Primeros 500 chars
                logger.info(f"TODOS PRECIOS: {[el.text for el in card.find_elements(By.XPATH, './/*[contains(text(), COP)]')]}")
                logger.info(f"HTML: {card.get_attribute('outerHTML')[:1000]}...")

                # for i, card in enumerate(property_cards[:1], 1):
                #     logger.info(f"\n=== DEBUG {i} ===")
                #
                #     # SCROLL
                #     self.driver.execute_script("arguments[0].scrollIntoView();", card)
                #     time.sleep(2)  # MÁS tiempo
                #
                #     # Hover + busca en toda la página
                #     from selenium.webdriver.common.action_chains import ActionChains
                #     ActionChains(self.driver).move_to_element(card).perform()
                #     time.sleep(1)
                #
                #     # Busca EXACTAMENTE "280.000" en CUALQUIER span
                #     span_280 = self.driver.find_element(By.XPATH, "//span[contains(text(), '280.000')]")
                #     logger.info(f"🎯 ENCONTRADO: '{span_280.text}' en {span_280.tag_name}")

                precio = self.driver.find_element(By.XPATH, '//span[@data-testid="price-and-discounted-price"]').text
                print(f"precio -----------> {precio}")

                #  NO FUNCIONA
                # precios_css = self.driver.execute_script("""
                #     var elementos = arguments[0].querySelectorAll('*');
                #     var precios = [];
                #     for(var el of elementos) {
                #         var before = window.getComputedStyle(el, '::before').content;
                #         var after = window.getComputedStyle(el, '::after').content;
                #         if (before !== 'none' && before.includes('COP')) precios.push(before);
                #         if (after !== 'none' && after.includes('COP')) precios.push(after);
                #     }
                #     return precios;
                # """, card)
                #
                # logger.info(f"\n\n  ✅ PRECIOS CSS ::before/::after: {precios_css} \n\n")

                # Busca canvas/textPath que Booking usa para anti-bot
                canvas_precios = self.driver.execute_script("""
                    return Array.from(arguments[0].querySelectorAll('canvas, text, textPath'))
                        .map(el => el.textContent || el.innerText)
                        .filter(text => text.includes('COP'));
                """, card)
                logger.info(f"\ncanvas_precios {canvas_precios}")





                # try:
                #     # ******************************************************
                #     # FUNCIONA
                #     # precios_cop = [el.text.strip() for el in
                #     #                card.find_elements(By.XPATH, './/*[contains(text(), "COP")]') if el.text.strip()]
                #     # if precios_cop:
                #     #     precio_principal = precios_cop[0]  # Primer precio COP
                #     #     logger.info(f" ❌   ✅ Precio principal: {precio_principal}")
                #     # else:
                #     #     logger.warning("    ❌ Ningún precio COP encontrado")
                #     # ******************************************************
                # except Exception as e:
                #     logger.warning(f"error {e}")
                #     pass

                try:
                    # PRIMER INTENTO: data-testid (Mariquita layout)
                    span_testid = self.driver.find_element(By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]')
                    precio_testid = span_testid.text.strip()

                    # Si NO dice "Desde" → ES el precio correcto (Mariquita)
                    # if "Desde" not in precio_testid:
                    if "Desde " in precio_testid:
                        logger.info(f"    🎯 Layout 1 detectado: {precio_testid}")
                        return precio_testid
                    else:
                        # Si DICE "Desde" → Es promo, busca el real (Manilab)
                        logger.info(f"    🔍 Layout 1 es promo, buscando real...")

                except:
                    logger.info("    🔍 Layout 1 no disponible, probando Layout 2...")

                    # SEGUNDO INTENTO: Fallback sin "Desde" (Manilab)
                precios_cop = self.driver.find_elements(By.XPATH,
                                                 './/*[contains(text(), "COP") ]')
                if precios_cop:
                    precio_real = precios_cop[0].text.strip()
                    logger.info(f"    🎯 Layout 2 detectado: {precio_real}")
                    return precio_real

                #return None
                # *************************************************************
                print("=== TODOS LOS ELEMENTOS CON TEXTO ===")
                todos_elementos = card.find_elements(By.XPATH, ".//*[text()]")
                for i, el in enumerate(todos_elementos[:20]):  # Primeros 20
                    texto = el.text.strip()
                    if texto:
                        print(f"  [{i}] '{texto}'")

        import pprint as pp
        logger.info(f"SELF:DRIVER property cards {self.driver}")
        result_1=self._try_extract(property_cards, selectors, clean_price, "0")
        logger.info(f"result con property cards {pp.pformat(result_1)}")
        result = self._try_extract(self.driver, selectors, clean_price, "0")
        logger.info(f"result sin property cards {pp.pformat(result)}")
        return result

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
        hotel_name = self.extract_name()
        
        # Precio (múltiples estrategias)
        precio_raw = self.extract_price()
        divisa, precio = self.cleaner.limpiar_precio(precio_raw)
        
        # Puntuación - Estrategias mejoradas
        puntuacion = self._extract_puntuacion_from_card(card)
        
        # Calificación cualitativa
        review_promedio = self.extract_calificacion_cualitativa()

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

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="price-and-discounted-price"]')))

        # 1. GUARDAR SCREENSHOT PARA DEPURE
        self.driver.save_screenshot("debug_booking.png")
        print("Captura de pantalla guardada como 'debug_booking.png'")

        # 2. EXTRAER EL PRECIO
        precio_elemento = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="price-and-discounted-price"]')
        print(f"Texto extraído por el bot: {precio_elemento.text}")

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
