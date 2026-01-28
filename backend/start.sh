#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Create .env file from environment variables
echo "Baking environment variables into .env file..."
printenv > .env

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
