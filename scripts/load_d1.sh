#!/bin/bash
# D1 load script with empty SQL guard
set -e

UPLOAD_SQL="${1:-data/upload.sql}"
WORKERS_DIR="${2:-workers}"

if [ ! -f "$UPLOAD_SQL" ]; then
    echo "❌ Upload SQL file not found: $UPLOAD_SQL"
    exit 1
fi

# Check if SQL file has actual INSERT statements
SQL_LINES=$(grep -c "INSERT INTO" "$UPLOAD_SQL" 2>/dev/null || echo "0")

if [ "$SQL_LINES" -eq 0 ]; then
    echo "⚠️  Skipping D1 load - no INSERT statements found in $UPLOAD_SQL"
    exit 0
fi

echo "📝 Found $SQL_LINES INSERT statements, loading to D1..."

# Clear existing listings to avoid mixing old/new data
cd "$WORKERS_DIR"
npx wrangler d1 execute estate-db --local --command "DELETE FROM listings;" || true

# Load new data
npx wrangler d1 execute estate-db --local --file "../$UPLOAD_SQL"

echo "✅ D1 load complete"
