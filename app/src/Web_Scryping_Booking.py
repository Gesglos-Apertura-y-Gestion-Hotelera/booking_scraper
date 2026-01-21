import os
import tkinter as tk
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

# Lista global para almacenar todos los resultados de las búsquedas
todos_los_hoteles = []

# Función para realizar la búsqueda y guardar el resultado
def ejecutar_busqueda(driver, ciudad, checkin, checkout):
    url = f'https://www.booking.com/searchresults.es.html?ss={ciudad}&checkin={checkin}&checkout={checkout}&group_adults=2&no_rooms=1&group_children=0'

    # Actualizar la página con la URL generada (sin abrir un nuevo navegador)
    driver.get(url)
    time.sleep(5)

    # Cerrar el pop-up, si aparece
    try:
        close_popup_button = driver.find_element(By.XPATH, '//button[@aria-label="Ignorar información sobre el inicio de sesión."]')
        close_popup_button.click()
        time.sleep(2)
    except:
        pass

    # Buscar todos los elementos de hoteles
    hotels = driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')

    # Recorrer cada hotel y extraer la información
    for hotel in hotels:
        hotel_dict = {}
        try:
            hotel_dict['hotel'] = hotel.find_element(By.XPATH, './/div[@data-testid="title"]').text
        except:
            hotel_dict['hotel'] = None

        # Intentar obtener el precio alternativo, con descuento o el precio base
        try:
            hotel_dict['price'] = hotel.find_element(By.XPATH, './/span[@data-testid="price-and-discounted-price"]').text
        except:
            try:
                hotel_dict['price'] = hotel.find_element(By.XPATH, './/span[@data-testid="price-alternative"]').text  # Precio alternativo
            except:
                try:
                    hotel_dict['price'] = hotel.find_element(By.XPATH, './/span[@data-testid="price"]').text  # Precio base
                except:
                    hotel_dict['price'] = None

        try:
            hotel_dict['score'] = hotel.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[1]').text
        except:
            hotel_dict['score'] = None

        try:
            hotel_dict['avg review'] = hotel.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[2]/div[1]').text
        except:
            hotel_dict['avg review'] = None

        try:
            hotel_dict['reviews count'] = hotel.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[2]/div[2]').text.split()[0]
        except:
            hotel_dict['reviews count'] = None

        # Agregar ciudad, check-in y check-out al diccionario
        hotel_dict['ciudad'] = ciudad
        hotel_dict['check_in'] = checkin
        hotel_dict['check_out'] = checkout

        # Agregar el resultado a la lista global
        todos_los_hoteles.append(hotel_dict)

# Función para obtener los valores de entrada, generar el rango de fechas y ejecutar las búsquedas
def iniciar_busqueda():
    ciudad = ciudad_entry.get()
    checkin_str = checkin_entry.get()
    checkout_str = checkout_entry.get()

    # Verificar que todos los campos estén completos
    if not ciudad or not checkin_str or not checkout_str:
        tk.messagebox.showerror("Error", "Por favor, complete todos los campos")
        return

    # Convertir las fechas de check-in y check-out a objetos datetime
    try:
        checkin_date = datetime.strptime(checkin_str, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout_str, '%Y-%m-%d')
    except ValueError:
        tk.messagebox.showerror("Error", "Formato de fecha incorrecto. Use YYYY-MM-DD.")
        return

    # Configuración del driver de Selenium (Chrome) una vez
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Iterar sobre el rango de fechas de check-in
    current_date = checkin_date
    while current_date < checkout_date:
        next_date = current_date + timedelta(days=1)
        ejecutar_busqueda(driver, ciudad, current_date.strftime('%Y-%m-%d'), next_date.strftime('%Y-%m-%d'))
        current_date = next_date

    # Cerrar el navegador después de terminar todas las búsquedas
    driver.quit()

    # Guardar todos los resultados en un único archivo CSV al final del proceso
    df = pd.DataFrame(todos_los_hoteles)
    ruta_guardado = os.path.join(os.path.expanduser("~"), 'Documents', 'scraping_results', 'Hotels_Scraping')
    if not os.path.exists(ruta_guardado):
        os.makedirs(ruta_guardado)
    nombre_archivo = os.path.join(ruta_guardado, f'{ciudad}_{checkin_str}_to_{checkout_str}.csv')
    df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')

# Configuración de la ventana principal
root = tk.Tk()
root.title("Busqueda de Hoteles")
root.geometry("400x250")

# Campos de entrada
tk.Label(root, text="Ciudad:").pack(pady=5)
ciudad_entry = tk.Entry(root)
ciudad_entry.pack()

tk.Label(root, text="Check-in (YYYY-MM-DD):").pack(pady=5)
checkin_entry = tk.Entry(root)
checkin_entry.pack()

tk.Label(root, text="Check-out (YYYY-MM-DD):").pack(pady=5)
checkout_entry = tk.Entry(root)
checkout_entry.pack()

# Botón para ejecutar la búsqueda
tk.Button(root, text="Buscar", command=iniciar_busqueda).pack(pady=20)

root.mainloop()
