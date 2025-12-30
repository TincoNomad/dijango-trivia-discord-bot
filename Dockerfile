# Base Python image for all services
FROM python:3.12-slim

# Set working directory for application
WORKDIR /app

# Install minimal required dependencies
RUN apt-get update && apt-get install -y \
    # PostgreSQL client library
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8000

CMD ["python", "uvicorn", "app.main:app", "runserver", "0.0.0.0:8000", "--host"]