#!/usr/bin/env python3
"""
Web Scraping Competencia Adhoc
Uso: python script.py 'clientes_diario' '2025-02-01' '2025-02-10'
"""
"""
import time
import pandas as pd
from datetime import timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils.enviar_sheets_clientes_diario import enviar_sheets_diario
from utils.get_dates import get_dates
from utils.get_sheet_data import get_sheet_data
from utils.logger import logger


WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyPzxk_tlVrVvQlZg0k8M0g_lIRifVqgf5EdA7EsdeMGdoHPYwNsZAiRN0Zk0U6EUbl/exec"


# Función para iniciar la búsqueda diaria
def iniciar_busqueda():

    # Convertir las fechas ingresadas a objetos datetime
    try:
        check_in, check_out = get_dates()
        clientes_ciudades = get_sheet_data()

    except ValueError:
        logger.error("las fechas no pudieron ser parseadas")
        return


    # Configuración del driver de Selenium (Chrome)
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Lista para almacenar los datos de los hoteles
    hotels_list = []

    # Iterar sobre cada día en el rango de fechas
    fecha_actual = check_in
    while fecha_actual < check_out:
        siguiente_dia = fecha_actual + timedelta(days=1)
        checkin_str = fecha_actual.strftime('%Y-%m-%d')
        checkout_str = siguiente_dia.strftime('%Y-%m-%d')

        # Iterar sobre cada cliente y realizar la búsqueda diaria
        for cliente_info in clientes_ciudades:
            cliente = cliente_info['Hotel']
            ciudad = cliente_info['Ciudad']
            url = f'https://www.booking.com/searchresults.es.html?ss={cliente}&checkin={checkin_str}&checkout={checkout_str}&group_adults=2&no_rooms=1&group_children=0'

            driver.get(url)
            time.sleep(5)

            # Cerrar el pop-up, si aparece
            try:
                close_popup_button = driver.find_element(By.XPATH,
                                                         '//button[@aria-label="Ignorar información sobre el inicio de sesión."]')
                close_popup_button.click()
                time.sleep(2)
            except Exception:
                pass  # Ignorar si no aparece el pop-up

            # Crear un diccionario para almacenar la información del hotel
            hotel_dict = {}
            try:
                # Capturar precios en orden de prioridad
                try:
                    # Precio alternativo (Desde)
                    price_alternativo_element = driver.find_element(By.CSS_SELECTOR, 'div.abf093bdfe.fc23698243')
                    hotel_dict['precio'] = price_alternativo_element.text.replace("Desde ", "").strip()
                except Exception:
                    try:
                        # Precio con descuento
                        price_descuento_element = driver.find_element(By.XPATH,
                                                                      '//span[@data-testid="price-and-discounted-price"]')
                        hotel_dict['precio'] = price_descuento_element.text.strip()
                    except Exception:
                        try:
                            # Precio base
                            price_base_element = driver.find_element(By.CSS_SELECTOR, '[data-testid="price"]')
                            hotel_dict['precio'] = price_base_element.text.strip()
                        except Exception:
                            hotel_dict['precio'] = "0"  # Ningún precio disponible

                # Extraer el nombre y la calificación del hotel si están disponibles
                hotel_dict['nombre'] = driver.find_element(By.CSS_SELECTOR, '[data-testid="title"]').text
                hotel_dict['calificacion'] = driver.find_element(By.CSS_SELECTOR, '[data-testid="review-score"]').text
            except Exception as e:
                hotel_dict['nombre'] = cliente
                hotel_dict['precio'] = "No disponible"
                hotel_dict['calificacion'] = "No disponible"

            hotel_dict['ciudad'] = ciudad
            hotel_dict['check_in'] = checkin_str
            hotel_dict['check_out'] = checkout_str
            hotels_list.append(hotel_dict)

        # Avanzar al siguiente día en el rango
        fecha_actual = siguiente_dia

    enviar_sheets_diario(hotels_list, WEBAPP_URL)

    # Cerrar el navegador al finalizar
    driver.quit()


if __name__ == "__main__":
    iniciar_busqueda()"""

# !/usr/bin/env python3
"""
Scraper Ad-Hoc para búsqueda de clientes en rango de fechas
Hereda y reutiliza ClientesDiarioScraper
"""

import re
import time
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.logger import logger
from utils.enviar_sheets_clientes_diario import enviar_sheets_diario


