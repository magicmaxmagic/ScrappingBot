#!/bin/bash

# ETL Service Entrypoint
set -e

echo "🚀 Starting ETL service..."

# Attendre que PostgreSQL soit disponible
echo "⏳ Waiting for PostgreSQL..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import psycopg2
import os
import sys
try:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot')
    conn = psycopg2.connect(DATABASE_URL)
    conn.close()
    print('✅ PostgreSQL is ready!')
    sys.exit(0)
except Exception as e:
    print(f'❌ PostgreSQL not ready yet... ({e})')
    sys.exit(1)
" 2>/dev/null; then
        break
    fi
    echo "🔄 Attempt $attempt/$max_attempts - PostgreSQL not ready, waiting..."
    sleep 3
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ PostgreSQL connection timeout after $max_attempts attempts"
    exit 1
fi

echo "✅ PostgreSQL is ready!"

# Vérifier les variables d'environnement
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Warning: DATABASE_URL not set, using default"
    export DATABASE_URL="postgresql://scrappingbot_user:scrappingbot_pass@postgres:5432/scrappingbot"
fi

# Créer les répertoires nécessaires
mkdir -p /app/data /app/logs /app/output

# Vérifier que les modules ETL sont importables
echo "🔍 Checking ETL modules..."
python -c "
import sys
sys.path.append('/app')
try:
    import etl
    from etl.normalize import normalize_currency
    from etl.dedupe import dedupe_records  
    print('✅ ETL modules are importable')
except ImportError as e:
    print(f'❌ ETL module import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ ETL module error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ ETL module check failed"
    exit 1
fi

# Afficher les informations de l'environnement
echo "ℹ️  Environment info:"
echo "  - Python version: $(python --version)"
echo "  - Working directory: $(pwd)"
echo "  - Available ETL modules: $(python -c 'import etl; print([m for m in dir(etl) if not m.startswith(\"_\")])')"

# Lancer la commande
echo "🚀 Executing: $@"
exec "$@"
