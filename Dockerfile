# Base image con Python preinstalado
FROM python:3.13-alpine

# Set working directory for application
WORKDIR /app

# Instalar dependencias del sistema usando apk en lugar de apt-get
RUN apk update && apk add --no-cache \
    gcc \
    curl \
    netcat-openbsd \
    python3-dev \
    musl-dev \
    linux-headers \
    && rm -rf /var/cache/apk/*

# Las dependencias se instalan globalmente en el contenedor
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable and set it
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