class ClientesDiarioScraperAdHoc(BookingBaseScraper):
    """
    Scraper Ad-Hoc para búsqueda de hoteles en rango de fechas personalizado.
    Reutiliza toda la lógica de BookingBaseScraper.
    """

    def __init__(self, driver, hoteles: list, check_in: datetime, check_out: datetime):
        """
        Args:
            driver: Instancia de Selenium WebDriver
            hoteles: Lista de dicts con 'hotel'/'Hotel' y 'ciudad'/'Ciudad'
            check_in: Fecha inicial (datetime)
            check_out: Fecha final (datetime)
        """
        super().__init__(driver)
        self.hoteles = hoteles
        self.check_in = check_in
        self.check_out = check_out

    def run(self) -> list:
        """
        Ejecuta scraping para todos los hoteles en el rango de fechas.
        Itera día por día desde check_in hasta check_out.
        """
        results = []

        # Iterar sobre cada día en el rango de fechas
        fecha_actual = self.check_in

        while fecha_actual < self.check_out:
            siguiente_dia = fecha_actual + timedelta(days=1)
            checkin_str = fecha_actual.strftime('%Y-%m-%d')
            checkout_str = siguiente_dia.strftime('%Y-%m-%d')

            logger.info(f"📅 Procesando: {checkin_str} → {checkout_str}")

            # Iterar sobre cada hotel
            for hotel_data in self.hoteles:
                if not isinstance(hotel_data, dict):
                    logger.error(f"❌ Elemento no es dict: {type(hotel_data)}")
                    continue

                # Normalizar claves (mayúsculas o minúsculas)
                hotel = hotel_data.get('hotel') or hotel_data.get('Hotel') or ''
                ciudad = hotel_data.get('ciudad') or hotel_data.get('Ciudad') or ''

                if not hotel or not ciudad:
                    logger.warning(f"⚠️ Datos incompletos: {hotel_data}")
                    continue

                # Construir búsqueda
                hotel_ciudad = f"{hotel} - {ciudad}"
                hotel_ciudad = re.sub(r"\s{1,10}", "+", hotel_ciudad)

                # Usar el metodo heredado de BookingBaseScraper
                url = self.build_search_url(hotel_ciudad, checkin_str, checkout_str)
                logger.info(f"🔍 {hotel} | {checkin_str}")

                self.driver.get(url)
                time.sleep(5)
                self.close_popup()
                time.sleep(2)

                # Extraer datos usando métodos heredados
                try:
                    nombre = self.extract_name()
                    precio = self.extract_price()
                    calificacion = self.extract_rating()
                except Exception as e:
                    logger.warning(f"⚠️ {hotel} ({checkin_str}): {e}")
                    nombre = hotel
                    precio = "0"
                    calificacion = "No disponible"

                results.append({
                    'nombre': nombre,
                    'precio': precio,
                    'calificacion': calificacion,
                    'ciudad': ciudad,
                    'check_in': checkin_str,
                    'check_out': checkout_str
                })

                logger.info(f"✅ {nombre} - {precio}")

            # Avanzar al siguiente día
            fecha_actual = siguiente_dia

        return results


def buscar_reservas_adhoc(hoteles: list, check_in: datetime, check_out: datetime, webapp_url: str = None):
    """
    Función principal para ejecutar el scraper ad-hoc.

    Args:
        hoteles: Lista de hoteles a buscar
        check_in: Fecha inicial
        check_out: Fecha final
        webapp_url: URL opcional para enviar resultados a Google Sheets
    """
    logger.info("🚀 SCRAPING CLIENTES DIARIO AD-HOC")
    logger.info(f"📅 Rango: {check_in.strftime('%Y-%m-%d')} → {check_out.strftime('%Y-%m-%d')}")
    logger.info(f"🏨 Hoteles: {len(hoteles)}")

    driver = None
    try:
        # Crear driver
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        # Ejecutar scraping
        scraper = ClientesDiarioScraperAdHoc(driver, hoteles, check_in, check_out)
        results = scraper.run()

        # Enviar a Sheets si se proporciona URL
        if webapp_url:
            logger.info(f"📤 Enviando {len(results)} resultados a Sheets")
            enviar_sheets_diario(results, webapp_url)

        logger.info(f"✅ COMPLETADO: {len(results)} registros")
        return results

    except Exception as e:
        logger.error(f"💥 ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Datos de prueba
    fake_hoteles = [
        {'Hotel': 'Hotel Dann Carlton Bogotá', 'Ciudad': 'Bogotá'},
        {'Hotel': 'Hilton Bogotá Corferias', 'Ciudad': 'Bogotá'},
        {'Hotel': 'Hotel Tequendama', 'Ciudad': 'Bogotá'},
    ]

    # Rango de 3 días desde hoy
    fecha_inicio = datetime.now()
    fecha_fin = datetime.now() + timedelta(days=3)

    # Ejecutar
    resultados = buscar_reservas_adhoc(
        hoteles=fake_hoteles,
        check_in=fecha_inicio,
        check_out=fecha_fin,
        webapp_url=None  # Cambiar a tu WEBAPP_URL si quieres enviar a Sheets
    )

    # Mostrar resultados
    print(f"\n{'=' * 80}")
    print(f"Total de resultados: {len(resultados)}")
    print(f"{'=' * 80}\n")

    for hotel in resultados:
        print(f"🏨 {hotel['nombre']}")
        print(f"   📍 {hotel['ciudad']}")
        print(f"   💰 {hotel['precio']}")
        print(f"   ⭐ {hotel['calificacion']}")
        print(f"   📅 {hotel['check_in']} → {hotel['check_out']}")
        print("-" * 80)