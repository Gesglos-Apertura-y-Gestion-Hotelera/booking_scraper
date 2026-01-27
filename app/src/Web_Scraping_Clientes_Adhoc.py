#!/usr/bin/env python3
"""
Web Scraping Clientes - Búsqueda Adhoc (múltiples noches)
"""
import sys
import json
from datetime import datetime, timedelta
from typing import List, Optional
from tkinter import Tk, Label, Entry, Button, messagebox
from tkinter.filedialog import askopenfilename

import pandas as pd

from utils.logger import logger
from core.chrome_driver import ChromeDriverFactory
from core.base_scraper import BookingBaseScraper
from core.data_models import HotelSearchData


class ClientesAdhocScraper(BookingBaseScraper):
    """Scraper para búsqueda adhoc con rango de fechas"""

    def __init__(self, driver, hotels_data: List[HotelSearchData],
                 checkin: datetime, checkout: datetime):
        super().__init__(driver)
        self.hotels_data = hotels_data
        self.checkin = checkin
        self.checkout = checkout

    def run(self) -> List[dict]:
        """
        Ejecuta scraping para todos los hoteles
        Itera día por día en el rango de fechas
        """
        results = []
        fecha_actual = self.checkin

        while fecha_actual < self.checkout:
            siguiente_dia = fecha_actual + timedelta(days=1)
            checkin_str = fecha_actual.strftime('%Y-%m-%d')
            checkout_str = siguiente_dia.strftime('%Y-%m-%d')

            logger.info(f"📅 Procesando: {checkin_str}")

            for hotel_data in self.hotels_data:
                try:
                    result = self.search_hotel(hotel_data, checkin_str, checkout_str)
                    results.append(result.to_dict())
                    logger.info(f"✅ {result.nombre} - {result.precio}")
                except Exception as e:
                    logger.error(f"❌ Error con {hotel_data.hotel}: {e}")
                    results.append({
                        'nombre': hotel_data.hotel,
                        'precio': '0',
                        'calificacion': 'Error',
                        'ciudad': hotel_data.ciudad,
                        'check_in': checkin_str,
                        'check_out': checkout_str
                    })

            fecha_actual = siguiente_dia

        return results


def load_data_from_excel() -> List[HotelSearchData]:
    """Carga datos desde archivo Excel seleccionado por el usuario"""
    Tk().withdraw()
    filepath = askopenfilename(
        title="Selecciona el archivo Excel",
        filetypes=[("Archivos Excel", "*.xlsx")]
    )

    if not filepath:
        raise ValueError("No se seleccionó archivo")

    df = pd.read_excel(filepath, sheet_name='Cliente')
    logger.info(f"✅ Excel cargado: {len(df)} hoteles")

    return [
        HotelSearchData(hotel=row['Hotel'], ciudad=row['Ciudad'])
        for _, row in df.iterrows()
    ]


def load_data_from_json(json_str: str) -> List[HotelSearchData]:
    """Carga datos desde JSON"""
    data = json.loads(json_str)
    logger.info(f"✅ JSON cargado: {len(data)} hoteles")
    return [HotelSearchData.from_dict(item) for item in data]


def save_results(results: List[dict], checkin: str, checkout: str):
    """Guarda resultados en CSV"""
    import os

    df = pd.DataFrame(results)
    home_dir = os.path.expanduser("~")
    save_dir = os.path.join(home_dir, 'Documents', 'scraping_results', 'Clientes_Adhoc')

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    filename = os.path.join(save_dir, f'{checkin}_to_{checkout}.csv')
    df.to_csv(filename, index=False, encoding='utf-8-sig')

    logger.info(f"💾 Guardado en: {filename}")
    return filename


def run_with_gui():
    """Modo GUI con entrada de fechas"""

    def on_search():
        try:
            # Obtener fechas
            checkin_str = checkin_entry.get()
            checkout_str = checkout_entry.get()
            checkin = datetime.strptime(checkin_str, '%Y-%m-%d')
            checkout = datetime.strptime(checkout_str, '%Y-%m-%d')

            # Cerrar ventana
            root.destroy()

            # Cargar datos
            hotels_data = load_data_from_excel()

            # Ejecutar scraping
            driver = ChromeDriverFactory.create_gui_driver()
            ChromeDriverFactory.setup_booking_cookies(driver)

            try:
                scraper = ClientesAdhocScraper(driver, hotels_data, checkin, checkout)
                results = scraper.run()

                # Guardar
                filename = save_results(results, checkin_str, checkout_str)
                messagebox.showinfo("Completado", f"Guardado en:\n{filename}")

            finally:
                driver.quit()

        except ValueError as e:
            messagebox.showerror("Error", f"Formato de fecha incorrecto: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Crear ventana
    root = Tk()
    root.title("Búsqueda Adhoc de Hoteles")
    root.geometry("400x200")

    Label(root, text="Check-in (YYYY-MM-DD):").pack(pady=5)
    checkin_entry = Entry(root)
    checkin_entry.pack()

    Label(root, text="Check-out (YYYY-MM-DD):").pack(pady=5)
    checkout_entry = Entry(root)
    checkout_entry.pack()

    Button(root, text="Buscar", command=on_search).pack(pady=20)

    root.mainloop()


def run_headless(json_str: str, checkin_str: str, checkout_str: str):
    """Modo headless para Docker"""
    checkin = datetime.strptime(checkin_str, '%Y-%m-%d')
    checkout = datetime.strptime(checkout_str, '%Y-%m-%d')

    hotels_data = load_data_from_json(json_str)

    driver = ChromeDriverFactory.create_headless_driver()
    ChromeDriverFactory.setup_booking_cookies(driver)

    try:
        scraper = ClientesAdhocScraper(driver, hotels_data, checkin, checkout)
        results = scraper.run()

        filename = save_results(results, checkin_str, checkout_str)
        logger.info(f"✅ COMPLETADO: {len(results)} resultados")

    finally:
        driver.quit()


def main():
    """Punto de entrada"""
    logger.info("🚀 SCRAPING CLIENTES ADHOC")

    if len(sys.argv) >= 3:
        # Modo headless: main.py '[json]' '2025-01-01' '2025-01-31'
        json_data = sys.argv[1]
        checkin = sys.argv[2]
        checkout = sys.argv[3]
        run_headless(json_data, checkin, checkout)
    else:
        # Modo GUI
        run_with_gui()


if __name__ == "__main__":
    main()