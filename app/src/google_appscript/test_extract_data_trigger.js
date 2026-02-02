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