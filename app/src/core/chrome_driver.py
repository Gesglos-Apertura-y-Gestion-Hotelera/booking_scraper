"""
Configuración y setup de Chrome WebDriver
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from utils.logger import logger


class ChromeDriverFactory:
    """Factory para crear drivers de Chrome configurados"""

    BOOKING_BASE_URL = 'https://www.booking.com'

    @staticmethod
    def create_headless_driver() -> WebDriver:
        """Crea driver headless para Docker/producción"""
        options = webdriver.ChromeOptions()

        # Opciones para Docker
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--window-size=1920,1080')

        # Configuración Colombia/COP
        options.add_argument('--lang=es-CO')
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'es-CO,es,en',
        })

        # Anti-detección
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/144.0.0.0 Safari/537.36'
        )

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("✅ Chrome headless iniciado")

        return driver

    @staticmethod
    def setup_booking_cookies(driver: WebDriver):
        """Establece cookies de Booking.com para COP"""
        try:
            driver.get(ChromeDriverFactory.BOOKING_BASE_URL)
            time.sleep(2)

            driver.add_cookie({
                'name': 'currency',
                'value': 'COP',
                'domain': '.booking.com'
            })
            driver.add_cookie({
                'name': 'selected_currency',
                'value': 'COP',
                'domain': '.booking.com'
            })
            logger.info("✅ Cookies COP establecidas")
        except Exception as e:
            logger.warning(f"⚠️ Error con cookies: {e}")