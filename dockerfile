# Forzar plataforma amd64 para compatibilidad con Chrome
# FROM --platform=linux/amd64 python:3.11-slim
FROM python:3.11-slim
# Evitar diálogos interactivos
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=es_CO.UTF-8
ENV LC-ALL=es_CO.UTF-8
# 1. Instalar dependencias base necesarias para descargar e instalar Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Descargar e instalar Google Chrome directamente
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Establecer directorio de trabajo
WORKDIR /app

# 4. Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar código fuente
COPY app/src/ ./src/
COPY app/ .

# 6. Configurar punto de entrada
ENTRYPOINT ["python", "src/main.py"]
#, "{{script_key}}"]