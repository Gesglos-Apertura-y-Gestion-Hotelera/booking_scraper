"""
Modelos de datos compartidos para todos los scrapers
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class HotelSearchData:
    """Datos de entrada para búsqueda (genérico para clientes y competencia)"""
    hotel: str
    ciudad: str
    competidor: str = ''

    @classmethod
    def from_dict(cls, data: Dict):
        """Crea instancia desde diccionario con normalización de keys"""
        # Intenta diferentes variantes de nombres de columnas
        nombre = (
            data.get('nombre') or
            data.get('hotel') or
            data.get('competidor') or
            ''
        )
        ciudad = data.get('ciudad', '')

        return cls(hotel=nombre, ciudad=ciudad, competidor=nombre)


@dataclass
class HotelResult:
    """Resultado del scraping (único modelo para ambos casos)"""
    nombre: str
    precio: str
    calificacion: str
    ciudad: str
    check_in: str
    check_out: str
    origen: Optional[str] = None  # Para saber de qué hotel/competidor viene

    def to_dict(self) -> Dict:
        result = {
            'nombre': self.nombre,
            'precio': self.precio,
            'calificacion': self.calificacion,
            'ciudad': self.ciudad,
            'check_in': self.check_in,
            'check_out': self.check_out
        }

        # Agregar campo 'origen' o 'competidor' si está presente
        if self.origen:
            result['origen'] = self.origen

        return result