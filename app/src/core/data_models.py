"""
Modelos de datos compartidos para todos los scrapers
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class HotelSearchData:
    """Datos de entrada para búsqueda"""
    hotel: str
    ciudad: str

    @classmethod
    def from_dict(cls, data: Dict):
        """Crea instancia desde diccionario con normalización de keys"""
        return cls(
            hotel=data.get('hotel', data.get('Hotel', '')),
            ciudad=data.get('ciudad', data.get('Ciudad', ''))
        )


@dataclass
class HotelResult:
    """Resultado del scraping"""
    nombre: str
    precio: str
    calificacion: str
    ciudad: str
    check_in: str
    check_out: str

    def to_dict(self) -> Dict:
        return {
            'nombre': self.nombre,
            'precio': self.precio,
            'calificacion': self.calificacion,
            'ciudad': self.ciudad,
            'check_in': self.check_in,
            'check_out': self.check_out
        }