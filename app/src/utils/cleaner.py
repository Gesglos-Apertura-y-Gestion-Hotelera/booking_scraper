import re




import requests
import json
import re

from .logger import logger


class DataCleaner:
    """Responsabilidad: Limpiar y transformar campos específicos."""

    @staticmethod
    def limpiar_calificacion(calif_raw):
        logger.info(f"\n\ncalificacion  -{calif_raw}-")
        if not calif_raw or '\n' not in str(calif_raw):
            return ["", "", ""]
        partes = calif_raw.split('\n')
        score = partes[1].strip() if len(partes) > 1 else ""
        avg_review = partes[2].strip() if len(partes) > 2 else ""

        count_raw = partes[3] if len(partes) > 3 else ""
        reviews_count = re.sub(r'\D', '', count_raw)

        return [score, avg_review, reviews_count]

    def limpiar_precio(self, price_raw):
        if not price_raw:
            return ["", ""]

        partes = str(price_raw).split(" ")
        if len(partes) >= 2:
            currency = partes[0].strip()
            price = partes[1].replace('.', '').strip()
            return [currency, price]

        return ["", ""]

    def clean_rating_details(self, rating_details: str):
        rating_details = re.sub(r"Puntuación:\s{1,3}No disponible\s{1,3}", "", rating_details)
        rating_details = re.sub(r"\d{1,10}\s{1,10}comentarios", "", rating_details)
        return rating_details

class DataTransformer:
    """Responsabilidad: Mapear diccionarios a listas para Sheets."""

    def __init__(self, cleaner: DataCleaner):
        self.cleaner = cleaner

    def transformar_hoteles(self, lista_datos):
        filas = []
        for d in lista_datos:
            # Limpiar precio
            score_data1 = self.cleaner.limpiar_precio(d.get('precio', ''))
            score_data2 = self.cleaner.limpiar_calificacion(d.get('calificacion', ''))

            # Usar datos originales si existen, si no usar los procesados
            fila = {
                'divisa': d.get('divisa') or score_data1[0],
                'precio': d.get('precio') if 'divisa' in d else score_data1[1],
                'calificacion': d.get('calificacion') if 'review_promedio' in d else score_data2[0],
                'review_promedio': d.get('review_promedio') or score_data2[1],
                'comentarios': d.get('comentarios') or score_data2[2],
                'puntaje': d.get('puntaje', ''),
                'ciudad': d.get('ciudad', ''),
                'check_in': d.get('check_in', ''),
                'check_out': d.get('check_out', ''),
                'hotel': d.get('hotel', ''),
                'competidor': d.get('competidor', '')
            }
            filas.append(fila)
        return filas

