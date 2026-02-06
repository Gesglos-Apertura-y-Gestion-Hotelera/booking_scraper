"""
Web Scraping Competencia Ad-Hoc
Scraping de competidores en rango de fechas personalizado
"""
import os
import re
import time
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from core.chrome_driver import ChromeDriverFactory
from utils.cleaner import DataCleaner
from utils.enviar_sheets import enviar_sheets
from utils.logger import logger


class CompetenciaDiarioScraperAdHoc(BookingBaseScraper):
    """
    Scraper Ad-Hoc para búsqueda de competidores en rango de fechas.
    Reutiliza toda la lógica de BookingBaseScraper.
    """

    def __init__(self, driver, competidores: list, check_in: datetime, check_out: datetime):
        """
        Args:
            driver: Instancia de Selenium WebDriver
            competidores: Lista de dicts con 'competidor'/'Competidor' y 'ciudad'/'Ciudad'
            check_in: Fecha inicial (datetime)
            check_out: Fecha final (datetime)
        """
        super().__init__(driver)
        self.competidores = competidores
        self.check_in = check_in
        self.check_out = check_out

    def run(self) -> list:
        """
        Ejecuta scraping para todos los competidores en el rango de fechas.
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

            # Iterar sobre cada competidor
            for comp_data in self.competidores:
                if not isinstance(comp_data, dict):
                    logger.error(f"❌ Elemento no es dict: {type(comp_data)}")
                    continue

                # Normalizar claves (mayúsculas o minúsculas)
                competidor = comp_data.get('competidor') or comp_data.get('Competidor') or ''
                ciudad = comp_data.get('ciudad') or comp_data.get('Ciudad') or ''

                if not competidor or not ciudad:
                    logger.warning(f"⚠️ Datos incompletos: {comp_data}")
                    continue

                # Construir búsqueda: "Nombre Competidor Ciudad"
                competidor_ciudad = f"{competidor} {ciudad}"
                competidor_ciudad = re.sub(r"\s{1,10}", "+", competidor_ciudad)

                url = self.build_search_url(competidor_ciudad, checkin_str, checkout_str)
                logger.info(f"🔍 {competidor} | {checkin_str}")

                self.driver.get(url)
                time.sleep(1)
                self.close_popup()
                time.sleep(1)

                # Extraer datos usando métodos heredados
                try:
                    nombre = self.extract_name()
                    precio = self.extract_price()
                    calificacion = self.extract_rating_details()
                except Exception as e:
                    logger.warning(f"⚠️ {competidor} ({checkin_str}): {e}")
                    nombre = competidor
                    precio = "0"
                    calificacion = "No disponible"

                cleaner = DataCleaner()
                divisa, precio = cleaner.limpiar_precio(precio)
                results.append({
                    'hotel': nombre,
                    'divisa': divisa,
                    'precio': precio,
                    'review_promedio': calificacion.get("calificacion_cualitativa"),
                    'comentarios': calificacion.get("comentarios"),
                    'puntuacion': calificacion.get("puntuacion"),
                    'competidor': competidor,
                    'ciudad': ciudad,
                    'check_in': checkin_str,
                    'check_out': checkout_str
                })

                logger.info(f"✅ {nombre} - {precio}")

            # Avanzar al siguiente día
            fecha_actual = siguiente_dia

        return results


def buscar_competencia_adhoc(
        competidores: list,
        check_in: datetime,
        check_out: datetime,
        webapp_url: str = None
):
    """
    Función principal para ejecutar el scraper ad-hoc de competencia.

    Args:
        competidores: Lista de competidores a buscar
        check_in: Fecha inicial
        check_out: Fecha final
        webapp_url: URL opcional para enviar resultados a Google Sheets
    """
    logger.info("🚀 SCRAPING COMPETENCIA AD-HOC")
    logger.info(f"📅 Rango: {check_in.strftime('%Y-%m-%d')} → {check_out.strftime('%Y-%m-%d')}")
    logger.info(f"🏨 Competidores: {len(competidores)}")

    driver = None
    try:
        # Crear driver
        driver = ChromeDriverFactory.create_headless_driver()
        ChromeDriverFactory.setup_booking_cookies(driver)

        # Ejecutar scraping
        scraper = CompetenciaDiarioScraperAdHoc(driver, competidores, check_in, check_out)
        results = scraper.run()

        # Enviar a Sheets si se proporciona URL
        if webapp_url:
            logger.info(f"📤 Enviando {len(results)} resultados a Sheets")
            enviar_sheets(results, os.environ.get('WEBAPP_URL'), sheet_name="competencia")

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
    # codigo para pruebas unitarias

    # Datos de prueba
    fake_competidores = [
        {'Competidor': 'Hilton Bogotá', 'Ciudad': 'Bogotá'},
        {'Competidor': 'Marriott Bogotá', 'Ciudad': 'Bogotá'},
        {'Competidor': 'Sheraton Bogotá', 'Ciudad': 'Bogotá'},
    ]

    # Rango de 3 días desde hoy
    fecha_inicio = datetime.now()
    fecha_fin = datetime.now() + timedelta(days=3)

    # Ejecutar
    resultados = buscar_competencia_adhoc(
        competidores=fake_competidores,
        check_in=fecha_inicio,
        check_out=fecha_fin,
        webapp_url=None
    )

    # # Mostrar resultados
    # print(f"\n{'=' * 80}")
    # print(f"Total de resultados: {len(resultados)}")
    # print(f"{'=' * 80}\n")
    #
    # for comp in resultados:
    #     print(f"🏨 {comp['nombre']}")
    #     print(f"   🏷️  Competidor: {comp['competidor']}")
    #     print(f"   📍 {comp['ciudad']}")
    #     print(f"   💰 {comp['precio']}")
    #     print(f"   ⭐ {comp['calificacion']}")
    #     print(f"   📅 {comp['check_in']} → {comp['check_out']}")
    #     print("-" * 80)