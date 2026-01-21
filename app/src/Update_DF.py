import os
import win32com.client as win32

# Asegúrate de que pywin32 esté instalado ejecutando `pip install pywin32` antes de ejecutar el script

# Obtener la ruta del usuario actual
home_dir = os.path.expanduser("~")
ruta_actualizacion = os.path.join(home_dir, 'Documents', 'database')

# Filtrar los archivos Excel en la carpeta
excel_files = [f for f in os.listdir(ruta_actualizacion) if f.endswith('.xlsx')]

# Inicializar la aplicación Excel sin mostrar la interfaz y sin alertas
try:
    excel_app = win32.gencache.EnsureDispatch('Excel.Application')
    excel_app.Visible = False
    excel_app.DisplayAlerts = False  # Desactiva los cuadros de diálogo

    # Recorre cada archivo y actualiza las conexiones
    for file_name in excel_files:
        file_path = os.path.join(ruta_actualizacion, file_name)
        workbook = excel_app.Workbooks.Open(file_path)
        workbook.RefreshAll()
        excel_app.CalculateUntilAsyncQueriesDone()
        workbook.Save()
        workbook.Close()

    print("Actualización completada en todos los archivos.")

finally:
    # Asegúrate de cerrar la aplicación Excel al finalizar
    excel_app.Quit()
