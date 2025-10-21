#!/usr/bin/env bash
set -euo pipefail

# --- Config (override via env or .env export before running) ---
DB_NAME="${DB_NAME:-find_south}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
MAINT_DB="${MAINT_DB:-postgres}"  # maintenance DB for admin commands

# Pass password if provided
if [[ -n "$DB_PASSWORD" ]]; then
  export PGPASSWORD="$DB_PASSWORD"
fi

echo "⚠️ Dropping database '$DB_NAME' if it exists..."

# Drop database if exists
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$MAINT_DB" \
  -c "DROP DATABASE IF EXISTS \"$DB_NAME\" WITH (FORCE);"

echo "📦 Creating database '$DB_NAME'..."
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -T template0 -E UTF8 "$DB_NAME"

echo "✅ Database '$DB_NAME' dropped and recreated successfully"