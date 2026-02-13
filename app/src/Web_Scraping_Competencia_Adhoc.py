"""
Web Scraping Competencia Ad-Hoc
Scraping de competidores en rango de fechas personalizado
"""
import re
from datetime import datetime, timedelta

from core.scraper import BookingBaseScraper
from utils.cleaner import DataCleaner
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
        cleaner = DataCleaner()
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
                hotel=comp_data.get('hotel') or comp_data.get('Hotel') or ''

                if not competidor or not ciudad:
                    logger.warning(f"⚠️ Datos incompletos: {comp_data}")
                    continue

                # Construir búsqueda: "Nombre Competidor Ciudad"
                competidor_ciudad = f"{competidor} {ciudad}"
                competidor_ciudad = re.sub(r"\s{1,10}", "+", competidor_ciudad)

                url = self.build_search_url(competidor_ciudad, checkin_str, checkout_str)
                logger.info(f"🔍 {competidor} | {checkin_str}")

                self.open_url(url)

                # Extraer datos usando métodos heredados
                try:
                    nombre = self.extract_name()
                    precio = self.extract_price()
                    puntuacion = self.extract_puntuacion()
                    calificacion_cualitativa = self.extract_calificacion_cualitativa()
                    comentarios = self.extract_comentarios()
                except Exception as e:
                    logger.warning(f"⚠️ {competidor} ({checkin_str}): {e}")
                    nombre = competidor
                    precio = "0"
                    calificacion_cualitativa = "No disponible"
                    puntuacion = "0"
                    comentarios = "No disponible"

                divisa, precio = cleaner.limpiar_precio(precio)
                results.append({
                    'hotel': hotel,
                    'divisa': divisa,
                    'precio': precio,
                    'review_promedio': calificacion_cualitativa,
                    'comentarios': comentarios,
                    'puntuacion': puntuacion,
                    'competidor': nombre,
                    'ciudad': ciudad,
                    'check_in': checkin_str,
                    'check_out': checkout_str
                })

                logger.info(f"✅ {competidor} - {precio}")

            # Avanzar al siguiente día
            fecha_actual = siguiente_dia

        return results
