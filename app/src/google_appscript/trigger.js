function doGet(e) {
  try {
    console.log("=== INICIO DE PETICIÓN ===");
  
    // Capturamos los datos de la URL
    var scriptKey   = (e && e.parameter && e.parameter.script_key) ? e.parameter.script_key : "no_key";
    var checkIn     = (e && e.parameter && e.parameter.check_in)   ? e.parameter.check_in   : "no_checkin";
    var checkOut    = (e && e.parameter && e.parameter.check_out)  ? e.parameter.check_out  : "no_checkout";
    var ciudadInput = (e && e.parameter && e.parameter.ciudad)     ? e.parameter.ciudad     : "no_city";
  
    console.log("Parámetros recibidos: " + scriptKey + " | Ciudad: " + ciudadInput);
  
    var records = [];

    if (scriptKey === "personalizado") {
      records.push({
        "ciudad": ciudadInput,
        "hotel": "Personalizado"
      });
    } else {
      var spreadsheetId = "1ZsS-tWfgn3Zzl4DNWX9u1UagRfC4ZwydeZPMymVfOGY";
      var sheetName = "";

      // Determinamos la hoja según el scriptKey
      switch (scriptKey) {
        case "competencia_diario":
        case "competencia_prevision":
          sheetName = "Competencia";
          break;
        default:
          sheetName = "Cliente";
      }

      var sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(sheetName);
      if (!sheet) throw new Error("No se encontró la hoja: " + sheetName);

      var lastRow = sheet.getLastRow();
      if (lastRow < 2) {
        return ContentService.createTextOutput(JSON.stringify({
          "status": "error", "message": "Hoja vacía o sin datos: " + sheetName
        })).setMimeType(ContentService.MimeType.JSON);
      }

      // --- LÓGICA DE DETECCIÓN DINÁMICA POR ETIQUETA ---
      // Obtenemos todos los datos (incluyendo cabecera en fila 1)
      var fullData = sheet.getRange(1, 1, lastRow, sheet.getLastColumn()).getValues();
      var headers = fullData[0]; // Fila 1: Nombres de columnas
      var dataRows = fullData.slice(1); // Fila 2 en adelante: Datos

      // Buscamos los índices de las columnas por su nombre exacto
      var colIdxCiudad = headers.indexOf("Ciudad");
      var colIdxHotel  = headers.indexOf("Hotel");

      // Validamos que existan las columnas mínimas
      if (colIdxCiudad === -1 || colIdxHotel === -1) {
        throw new Error("No se encontraron las columnas 'Ciudad' o 'Hotel' en la hoja " + sheetName);
      }

      // Mapeamos los datos usando los nombres detectados
      records = dataRows.map(function(row) {
        return {
          "ciudad": String(row[colIdxCiudad]),
          "hotel": String(row[colIdxHotel])
        };
      });
    }
    
    // Configuración de GitHub Actions
    var url = 'https://api.github.com/repos/Gesglos-Apertura-y-Gestion-Hotelera/booking_scraper/actions/workflows/selenium.yml/dispatches';
    
    // NOTA: Se recomienda usar PropertiesService para el Token por seguridad
    var token = "aqui va el token"; 
    
    var payload = {
      "ref": "main", 
      "inputs": {
        "script_key": scriptKey,
        "sheet_data": JSON.stringify(records),
        "check_in": checkIn,
        "check_out": checkOut
      }
    };
    
    var options = {
      "method": "POST",
      "contentType": "application/json",
      "headers": {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github.v3+json"
      },
      "muteHttpExceptions": true,
      "payload": JSON.stringify(payload)
    };

    var response = UrlFetchApp.fetch(url, options);
    var code = response.getResponseCode();
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": code === 204 ? "success" : "error",
      "code": code,
      "records_sent": records.length,
      "sheet_used": sheetName || "N/A"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    Logger.log("ERROR: " + error);
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/* 

// Función alternativa para ejecutar manualmente desde el editor
function testReadSheet() {
  var spreadsheetId = "1ZsS-tWfgn3Zzl4DNWX9u1UagRfC4ZwydeZPMymVfOGY";
  var sheetName = "Competencia";
  
  var spreadsheet = SpreadsheetApp.openById(spreadsheetId);
  var sheet = spreadsheet.getSheetByName(sheetName);
  
  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  
  var data = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
  
  if (sheetName == "Cliente"){
  var records = data.map(function(row) {
    return {
      "ciudad": row[0],
      "hotel": row[1],
      "habitaciones": row[2],
      "ocupadas": row[3],
      "tarifa": row[4],
      "total_ingresos": row[5],
      "registro": row[6]
    };
  });
  };
  if (sheetName == "Competencia"){
  var records = data.map(function(row) {
    return {
      "ciudad": row[2],
      "hotel": row[0],
      "competidor": row[1],
      "buscar": row[3]      
    };
  });
  };

  
  Logger.log(JSON.stringify(records, null, 2));
  return records;
}
/**/
