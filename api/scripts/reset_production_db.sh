#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-production}"

case "$ENV" in
  production)  BASE="/var/www/production" ;;
  *) echo "Unknown env: $ENV"; exit 2 ;;
esac

REMOTE_USER="root"
REMOTE_HOST="157.180.126.162"

APP="$BASE/app"
SHARED="$BASE/shared"

ssh_do() { ssh -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" "$@"; }

# Confirmation prompt
echo "⚠️  WARNING: This will DROP and RECREATE the production database!"
echo "   All data will be LOST!"
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation

if [[ "$confirmation" != "yes" ]]; then
  echo "❌ Aborted. Database was not modified."
  exit 1
fi

echo "==> Stopping API service to prevent connections..."
ssh_do "systemctl stop findme-api-production" || echo "Service may not be running"

echo ""
echo "==> Dropping and recreating database..."

ssh_do "bash -lc '
  set -e
  
  # Load environment variables from shared .env
  set -a
  if [[ -f \"$SHARED/.env\" ]]; then
    export \$(grep -v \"^#\" \"$SHARED/.env\" | xargs -d $'\''\n'\'')
  fi
  set +a
  
  # Extract database name from DB_URL
  DB_NAME=\"find_south\"
  if [[ -n \"\${DB_URL:-}\" ]]; then
    # Parse postgresql+psycopg2://user:pass@host:port/dbname
    DB_NAME=\$(echo \"\$DB_URL\" | sed \"s/.*\\///\" | sed \"s/.*@[^/]*\\///\")
  fi
  
  DB_USER=\"findme_api\"
  if [[ -n \"\${DB_URL:-}\" ]]; then
    DB_USER=\$(echo \"\$DB_URL\" | sed \"s/postgresql+psycopg2:\\/\\///\" | cut -d\":\" -f1)
  fi
  
  echo \"Database: \$DB_NAME\"
  echo \"User: \$DB_USER\"
  
  # Terminate active connections as postgres superuser
  echo \"Terminating active connections...\"
  sudo -u postgres psql -d postgres -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '\''\$DB_NAME'\'' AND pid <> pg_backend_pid();\" 2>/dev/null || true
  
  # Drop database as postgres superuser
  echo \"Dropping database \$DB_NAME...\"
  sudo -u postgres psql -d postgres -c \"DROP DATABASE IF EXISTS \\\"\$DB_NAME\\\" WITH (FORCE);\"
  
  # Create database as postgres superuser
  echo \"Creating database \$DB_NAME...\"
  sudo -u postgres createdb -T template0 -E UTF8 \"\$DB_NAME\"
  
  # Grant privileges as postgres superuser
  echo \"Granting privileges to \$DB_USER...\"
  sudo -u postgres psql -d postgres -c \"GRANT ALL PRIVILEGES ON DATABASE \\\"\$DB_NAME\\\" TO \\\"\$DB_USER\\\";\"
  
  # Grant schema privileges
  sudo -u postgres psql -d \"\$DB_NAME\" -c \"GRANT ALL ON SCHEMA public TO \\\"\$DB_USER\\\";\"
'"

echo ""
echo "==> Starting API service..."
ssh_do "systemctl start findme-api-production"

echo ""
echo "✅ Database dropped and recreated successfully"
echo ""
echo "📝 Next steps:"
echo "   1. Run migrations: ./scripts/deploy.sh production --migrate"
echo "   2. Seed data: ./scripts/seed_production.sh production"