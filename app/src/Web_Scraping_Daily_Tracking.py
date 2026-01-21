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

# Obtener la fecha actual para check-in y sumar un día para check-out
checkin = datetime.today().date()
checkout = checkin + timedelta(days=1)

# Abrir cuadro de diálogo para seleccionar el archivo
Tk().withdraw()  # Evitar que aparezca la ventana principal de Tkinter
ruta_archivo = askopenfilename(title="Selecciona el archivo Excel", filetypes=[("Archivos Excel", "*.xlsx")])

# Validar que se haya seleccionado un archivo
if not ruta_archivo:
    print("No se seleccionó ningún archivo. El programa terminará.")
    exit()

# Cargar el archivo seleccionado
try:
    df = pd.read_excel(ruta_archivo, sheet_name='Cliente')
except Exception as e:
    print(f"Error al cargar el archivo Excel: {e}")
    exit()

# Suponiendo que las ciudades están en una columna llamada 'Ciudad'
# Remover duplicados y considerar solo texto antes de la coma
try:
    ciudades = list({ciudad.split(",")[0].strip() for ciudad in df['Ciudad'].tolist() if isinstance(ciudad, str)})
except KeyError:
    print("La columna 'Ciudad' no se encontró en el archivo. El programa terminará.")
    exit()

# Configuración del driver de Selenium (Chrome)
options = webdriver.ChromeOptions()
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
except Exception as e:
    print(f"Error al inicializar el driver de Selenium: {e}")
    exit()

# Lista para almacenar todos los datos de hoteles
hotels_list = []

# Iterar sobre la lista de ciudades únicas y procesadas
for ciudad in ciudades:
    print(f"Procesando la ciudad: {ciudad}")
    # Crear la URL dinámicamente para cada ciudad
    url = f'https://www.booking.com/searchresults.es.html?ss={ciudad}&checkin={checkin}&checkout={checkout}&group_adults=2&no_rooms=1&group_children=0'
    
    # Abrir la página con la URL generada
    try:
        driver.get(url)
        time.sleep(5)  # Esperar a que se cargue la página
    except Exception as e:
        print(f"Error al cargar la página para la ciudad {ciudad}: {e}")
        continue

    # Cerrar pop-up si aparece
    try:
        close_popup_button = driver.find_element(By.XPATH, '//button[@aria-label="Ignorar información sobre el inicio de sesión."]')
        close_popup_button.click()
        time.sleep(2)  # Espera breve para asegurarse de que el pop-up desaparezca
    except Exception:
        print(f"No se pudo cerrar el pop-up en {ciudad} (si existía).")

    # Buscar todos los elementos de hoteles
    try:
        hotels = driver.find_elements(By.XPATH, '//div[@data-testid="property-card"]')
        if not hotels:
            print(f"No se encontraron hoteles para la ciudad {ciudad}.")
            continue
    except Exception as e:
        print(f"Error al buscar hoteles para la ciudad {ciudad}: {e}")
        continue

    # Recorrer cada hotel y extraer la información
    for hotel in hotels:
        hotel_dict = {}
        
        # Extraer nombre del hotel
        try:
            hotel_dict['hotel'] = hotel.find_element(By.XPATH, './/div[@data-testid="title"]').text
        except:
            hotel_dict['hotel'] = "No disponible"
        
        # Extraer el precio con descuento (si existe) o el precio base
        try:
            # Intentar obtener el precio con descuento
            hotel_dict['price'] = hotel.find_element(By.XPATH, './/span[@data-testid="price-and-discounted-price"]').text
        except:
            # Si no se encuentra un precio con descuento, intentar el precio base
            try:
                hotel_dict['price'] = hotel.find_element(By.XPATH, './/span[@data-testid="price"]').text
            except:
                hotel_dict['price'] = "No disponible"
        
        # Extraer calificación
        try:
            hotel_dict['score'] = hotel.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[1]').text
        except:
            hotel_dict['score'] = "No disponible"
        
        # Extraer reseña promedio
        try:
            hotel_dict['avg review'] = hotel.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[2]/div[1]').text
        except:
            hotel_dict['avg review'] = "No disponible"
        
        # Extraer el número de reseñas
        try:
            hotel_dict['reviews count'] = hotel.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[2]/div[2]').text.split()[0]
        except:
            hotel_dict['reviews count'] = "No disponible"
        
        # Agregar ciudad, check-in y check-out al diccionario de cada hotel
        hotel_dict['ciudad'] = ciudad
        hotel_dict['check_in'] = checkin
        hotel_dict['check_out'] = checkout

        hotels_list.append(hotel_dict)

# Crear un DataFrame con todos los datos recopilados
df_hotels = pd.DataFrame(hotels_list)

# Definir la carpeta de guardado
home_dir = os.path.expanduser("~")
ruta_guardado = os.path.join(home_dir, 'Documents', 'scraping_results', 'Daily_Tracking')
if not os.path.exists(ruta_guardado):
    os.makedirs(ruta_guardado)

# Guardar el DataFrame completo en un único archivo CSV
nombre_archivo = os.path.join(ruta_guardado, f'{checkin}.csv')
try:
    df_hotels.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    print(f"Archivo guardado en: {nombre_archivo}")
except Exception as e:
    print(f"Error al guardar el archivo: {e}")

# Cerrar el navegador al finalizar
driver.quit()

