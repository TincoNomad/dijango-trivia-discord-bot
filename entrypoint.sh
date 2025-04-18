#!/bin/sh
set -e

# Django API Service Entrypoint Script
# ----------------------------------
# Purpose: Initialize and start the Django API service
# Features:
# - Database connection verification
# - Service startup banner
# - Django server management
# Author: Renzo Tincopa
# Last Updated: 2024

# Database connection check function
wait_for_db() {
    echo "🔄 Waiting for PostgreSQL..."

    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
        echo "⏳ PostgreSQL is unavailable - sleeping"
        sleep 1
    done

    echo "✅ PostgreSQL connected"
}

# Apply database migrations
apply_migrations() {
    echo "🔄 Applying database migrations..."
    python manage.py migrate --noinput
    echo "✅ Migrations applied"
}

# Service startup banner display
show_banner() {
    echo "==================================="
    echo "🚀 Django API Server"
    echo "🌐 http://0.0.0.0:8000"
    echo "==================================="
}

# Execution Steps
wait_for_db        # Step 1: Ensure database is ready
apply_migrations   # Step 2: Apply migrations
show_banner       # Step 3: Display startup message
export PYTHONUNBUFFERED=1  # Step 4: Configure Python output
python manage.py runserver 0.0.0.0:8000  # Step 5: Start Django server
