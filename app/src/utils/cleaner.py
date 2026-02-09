import re

from numpy.lib.utils import deprecate

from .logger import logger


class DataCleaner:
    """Responsabilidad: Limpiar y transformar campos específicos."""

    def limpiar_precio(self, price_raw):
        if not price_raw:
            return ["", ""]

        partes = str(price_raw).split(" ")
        if len(partes) >= 2:
            currency = partes[0].strip()
            price = partes[1].replace('.', '').strip()
            return [currency, price]

        return ["", ""]

