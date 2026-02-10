#!/bin/bash

# Script para ejecutar contenedores Docker según opción 1-7
echo "Selecciona un contenedor Docker (1-7):"
echo "1) Scraper Clientes Diario"
echo "2) Scraper Clientes Prevision"
echo "3) Scraper Competencia Diario"
echo "4) Scraper Competencia Prevision"
echo "5) Scraper Seguimiento Diario"
echo "6) Personalizado"
echo "7) Todos"

read -p "Opción: " opcion

# Cargar solo variables específicas del .env de forma segura
if [ -f .env ]; then
    export WEBAPP_URL=$(grep '^WEBAPP_URL=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    export BOOKING_CURRENCY=$(grep '^BOOKING_CURRENCY=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "COP")
    export BOOKING_COUNTRY=$(grep '^BOOKING_COUNTRY=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || echo "co")
fi

# Verificar que WEBAPP_URL existe
if [ -z "$WEBAPP_URL" ]; then
    echo "❌ ERROR: WEBAPP_URL no está definida en el archivo .env"
    exit 1
fi

# Función para ejecutar Docker con variables de entorno
run_docker() {
    local script_key=$1
    local sheet_data=$2
    local check_in=$3
    local check_out=$4

    echo "🚀 Ejecutando: $script_key"
    echo "📊 WEBAPP_URL: ${WEBAPP_URL:0:50}..."
    echo "📊 Sheet Data: ${sheet_data:0:100}..."

    # IMPORTANTE: Pasar las variables con -e
    sudo docker run --rm --shm-size=2gb \
        -e "BOOKING_CURRENCY=${BOOKING_CURRENCY}" \
        -e "BOOKING_COUNTRY=${BOOKING_COUNTRY}" \
        -e "WEBAPP_URL=${WEBAPP_URL}" \
        -e "SCRIPT_KEY=${script_key}" \
        -e "SHEET_DATA=${sheet_data}" \
        -e "CHECK_IN=${check_in}" \
        -e "CHECK_OUT=${check_out}" \
        selenium-app
}

# Construir imagen una sola vez
echo "🔨 Construyendo imagen Docker..."
sudo docker build -f dockerfile -t selenium-app .

case $opcion in
  1)
    echo "🚀 Iniciando Scraper Clientes Diario..."
    SCRIPT_KEY="clientes_diario"
    SHEET_DATA='[{"ciudad":"Mariquita","hotel":"Hotel Brisas La Gaviota Mariquit-Tolima","habitaciones":"","ocupadas":"","tarifa":"","total_ingresos":"","registro":""},{"ciudad":"Medellin","hotel":"Botánica Casa Hotel Manilab y HOUSY","habitaciones":"","ocupadas":"","tarifa":"","total_ingresos":"","registro":""}]'

    run_docker "$SCRIPT_KEY" "$SHEET_DATA" "" ""
    ;;

  2)
    echo "🚀 Iniciando Scraper Clientes Prevision..."
    SCRIPT_KEY="clientes_prevision"
    SHEET_DATA='[{"ciudad":"Mariquita","hotel":"Hotel Brisas La Gaviota Mariquit-Tolima","habitaciones":"","ocupadas":"","tarifa":"","total_ingresos":"","registro":""},{"ciudad":"Medellin","hotel":"Botánica Casa Hotel Manilab y HOUSY","habitaciones":"","ocupadas":"","tarifa":"","total_ingresos":"","registro":""}]'
    CHECK_IN="2027-02-01"
    CHECK_OUT="2027-02-05"

    run_docker "$SCRIPT_KEY" "$SHEET_DATA" "$CHECK_IN" "$CHECK_OUT"
    ;;

  3)
    echo "🚀 Iniciando Scraper Competencia Diario..."
    SCRIPT_KEY="competencia_diario"
    SHEET_DATA='[{"hotel":"Porto Marina Hotel","competidor":"Hotel Bambu Guatape","ciudad":"Guatapé","buscar":"Hotel Bambu Guatape, Guatapé"},{"hotel":"1714 Hotel Boutique Guatapé","competidor":"El Tropico Boutique Hotel","ciudad":"El peñol","buscar":"El Tropico Boutique Hotel, El peñol"},{"hotel":"Porto Marina Hotel","competidor":"Arvum Hotel Boutique","ciudad":"Guatapé","buscar":"Arvum Hotel Boutique, Guatapé"}]'

    run_docker "$SCRIPT_KEY" "$SHEET_DATA" "" ""
    ;;

  4)
    echo "🚀 Iniciando Scraper Competencia Prevision..."
    SCRIPT_KEY="competencia_prevision"
    SHEET_DATA='[{"hotel":"Hotel Brisas La Gaviota Mariquit-Tolima","competidor":"Arvum Hotel Boutique","ciudad":"guatape","buscar":"Arvum Hotel Boutique, El peñol"},{"hotel":"1714 Hotel Boutique Guatapé","competidor":"El Tropico Boutique Hotel","ciudad":"El peñol","buscar":"El Tropico Boutique Hotel, El peñol"},{"hotel":"Porto Marina Hotel","competidor":"Hotel Bambu Guatape","ciudad":"Guatapé","buscar":"Hotel Bambu Guatape, Guatapé"}]'
    CHECK_IN="2027-04-01"
    CHECK_OUT="2027-04-05"

    run_docker "$SCRIPT_KEY" "$SHEET_DATA" "$CHECK_IN" "$CHECK_OUT"
    ;;

  5)
    echo "🚀 Iniciando Seguimiento Diario..."
    SCRIPT_KEY="seguimiento_diario"
    SHEET_DATA='[{"hotel":"Porto Marina Hotel","competidor":"Hotel Bambu Guatape","ciudad":"Guatapé","buscar":"Hotel Bambu Guatape, Guatapé"},{"hotel":"1714 Hotel Boutique Guatapé","competidor":"El Tropico Boutique Hotel","ciudad":"El peñol","buscar":"El Tropico Boutique Hotel, El peñol"},{"hotel":"Porto Marina Hotel","competidor":"Arvum Hotel Boutique","ciudad":"Guatapé","buscar":"Arvum Hotel Boutique, Guatapé"}]'

    run_docker "$SCRIPT_KEY" "$SHEET_DATA" "" ""
    ;;

  6)
    echo "🚀 Iniciando Personalizado..."
    echo ""

    SCRIPT_KEY="personalizado"
    SHEET_DATA='[{"hotel":"Porto Marina Hotel","competidor":"Hotel Bambu Guatape","ciudad":"Guatapé","buscar":"Hotel Bambu Guatape, Guatapé"},{"hotel":"1714 Hotel Boutique Guatapé","competidor":"El Tropico Boutique Hotel","ciudad":"El peñol","buscar":"El Tropico Boutique Hotel, El peñol"},{"hotel":"Porto Marina Hotel","competidor":"Arvum Hotel Boutique","ciudad":"Guatapé","buscar":"Arvum Hotel Boutique, Guatapé"}]'
    CHECK_IN="2027-04-01"
    CHECK_OUT="2027-04-05"

    run_docker "$SCRIPT_KEY" "$SHEET_DATA" "$CHECK_IN" "$CHECK_OUT"
    ;;

  7)
    echo "🚀 Iniciando TODOS los scrapers en paralelo..."

    SHEET_DATA='[{"ciudad":"Mariquita","hotel":"Hotel Brisas La Gaviota Mariquit-Tolima"}]'
    run_docker "clientes_diario" "$SHEET_DATA" "" "" &

    run_docker "clientes_prevision" "$SHEET_DATA" "2027-02-01" "2027-02-05" &

    SHEET_DATA='[{"hotel":"Porto Marina Hotel","competidor":"Hotel Bambu Guatape","ciudad":"Guatapé","buscar":"Hotel Bambu Guatape, Guatapé"}]'
    run_docker "competencia_diario" "$SHEET_DATA" "" "" &

    run_docker "competencia_prevision" "$SHEET_DATA" "2027-04-01" "2027-04-05" &

    run_docker "seguimiento_diario" "$SHEET_DATA" "" "" &

    run_docker "personalizado" "$SHEET_DATA" "2027-04-01" "2027-04-05" &

    echo "⏳ Esperando que todos los procesos terminen..."
    wait

    echo "✅ Todos los scrapers completados."
    ;;

  *)
    echo "❌ Opción inválida. Usa 1-7."
    exit 1
    ;;
esac

echo "✅ Proceso completado."