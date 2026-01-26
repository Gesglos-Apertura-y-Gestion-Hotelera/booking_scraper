# Gesglos - Scraper
## Scrapper de hoteleria usado en booking.com

### para ejecutar el codigo correr estos comandos en docker:

    docker build -f dockerfile -t selenium-app . 
### &&
    docker run --shm-size=2gb selenium-app {{script_key}}

### por facilidad usa este comando largo:
     docker build -f dockerfile -t selenium-app . && docker run --shm-size=2gb selenium-app {{script_key}}

### para detener una imagen:
    sudo docker stop selenium-app

### para ver la salida de los logs:
    sudo docker logs -f selenium-app

### para borrar la imagen:
    sudo docker rm -f selenium-app

### para borrar todas las imagenes sin pedir confirmacion:
    sudo docker system prune -af

### para ver todas las imagenes:
    sudo docker images

### para ver todos los contenedores activos:
    sudo docker ps

### para ver todos los contenedores (prendidos-apagados):
    sudo docker ps -a

### Diagrama de flujo de proceso:
###
flowchart TD
    A[Usuario ingresa parámetro<br/>Clientes / Competencia<br/>en Google Sites]
    B[Click en botón<br/>Ejecutar búsqueda]
    C[Google Apps Script<br/>recibe la orden]
    D[Apps Script<br/>se autentica / loguea]
    E[Envía datos y orden<br/>al Runner de GitHub Actions]
    F[GitHub Actions ejecuta<br/>Scraper]
    G[Scraper consulta<br/>Booking]
    H[Resultados obtenidos]
    I[Apps Script vinculado<br/>a Google Sheets]
    J[Resultados guardados<br/>en Google Sheets]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J


