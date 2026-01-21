# Gesglos - Scraper
## Scrapper de hoteleria usado en booking.com

### para ejecutar el codigo correr estos comandos en docker:

    sudo docker compose up --build 
### &&
    sudo docker compose logs -f scraper

### por facilidad usa este comando largo:
     sudo docker compose up --build -d && sudo docker compose logs -f scraper

### para detener una imagen:
    sudo docker stop scraper

### para ver la salida de los logs:
    sudo docker logs -f scraper

### para borrar la imagen:
    sudo docker rm -f scraper

### para borrar todas las imagenes sin pedir confirmacion:
    sudo docker system prune -af

### para ver todas las imagenes:
    sudo docker images

### para ver todos los contenedores activos:
    sudo docker ps

### para ver todos los contenedores (prendidos-apagados):
    sudo docker ps -a

