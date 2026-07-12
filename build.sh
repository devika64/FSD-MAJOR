#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "Installing requirements..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate

echo "Creating default superuser..."
python create_superuser.py

echo "Build process completed successfully!"
