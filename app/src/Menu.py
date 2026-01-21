import os
import tkinter as tk
from tkinter import messagebox

# Función para ejecutar cada script
def run_script(script_name):
    try:
        os.system(f'python {script_name}')
    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar {script_name}: {e}")

# Configuración de la ventana principal
def main():
    root = tk.Tk()
    root.title("Menú")
    root.geometry("300x400")  # Tamaño de la ventana

    # Etiqueta de título
    label = tk.Label(root, text="Selecciona una consulta para ejecutar", font=("Segoe UI light", 12))
    label.pack(pady=10)

    # Botones para cada script
    button1 = tk.Button(root, text="Clientes diario", command=lambda: run_script('Web_Scraping_Clientes.py'))
    button1.pack(pady=5)

    button2 = tk.Button(root, text="Clientes prevision", command=lambda: run_script('Web_Scraping_Clientes_Adhoc.py'))
    button2.pack(pady=5)

    button3 = tk.Button(root, text="Competencia diario", command=lambda: run_script('Web_Scraping_Competencia.py'))
    button3.pack(pady=5)

    button4 = tk.Button(root, text="Competencia prevision", command=lambda: run_script('Web_Scraping_Competencia_Adhoc.py'))
    button4.pack(pady=5)

    button5 = tk.Button(root, text="Seguimiento diario", command=lambda: run_script('Web_Scraping_Daily_Tracking.py'))
    button5.pack(pady=5)

    button6 = tk.Button(root, text="Personalizado", command=lambda: run_script('Web_Scryping_Booking.py'))
    button6.pack(pady=5)

    button7 = tk.Button(root, text="Actualizar Data Frames", command=lambda: run_script('Update_DF.py'))
    button7.pack(pady=5)

    button_exit = tk.Button(root, text="Salir", command=root.quit)
    button_exit.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
