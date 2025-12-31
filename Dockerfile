# Base Python image for all services
FROM python:3.12-slim

# Set working directory for application
WORKDIR /app

# Install minimal required dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Primero copiamos solo requirements.txt para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos dependencias
RUN pip install -r requirements.txt

# Luego copiamos solo los archivos necesarios
COPY manage.py .
COPY api/ ./api
COPY templates/ ./templates
COPY static/ ./static
# No copiamos media/ ya que será montado como volumen

EXPOSE 8000

CMD ["uvicorn", "api.asgi:application", "--host", "0.0.0.0", "--port", "8000"]