#!/bin/bash

echo "📦 Starte Django Migrationen..."
python manage.py makemigrations
python manage.py migrate

echo "🔁 Gunicorn Prozesse neustarten..."

if pgrep gunicorn > /dev/null
then
    echo "Gunicorn läuft, wird neu geladen..."
    pkill -HUP gunicorn
else
    echo "Gunicorn läuft nicht, wird gestartet..."
    gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi

echo "✅ Fertig!"
