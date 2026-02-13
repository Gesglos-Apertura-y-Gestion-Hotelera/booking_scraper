function doGet(e) {
  try {
    var scriptKey   = (e && e.parameter && e.parameter.script_key) ? e.parameter.script_key : "no_key";
    var checkIn     = (e && e.parameter && e.parameter.check_in)   ? e.parameter.check_in   : "";
    var checkOut    = (e && e.parameter && e.parameter.check_out)  ? e.parameter.check_out  : "";
    var ciudadInput = (e && e.parameter && e.parameter.ciudad)     ? e.parameter.ciudad     : "";
  
    var records = [];
    var spreadsheetId = "1ZsS-tWfgn3Zzl4DNWX9u1UagRfC4ZwydeZPMymVfOGY";

    if (scriptKey === "personalizado") {
      records.push({
        "ciudad": String(ciudadInput).trim(),
        "hotel": "Personalizado"
      });
    } else {
      var esCompetencia = (scriptKey === "competencia_diario" || scriptKey === "competencia_prevision");
      var sheetName = esCompetencia ? "Competencia" : "Cliente";
      var sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(sheetName);
      
      if (!sheet) throw new Error("No se encontró la hoja: " + sheetName);

      var fullData = sheet.getDataRange().getValues();
      var headers = fullData[0];
      var dataRows = fullData.slice(1);

      var colIdxCiudad = headers.indexOf("Ciudad");

      if (esCompetencia) {
        var colIdxComp = headers.indexOf("Competidor");
        var colIdxHotel = headers.indexOf("Hotel");
        if (colIdxCiudad === -1 || colIdxComp === -1) throw new Error("Faltan columnas Ciudad/Competidor");
        
        // BLOQUE DE COMPETENCIA (El que te está fallando)
        records = dataRows.map(function(row) {
          return {
            "ciudad": String(row[colIdxCiudad]).replace(/[\r\n]+/g, " ").trim(),
            "competidor": String(row[colIdxComp]).replace(/[\r\n]+/g, " ").trim(),
            "hotel": String(row[colIdxHotel]).replace(/[\r\n]+/g, " ").trim()
          };
        });
      } else {
        var colIdxHotel = headers.indexOf("Hotel");
        if (colIdxCiudad === -1 || colIdxHotel === -1) throw new Error("Faltan columnas Ciudad/Hotel");
        
        // BLOQUE DE CLIENTE (El que te funciona)
        records = dataRows.map(function(row) {
          return {
            "ciudad": String(row[colIdxCiudad]).replace(/[\r\n]+/g, " ").trim(),
            "hotel": String(row[colIdxHotel]).replace(/[\r\n]+/g, " ").trim()
          };
        });
      }
    }
    
    // Forzamos la serialización a un string JSON puro
    var jsonString = JSON.stringify(records);
    
    // REFUERZO: Si el string no empieza con '[', lo forzamos (Protección contra optimización de Apps Script)
    if (typeof jsonString !== "string") {
      jsonString = JSON.stringify(jsonString);
    }

    var payload = {
      "ref": "main", 
      "inputs": {
        "script_key": String(scriptKey),
        "sheet_data": jsonString, 
        "check_in": String(checkIn),
        "check_out": String(checkOut)
      }
    };
    
    var options = {
      "method": "POST",
      "contentType": "application/json",
      "headers": {
        "Authorization": "Bearer AQUI VA EL TOKEN",
        "Accept": "application/vnd.github.v3+json"
      },
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    };

    var response = UrlFetchApp.fetch('https://api.github.com/repos/Gesglos-Apertura-y-Gestion-Hotelera/booking_scraper/actions/workflows/selenium.yml/dispatches', options);
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": response.getResponseCode() === 204 ? "success" : "error",
      "debug_json": jsonString // Revisa esto en tu navegador para ver si tiene comillas
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({"status": "error", "message": error.toString()})).setMimeType(ContentService.MimeType.JSON);
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
