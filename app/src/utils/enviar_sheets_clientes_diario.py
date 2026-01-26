import requests
import json
import re

class DataCleaner:
    """Responsabilidad: Limpiar y transformar campos específicos."""
    @staticmethod
    def limpiar_calificacion(calif_raw):
        if not calif_raw or '\n' not in str(calif_raw):
            return ["", "", ""]
        
        partes = calif_raw.split('\n')
        score = partes[1].strip() if len(partes) > 1 else ""
        avg_review = partes[2].strip() if len(partes) > 2 else ""
        
        count_raw = partes[3] if len(partes) > 3 else ""
        reviews_count = re.sub(r'\D', '', count_raw)
        
        return [score, avg_review, reviews_count]

class DataTransformer:
    """Responsabilidad: Mapear diccionarios a listas para Sheets."""
    def __init__(self, cleaner: DataCleaner):
        self.cleaner = cleaner

    def transformar_hoteles(self, lista_datos):
        filas = []
        for d in lista_datos:
            score_data = self.cleaner.limpiar_calificacion(d.get('calificacion', ''))
            
            fila = [
                d.get('precio', ''),
                d.get('nombre', ''),
                *score_data,  # Desempaqueta score, avg_review y count
                d.get('ciudad', ''),
                d.get('check_in', ''),
                d.get('check_out', '')
            ]
            filas.append(fila)
        return filas

class GoogleSheetsClient:
    """Responsabilidad: Comunicación externa con la API."""
    def __init__(self, url: str):
        self.url = url

    def enviar(self, datos):
        try:
            response = requests.post(
                self.url,
                data=json.dumps(datos),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red: {e}")
            return False

# --- FUNCIÓN PRINCIPAL (ORQUESTADORA) ---
def enviar_sheets_diario(lista_datos, url_apps_script):
    if not lista_datos:
        print("⚠️ La lista está vacía.")
        return

    # Inyección de dependencias
    cleaner = DataCleaner()
    transformer = DataTransformer(cleaner)
    client = GoogleSheetsClient(url_apps_script)

    # Flujo de trabajo
    datos_listos = transformer.transformar_hoteles(lista_datos)
    
    if client.enviar(datos_listos):
        print(f"✅ Éxito: {len(datos_listos)} filas procesadas y enviadas.")