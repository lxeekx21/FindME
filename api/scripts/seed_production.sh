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

# Parse optional arguments for seed script
SEED_ARGS=""
while (( "$#" )); do
  case "$1" in
    --admins) SEED_ARGS="$SEED_ARGS --admins $2"; shift 2 ;;
    --users) SEED_ARGS="$SEED_ARGS --users $2"; shift 2 ;;
    --subs) SEED_ARGS="$SEED_ARGS --subs $2"; shift 2 ;;
    --comments) SEED_ARGS="$SEED_ARGS --comments $2"; shift 2 ;;
    --log-level) SEED_ARGS="$SEED_ARGS --log-level $2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "==> Running seed_test_data.py on $ENV"
echo "==> Seed arguments: $SEED_ARGS"

ssh_do "sudo -u findme-api bash -lc '
  set -e
  cd \"$APP\"
  
  # Load environment variables from shared .env
  set -a
  if [[ -f \"$SHARED/.env\" ]]; then
    export \$(grep -v \"^#\" \"$SHARED/.env\" | xargs -d $'\''\n'\'')
  fi
  set +a
  
  # Activate virtual environment
  . .venv/bin/activate
  
  # Run seed script
  if [[ -f scripts/seed_test_data.py ]]; then
    echo \"==> Running seed_test_data.py$SEED_ARGS\"
    python scripts/seed_test_data.py$SEED_ARGS
  else
    echo \"ERROR: scripts/seed_test_data.py not found\" >&2
    exit 1
  fi
'"

echo "✅ SEED COMPLETE"


# ./scripts/seed_production.sh production