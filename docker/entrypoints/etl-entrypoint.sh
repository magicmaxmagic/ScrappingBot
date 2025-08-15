#!/bin/bash

# ETL Service Entrypoint
set -e

echo "Starting ETL service..."

# Attendre que PostgreSQL soit disponible
echo "Waiting for PostgreSQL..."
while ! python -c "
import psycopg2
import os
import time
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgresql://scrappingbot_user:scrappingbot_password@postgres:5432/scrappingbot'))
    conn.close()
    print('PostgreSQL is ready!')
except:
    print('PostgreSQL not ready yet...')
    exit(1)
" 2>/dev/null; do
    sleep 2
done

echo "PostgreSQL is ready!"

# Vérifier les variables d'environnement
if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL not set, using default"
    export DATABASE_URL="postgresql://scrappingbot_user:scrappingbot_password@postgres:5432/scrappingbot"
fi

# Créer les répertoires nécessaires
mkdir -p /app/data /app/logs

# Lancer la commande
echo "Executing: $@"
exec "$@"
