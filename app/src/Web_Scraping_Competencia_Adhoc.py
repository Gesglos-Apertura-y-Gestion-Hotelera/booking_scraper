import os
import time
import pandas as pd
from tkinter import Tk, Label, Entry, Button, messagebox
from tkinter.filedialog import askopenfilename
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Función para iniciar la búsqueda diaria
def iniciar_busqueda():
    # Obtener fechas de check-in y check-out desde la ventana emergente
    checkin_str = checkin_entry.get()
    checkout_str = checkout_entry.get()

    # Convertir las fechas ingresadas a objetos datetime
    try:
        checkin = datetime.strptime(checkin_str, '%Y-%m-%d')
        checkout = datetime.strptime(checkout_str, '%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Error", "Formato de fecha incorrecto. Use YYYY-MM-DD.")
        return

    # Validar que el rango de fechas sea correcto
    if checkin >= checkout:
        messagebox.showerror("Error", "La fecha de check-out debe ser posterior a la de check-in.")
        return

    # Abrir cuadro de diálogo para seleccionar el archivo
    Tk().withdraw()
    ruta_archivo = askopenfilename(title="Selecciona el archivo Excel", filetypes=[("Archivos Excel", "*.xlsx")])

    try:
        # Cargar el archivo seleccionado
        df = pd.read_excel(ruta_archivo, sheet_name='Competencia')
        competencia_ciudades = df[['Competidor', 'Ciudad']].to_dict(orient='records')
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar el archivo Excel: {e}")
        return

    # Configuración del driver de Selenium (Chrome)
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Lista para almacenar los datos de los competidores
    hotels_list = []

    # Iterar sobre cada día en el rango de fechas
    fecha_actual = checkin
    while fecha_actual < checkout:
        siguiente_dia = fecha_actual + timedelta(days=1)
        checkin_str = fecha_actual.strftime('%Y-%m-%d')
        checkout_str = siguiente_dia.strftime('%Y-%m-%d')

        # Iterar sobre cada competidor y realizar la búsqueda diaria
        for competencia_info in competencia_ciudades:
            competencia = competencia_info['Competidor']
            ciudad = competencia_info['Ciudad']
            url = f'https://www.booking.com/searchresults.es.html?ss={competencia}%20{ciudad}&checkin={checkin_str}&checkout={checkout_str}&group_adults=2&no_rooms=1&group_children=0'

            driver.get(url)
            time.sleep(5)

            # Cerrar el pop-up, si aparece
            try:
                close_popup_button = driver.find_element(By.XPATH, '//button[@aria-label="Ignorar información sobre el inicio de sesión."]')
                close_popup_button.click()
                time.sleep(2)
            except Exception:
                pass

            # Crear un diccionario para almacenar la información del competidor
            hotel_dict = {}

            try:
                # Capturar precios en orden de prioridad
                try:
                    precio_alternativo = driver.find_element(By.CSS_SELECTOR, 'div.abf093bdfe.fc23698243')
                    hotel_dict['precio'] = precio_alternativo.text.replace("Desde ", "").strip()
                except Exception:
                    try:
                        precio_descuento = driver.find_element(By.CSS_SELECTOR, '[data-testid="price-and-discounted-price"]')
                        hotel_dict['precio'] = precio_descuento.text.strip()
                    except Exception:
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
            hotel_dict['check_in'] = checkin_str
            hotel_dict['check_out'] = checkout_str

            hotels_list.append(hotel_dict)

        # Avanzar al siguiente día en el rango
        fecha_actual = siguiente_dia

    # Guardar los datos en un archivo CSV consolidado
    df_hotels = pd.DataFrame(hotels_list)
    home_dir = os.path.expanduser("~")
    ruta_guardado = os.path.join(home_dir, 'Documents', 'scraping_results', 'Competencia_Adhoc')
    if not os.path.exists(ruta_guardado):
        os.makedirs(ruta_guardado)

    nombre_archivo = os.path.join(ruta_guardado, f'{checkin_entry.get()}_to_{checkout_entry.get()}.csv')
    df_hotels.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    messagebox.showinfo("Guardado", f"Archivo guardado en: {nombre_archivo}")

    # Cerrar el navegador al finalizar
    driver.quit()

# Configuración de la ventana principal para solicitar las fechas
root = Tk()
root.title("Búsqueda de Competidores Diaria")
root.geometry("400x200")

Label(root, text="Check-in (YYYY-MM-DD):").pack(pady=5)
checkin_entry = Entry(root)
checkin_entry.pack()

Label(root, text="Check-out (YYYY-MM-DD):").pack(pady=5)
checkout_entry = Entry(root)
checkout_entry.pack()

Button(root, text="Buscar", command=iniciar_busqueda).pack(pady=20)

root.mainloop()

