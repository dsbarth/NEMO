#!/bin/bash


# Run migrations to create or update the database
django-admin makemigrations NEMO
django-admin migrate

# Collect static files
django-admin collectstatic --no-input --clear
# Run NEMO
waitress-serve --port=8000 NEMO.wsgi:application
