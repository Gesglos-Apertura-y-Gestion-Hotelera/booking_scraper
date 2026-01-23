import os
import time
import pandas as pd
from logger import logger
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from enviar_sheets_clientes_diario import enviar_sheets_diario

# Obtener la fecha actual y sumar un día para el check-out
checkin = datetime.now().strftime('%Y-%m-%d')
checkout = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# TODO: cambiar la direccion del archivo parametros para pasarlo dinamicamente
# Cargar el archivo seleccionado
nombre_archivo= "/app/database/Parametros.xlsx"


# Verificar si el archivo existe
if not os.path.exists(nombre_archivo):
    logger.error(f"Archivo NO existe: {nombre_archivo}")
    logger.error(f"Listando directorio database: {os.listdir('/app/database') if os.path.exists('/app/database') else 'No existe /app/database'}")
    exit(1)

try:
    df = pd.read_excel(nombre_archivo, sheet_name='Cliente')
    logger.info(f"✅ Archivo cargado exitosamente: {nombre_archivo} ({len(df)} filas)")
except FileNotFoundError:
    logger.error(f"❌ Archivo no encontrado: {nombre_archivo}")
    exit(1)
except Exception as e:
    logger.error(f"❌ Error cargando Excel: {str(e)}")
    exit(1)

# Suponiendo que los clientes están en columnas llamadas 'Hotel' y 'Ciudad'
clientes_ciudades = df[['Hotel', 'Ciudad']].to_dict(orient='records')

# Configuración del driver de Selenium (Chrome)
options = webdriver.ChromeOptions()

# Opciones esenciales para Docker
options.add_argument('--headless=new')  # Modo headless moderno
options.add_argument('--no-sandbox')  # Bypass OS security model (necesario en Docker)
options.add_argument('--disable-dev-shm-usage')  # Superar limitaciones de /dev/shm
options.add_argument('--disable-gpu')  # Deshabilitar GPU
options.add_argument('--disable-extensions')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--window-size=1920,1080')  # Tamaño de ventana

# Opciones adicionales para estabilidad
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36')

# Configurar el servicio
service = Service(ChromeDriverManager().install())

try:
    driver = webdriver.Chrome(service=service, options=options)
    logger.info("✅ Chrome WebDriver iniciado correctamente")
except Exception as e:
    logger.error(f"❌ Error al iniciar Chrome: {str(e)}")
    exit(1)

# Lista para almacenar los datos de los hoteles
hotels_list = []

# Iterar sobre la lista de clientes
for cliente_info in clientes_ciudades:
    logger.info(f"Cliente: {cliente_info}")
    cliente = cliente_info['Hotel']
    ciudad = cliente_info['Ciudad']
    
    # Crear la URL dinámica para cada cliente
    url = f'https://www.booking.com/searchresults.es.html?ss={cliente}&checkin={checkin}&checkout={checkout}&group_adults=2&no_rooms=1&group_children=0'
    logger.info(f"URL generada: {url}")

    # Abrir la página con la URL generada
    driver.get(url)
    time.sleep(5)  # Esperar a que se cargue la página

    # Cerrar pop-up si aparece
    try:
        close_popup_button = driver.find_element(By.XPATH, '//button[@aria-label="Ignorar información sobre el inicio de sesión."]')
        close_popup_button.click()  # Cierra el pop-up
        time.sleep(2)  # Espera breve para asegurarse de que el pop-up desaparezca
    except Exception as e:
        logger.info(f"❌ No se pudo encontrar o cerrar el pop-up: {e}")

    # Crear un diccionario para almacenar la información del hotel
    hotel_dict = {}
    
    try:
        time.sleep(2)  # Pequeño tiempo de espera para asegurarse de que la página esté completamente cargada
        
        # Capturar precios en orden de prioridad
        try:
            # Precio alternativo (Desde)
            price_alternativo_element = driver.find_element(By.CSS_SELECTOR, 'div.abf093bdfe.fc23698243')
            hotel_dict['precio'] = price_alternativo_element.text.replace("Desde ", "").strip()  # Quita "Desde" y mantiene formato
        except Exception as e:
            try:
                # Precio con descuento
                price_descuento_element = driver.find_element(By.XPATH, '//span[@data-testid="price-and-discounted-price"]')
                hotel_dict['precio'] = price_descuento_element.text.strip()
            except Exception as e:
                try:
                    # Precio base
                    price_base_element = driver.find_element(By.CSS_SELECTOR, '[data-testid="price"]')
                    hotel_dict['precio'] = price_base_element.text.strip()
                except Exception as e:
                    hotel_dict['precio'] = "0"  # Ningún precio disponible

        # Extraer el nombre y la calificación del hotel si están disponibles
        hotel_dict['nombre'] = driver.find_element(By.CSS_SELECTOR, '[data-testid="title"]').text
        hotel_dict['calificacion'] = driver.find_element(By.CSS_SELECTOR, '[data-testid="review-score"]').text

    except Exception as e:
        logger.info(f"❌ No se pudo encontrar la información del hotel: {e}")
        hotel_dict['nombre'] = cliente
        hotel_dict['precio'] = "0"
        hotel_dict['calificacion'] = "No disponible"
    
    # Agregar ciudad, check-in y check-out al diccionario de cada hotel
    hotel_dict['ciudad'] = ciudad
    hotel_dict['check_in'] = checkin
    hotel_dict['check_out'] = checkout
    hotels_list.append(hotel_dict)

# Guardar los datos de cada cliente en un archivo CSV con las columnas deseadas
df_hotels = pd.DataFrame(hotels_list)

# Crear la carpeta de guardado si no existe
home_dir = os.path.expanduser("~")
ruta_guardado = os.path.join(home_dir, 'Documents', 'scraping_results', 'Clientes')
if not os.path.exists(ruta_guardado):
    os.makedirs(ruta_guardado)

# Nombre de archivo seguro
nombre_archivo = os.path.join(ruta_guardado, f'{checkin}.csv')

# Guardar solo las columnas necesarias
df_hotels[['precio', 'nombre', 'calificacion', 'ciudad', 'check_in', 'check_out']]#.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
#logger.info(f"Archivo guardado en: {nombre_archivo}")
#logger.info(f"df_hotels: {df_hotels}")



URL_WEBAPP="https://script.google.com/macros/s/AKfycbyPzxk_tlVrVvQlZg0k8M0g_lIRifVqgf5EdA7EsdeMGdoHPYwNsZAiRN0Zk0U6EUbl/exec"
logger.info(hotels_list)
enviar_sheets_diario(hotels_list, URL_WEBAPP)
# Cerrar el navegador al finalizar
driver.quit()
