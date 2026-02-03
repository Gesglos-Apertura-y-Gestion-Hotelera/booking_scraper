function doPost(e) {
  try {
    // Validar que existe postData
    if (!e || !e.postData || !e.postData.contents) {
      return ContentService.createTextOutput(
        JSON.stringify({error: 'No se recibieron datos en el POST'})
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Parsear el payload
    var payload = JSON.parse(e.postData.contents);
    var sheetName = payload.sheet;
    var data = payload.data;

    Logger.log('Sheet destino: ' + sheetName);
    Logger.log('Datos recibidos: ' + data.length + ' registros');

    // Validar que se proporcionó el nombre de la sheet
    if (!sheetName) {
      return ContentService.createTextOutput(
        JSON.stringify({error: 'No se proporcionó nombre de sheet'})
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Obtener la hoja por nombre
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(sheetName);

    if (!sheet) {
      return ContentService.createTextOutput(
        JSON.stringify({error: 'Sheet no encontrada: ' + sheetName})
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Convertir objetos a arrays según el tipo de sheet
    var rows = [];

    if (sheetName === 'clientes') {
      rows = data.map(function(item) {
        return [
          item.hotel || '',
          item.divisa || '',
          item.precio || '',
          item.review_promedio || '',
          item.comentarios || '',
          item.puntuacion || '',
          item.ciudad || '',
          item.check_in || '',
          item.check_out || ''
        ];
      });

    } else if (sheetName === 'competencia') {
      rows = data.map(function(item) {
        return [
          item.hotel || '',
          item.divisa || '',
          item.precio || '',
          item.puntuacion || '',
          item.review_promedio || '',
          item.comentarios || '',
          item.competidor || '',
          item.ciudad || '',
          item.check_in || '',
          item.check_out || ''
        ];
      });

    } else if (sheetName === 'ciudades') {
      rows = data.map(function(item) {
        return [
          item.hotel || '',
          item.divisa || '',
          item.precio || '',
          item.review_promedio || '',
          item.comentarios || '',
          item.puntuacion || '',
          item.ciudad || '',
          item.check_in || '',
          item.check_out || ''
        ];
      });

    } else {
      return ContentService.createTextOutput(
        JSON.stringify({error: 'Sheet no soportada: ' + sheetName})
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Escribir en la sheet (agregar al final)
    if (rows.length > 0) {
      var lastRow = sheet.getLastRow();
      sheet.getRange(lastRow + 1, 1, rows.length, rows[0].length).setValues(rows);
    }

    return ContentService.createTextOutput(
      JSON.stringify({
        success: true,
        rows: rows.length,
        sheet: sheetName,
        message: 'Éxito: ' + rows.length + ' filas añadidas a ' + sheetName
      })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    Logger.log('Error: ' + err.toString());
    return ContentService.createTextOutput(
      JSON.stringify({
        error: 'Error en el script: ' + err.message,
        stack: err.stack
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}