function doPost(e) {
  try {
    Logger.log("=== INICIO ===");
    
    var scriptKey = "clientes_diario";
    var checkIn = "";
    var checkOut = "";
    
    if (e && e.parameter) {
      scriptKey = e.parameter.script_key || scriptKey;
      checkIn = e.parameter.check_in || checkIn;
      checkOut = e.parameter.check_out || checkOut;
    }
    
    Logger.log("script_key: " + scriptKey);
    Logger.log("check_in: " + checkIn);
    Logger.log("check_out: " + checkOut);
    
    // Leer datos del sheet
    var spreadsheetId = "1ZsS-tWfgn3Zzl4DNWX9u1UagRfC4ZwydeZPMymVfOGY";
    var sheetName = "Cliente";
    
    var spreadsheet = SpreadsheetApp.openById(spreadsheetId);
    var sheet = spreadsheet.getSheetByName(sheetName);
    
    var lastRow = sheet.getLastRow();
    var lastCol = sheet.getLastColumn();
    
    if (lastRow < 2) {
      return ContentService.createTextOutput(JSON.stringify({
        "status": "error",
        "message": "No hay datos en la hoja"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    var data = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
    
     var records = data.map(function(row) {
      return {
        "ciudad": String(row[0]),  
        "hotel": String(row[1])    
      };
    });
    
    Logger.log("Registros: " + records.length);
    
    // Disparar GitHub Actions
    var url = 'https://api.github.com/repos/Gesglos-Apertura-y-Gestion-Hotelera/booking_scraper/actions/workflows/selenium.yml/dispatches';
    var token = "aqui va el token real";
    
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
    
    Logger.log("Response: " + code);

    return ContentService.createTextOutput(JSON.stringify({
      "status": code === 204 ? "success" : "error",
      "code": code,
      "records": records.length
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
  var sheetName = "Cliente";
  
  var spreadsheet = SpreadsheetApp.openById(spreadsheetId);
  var sheet = spreadsheet.getSheetByName(sheetName);
  
  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  
  var data = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
  
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
  
  Logger.log(JSON.stringify(records, null, 2));
  return records;
}
/**/
