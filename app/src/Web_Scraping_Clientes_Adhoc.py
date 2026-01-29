#!/usr/bin/env python3
"""
Web Scraping Competencia Adhoc
Uso: python script.py 'clientes_diario' '2025-02-01' '2025-02-10'
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
    iniciar_busqueda()