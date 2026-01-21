
function dispararScraper() {
  var url = "'https://api.github.com/repos/sof-fac/Gesglos/actions/workflows/selenium.yml/dispatches'";
  var token = "tu_github_pat_aqui";
  var payload = {
    "ref": "main", // o tu rama principal
    "inputs": {
      "comando_scraper": "clientes_diario" // Aquí cambias el parámetro dinámicamente
    }
  };

  var options = {
    "method": "post",
    "contentType": "application/json",
    "headers": {
      "Authorization": "token " + token,
      "Accept": "application/vnd.github.v3+json"
    },
    "payload": JSON.stringify(payload)
  };

  UrlFetchApp.fetch(url, options);
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