#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-}"; shift || true
if [[ -z "${ENV}" ]]; then
  echo "Usage: ./scripts/deploy.sh <alpha|beta|production> [--migrate] [--seed]"
  exit 1
fi

DO_MIGRATE=true
DO_SEED=true
while (( "$#" )); do
  case "$1" in
    --migrate) DO_MIGRATE=true ;;
    --seed)    DO_SEED=true ;;
    *) echo "Unknown flag: $1" ; exit 2 ;;
  esac
  shift
done

case "$ENV" in
  production)  DOMAIN="findme-api.mulanga.dev"        UNIT="findme-api-production"  ;;
  *) echo "Unknown env: $ENV"; exit 2 ;;
esac

REMOTE_USER="root"
REMOTE_HOST="157.180.126.162"

BASE="/var/www//$ENV"
APP="$BASE/app"          # single fixed directory; no releases
SHARED="$BASE/shared"
RUN_DIR="$BASE/run"

ssh_do() { ssh -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" "$@"; }

echo "==> Create dirs on remote"
ssh_do "mkdir -p '$APP' '$SHARED' '$RUN_DIR' && chown -R findme-api:findme-api '$BASE'"

echo "==> Upload .env (.env.$ENV → $SHARED/.env)"
scp ".env.$ENV" "$REMOTE_USER@$REMOTE_HOST:$SHARED/.env"

echo "==> Rsync code → $APP"
rsync -az --delete \
  --exclude ".git" \
  --exclude ".github" \
  --exclude ".venv" \
  --exclude "node_modules" \
  --exclude "__pycache__" \
  ./ "$REMOTE_USER@$REMOTE_HOST:$APP/"

# Ensure app files owned by service user
ssh_do "chown -R findme-api:findme-api '$APP'"

# Point 'current' to the freshly deployed app (atomic symlink swap)
ssh_do "ln -sfn '$APP' '$BASE/current' && chown -h findme-api:findme-api '$BASE/current'"

echo "==> (Re)create venv & install deps"
ssh_do "sudo -u findme-api bash -lc '
  set -e
  cd \"$APP\"
  python3 -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip wheel
  if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt \"uvicorn[standard]>=0.29\" \"gunicorn>=21\"
  elif [[ -f pyproject.toml ]]; then
    pip install \"uvicorn[standard]>=0.29\" \"gunicorn>=21\" .
  else
    echo \"ERROR: No requirements.txt or pyproject.toml found\" >&2
    exit 1
  fi

  # quick import smoke test: find an ASGI app
  python - <<PY
import importlib, sys
for m in (\"app.main\",\"main\",\"api.main\",\"server.main\"):
    try:
        importlib.import_module(m)
        print(\"ok:\", m)
        break
    except Exception:
        pass
else:
    sys.exit(1)
PY
'"

if $DO_MIGRATE || $DO_SEED; then
  echo "==> Export env vars for migrations/seeds"
  ssh_do "sudo -u findme-api bash -lc '
    set -e
    cd \"$APP\"
    # load env to current shell (ignores comments/blank lines)
    set -a
    if [[ -f \"$SHARED/.env\" ]]; then
      # shellcheck disable=SC2046
      export \$(grep -v \"^#\" \"$SHARED/.env\" | xargs -d $'\''\n'\'')
    fi
    set +a

    . .venv/bin/activate

    if $DO_MIGRATE; then
      echo \"==> Alembic upgrade head\"
      if [[ -f alembic.ini ]]; then
        .venv/bin/alembic -c alembic.ini upgrade head
      elif [[ -d alembic ]]; then
        .venv/bin/alembic upgrade head
      else
        echo \"WARN: alembic config not found; skipping migrations\"
      fi
    fi

    if $DO_SEED; then
      echo \"==> Run seed script\"
      # Option A: python module seeder (preferred)
      if [[ -f scripts/seed_db.py ]]; then
        .venv/bin/python scripts/seed_db.py --env \"$ENV\"
      elif [[ -f app/db/seed.py ]]; then
        .venv/bin/python -m app.db.seed --env \"$ENV\"
      else
        echo \"WARN: no seed script found (looked for scripts/seed_db.py and app/db/seed.py)\"
      fi
    fi
  '"
fi

echo "==> Restart systemd ($UNIT)"
ssh_do "systemctl daemon-reload && systemctl restart '$UNIT' && sleep 2 && systemctl status --no-pager -l '$UNIT'"
ssh_do "journalctl -u '$UNIT' -n 50 --no-pager"

echo "✅ DEPLOY COMPLETE → https://$DOMAIN"


#./scripts/deploy.sh production --migrate  --seed