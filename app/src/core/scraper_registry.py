# Mapeo de script_key a clases de scraper
SCRAPER_REGISTRY = {
    'clientes_diario': {
        'module': 'Web_Scraping_Clientes',
        'class': 'ClientesDiarioScraper',
        'requires_dates': False,
        'data_param': 'hoteles',
        'sheet_name': 'clientes',
        'description': 'Scraping diario de clientes (hoy)'
    },
    'clientes_prevision': {
        'module': 'Web_Scraping_Clientes_Adhoc',
        'class': 'ClientesDiarioScraperAdHoc',
        'requires_dates': True,
        'data_param': 'hoteles',
        'sheet_name': 'clientes',
        'description': 'Scraping de clientes en rango de fechas'
    },
    'competencia_diario': {
        'module': 'Web_Scraping_Competencia',
        'class': 'CompetenciaDiarioScraper',
        'requires_dates': False,
        'data_param': 'competidores',
        'sheet_name': 'competencia',
        'description': 'Scraping diario de competencia (hoy)'
    },
    'competencia_prevision': {
        'module': 'Web_Scraping_Competencia_Adhoc',
        'class': 'CompetenciaDiarioScraperAdHoc',
        'requires_dates': True,
        'data_param': 'competidores',
        'sheet_name': 'competencia',
        'description': 'Scraping de competencia en rango de fechas'
    },
    'seguimiento_diario': {
        'module': 'Web_Scraping_Daily_Tracking',
        'class': 'DailyTrackingScraper',
        'requires_dates': False,
        'data_param': 'hoteles',
        'sheet_name': 'ciudades',
        'description': 'Scraping de seguimiento diario'
    },
    'personalizado': {
        'module': 'Web_Scraping_Booking',
        'class': 'BookingScraperPersonalizado',
        'requires_dates': True,
        'data_param': 'hoteles',
        'sheet_name': 'lista_hoteles',
        'description': 'Scraping personalizado de Booking'
    }
}
