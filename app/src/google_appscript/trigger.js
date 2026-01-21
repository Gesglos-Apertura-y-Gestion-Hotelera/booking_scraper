
  var rawUrl = 'https://api.github.com/repos/Gesglos-Apertura-y-Gestion-Hotelera/booking_scraper/actions/jobs/61062966569/rerun'
  var url = encodeURI(rawUrl);


  var token = "aqui va el token";
  var payload = {
    "ref": "main",
    "inputs": {
      "script_key": "clientes_diario" // Aquí cambias el parámetro dinámicamente
    }
  };

  var options = {
    "method": "get",
    "contentType": "application/json",
    "headers": {
      "Authorization": "Bearer " + token,
      "Accept": "application/vnd.github.v3+json",
      muteHttpExceptions: true
    },
    "payload": JSON.stringify(payload)
  };

  var response = UrlFetchApp.fetch(url, options);
  console.log(response);
}


/*
# Mapeo directo de parámetro → script (SIN INTERFAZ)
SCRIPTS = {
    'clientes_diario': 'Web_Scraping_Clientes.py',
    'clientes_prevision': 'Web_Scraping_Clientes_Adhoc.py',
    'competencia_diario': 'Web_Scraping_Competencia.py',
    'competencia_prevision': 'Web_Scraping_Competencia_Adhoc.py',
    'seguimiento_diario': 'Web_Scraping_Daily_Tracking.py',
    'personalizado': 'Web_Scryping_Booking.py',
    'update_df': 'Update_DF.py'
}
*/