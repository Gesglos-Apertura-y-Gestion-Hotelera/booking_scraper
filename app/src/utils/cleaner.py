from .logger import logger

class DataCleaner:
    """Responsabilidad: Limpiar y transformar campos específicos."""

    def limpiar_precio(self, price_raw):
        if not price_raw:
            return ["", ""]

        precio, divisa = self.extract_min_price(price_raw)

        if (precio and divisa) and precio != "":
            return divisa, precio

        if (precio and not divisa) and precio != "":
            return "COP ", precio

        partes = str(price_raw).split(" ")

        if len(partes) >= 2:
            currency = partes[0].strip()
            price = partes[1].replace('.', '').strip()
            return [currency, price]

        return ["", ""]

    def extract_min_price(self, raw_price):
        multiples_precios = str(raw_price).split("COP ")
        try:
            if len(multiples_precios) >= 3:
                price_1 = 0
                price_2 = 0
                if multiples_precios[0] != "":
                    price_1 = int(multiples_precios[0].strip())
                if multiples_precios[1] != "":
                    price_2 = int(multiples_precios[1].strip())
                divisa = "COP"
                return min(price_1, price_2), divisa

            return None, None
        except ValueError:
            logger.error(f"El price no puede ser igual a <{raw_price}>")
            return "", ""
