import os
import time
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Obtener la fecha actual y sumar un día para el check-out
checkin = datetime.now().strftime('%Y-%m-%d')
checkout = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# Abrir cuadro de diálogo para seleccionar el archivo
Tk().withdraw()
ruta_archivo = askopenfilename(title="Selecciona el archivo Excel", filetypes=[("Archivos Excel", "*.xlsx")])

# Cargar el archivo seleccionado
df = pd.read_excel(ruta_archivo, sheet_name='Competencia')

# Suponiendo que los competidores están en columnas llamadas 'Competidor' y 'Ciudad'
competencia_ciudades = df[['Competidor', 'Ciudad']].to_dict(orient='records')

# Configuración del driver de Selenium (Chrome)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Lista para almacenar los datos de los competidores
hotels_list = []

# Iterar sobre la lista de competidores
for competencia_info in competencia_ciudades:
    competencia = competencia_info['Competidor']
    ciudad = competencia_info['Ciudad']
    
    # Crear la URL dinámica para cada competidor y ciudad
    url = f'https://www.booking.com/searchresults.es.html?ss={competencia}%20{ciudad}&checkin={checkin}&checkout={checkout}&group_adults=2&no_rooms=1&group_children=0'
    
    # Abrir la página con la URL generada
    driver.get(url)
    time.sleep(5)

    # Cerrar pop-up si aparece
    try:
        close_popup_button = driver.find_element(By.XPATH, '//button[@aria-label="Ignorar información sobre el inicio de sesión."]')
        close_popup_button.click()
        time.sleep(2)
    except Exception:
        pass  # Ignora el error si no encuentra el pop-up

    # Crear un diccionario para almacenar la información del competidor
    hotel_dict = {}

    # Capturar precios en orden de prioridad
    try:
        # Precio alternativo (Desde)
        try:
            precio_alternativo = driver.find_element(By.CSS_SELECTOR, 'div.abf093bdfe.fc23698243')
            hotel_dict['precio'] = precio_alternativo.text.replace("Desde ", "").strip()
        except Exception:
            # Precio con descuento
            try:
                precio_descuento = driver.find_element(By.XPATH, '//span[@data-testid="price-and-discounted-price"]')
                hotel_dict['precio'] = precio_descuento.text.strip()
            except Exception:
                # Precio base
                try:
                    precio_base = driver.find_element(By.CSS_SELECTOR, '[data-testid="price"]')
                    hotel_dict['precio'] = precio_base.text.strip()
                except Exception:
                    hotel_dict['precio'] = "0"  # Ningún precio disponible

        # Extraer nombre y calificación
        hotel_dict['nombre'] = (
            driver.find_element(By.CSS_SELECTOR, '[data-testid="title"]').text
            if driver.find_elements(By.CSS_SELECTOR, '[data-testid="title"]')
            else "No se encontró"
        )
        hotel_dict['calificacion'] = (
            driver.find_element(By.CSS_SELECTOR, '[data-testid="review-score"]').text
            if driver.find_elements(By.CSS_SELECTOR, '[data-testid="review-score"]')
            else "0"
        )

    except Exception:
        # En caso de error, asignar valores predeterminados
        hotel_dict['nombre'] = competencia
        hotel_dict['precio'] = "0"
        hotel_dict['calificacion'] = "0"

    # Agregar información adicional al diccionario
    hotel_dict['competidor'] = competencia
    hotel_dict['ciudad'] = ciudad
    hotel_dict['check_in'] = checkin
    hotel_dict['check_out'] = checkout

    hotels_list.append(hotel_dict)

# Guardar los datos en un archivo CSV
df_hotels = pd.DataFrame(hotels_list)

# Crear la carpeta de guardado si no existe
home_dir = os.path.expanduser("~")
ruta_guardado = os.path.join(home_dir, 'Documents', 'scraping_results', 'Competencia')
if not os.path.exists(ruta_guardado):
    os.makedirs(ruta_guardado)

# Guardar con nombre seguro
nombre_archivo = os.path.join(ruta_guardado, f'{checkin}.csv')
df_hotels.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
print(f"Archivo guardado en: {nombre_archivo}")

# Cerrar el navegador al finalizar
driver.quit()
