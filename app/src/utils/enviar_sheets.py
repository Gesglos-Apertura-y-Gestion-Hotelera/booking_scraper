import requests
import json


from .logger import logger
from .cleaner import DataCleaner, DataTransformer

class GoogleSheetsClient:
    """Responsabilidad: Comunicación externa con la API."""

    def __init__(self, url: str):
        self.url = url

    def enviar(self, datos, sheet_name: str):
        try:
            import pprint as pp
            print (f"\n\nDATOS  {pp.pformat(datos)}")

            payload = {
                'data': datos,
                'sheet': sheet_name
            }

            response = requests.post(
                self.url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            logger.info(f"response:  {response.text}")
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red: {e}")
            return False

# --- FUNCIÓN PRINCIPAL (ORQUESTADORA) ---
def enviar_sheets(lista_datos, url_apps_script, sheet_name: str):
    if not lista_datos:
        logger.info("⚠️ La lista está vacía.")
        return

    # Inyección de dependencias
    cleaner = DataCleaner()
    transformer = DataTransformer(cleaner)
    client = GoogleSheetsClient(url_apps_script)

    # Flujo de trabajo
    datos_listos = transformer.transformar_hoteles(lista_datos)

    if client.enviar(datos_listos, sheet_name):
        logger.info(f"✅ Éxito: {len(datos_listos)} filas procesadas y enviadas a '{sheet_name}'.")
