#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-}"
if [[ -z "$ENV" ]]; then
  echo "Usage: scripts/deploy.sh <alpha|beta|production>"
  exit 1
fi

case "$ENV" in
  production)  DOTENV=".env.production"  DOMAIN="findme-dashboard.mulanga.dev"       ;;
  *) echo "Unknown env: $ENV"; exit 2 ;;
esac

echo "==> Generating static build for $ENV ($DOTENV)"
NUXT_ENV_MODE="$ENV" npx nuxt generate --dotenv "$DOTENV"

TS="$(date +%Y%m%d%H%M%S)"
REMOTE_USER="root"
REMOTE_HOST="46.62.234.146"
BASE="/var/www/findme-dashboard.mulanga.dev/$ENV"
REMOTE_RELEASE="$BASE/releases/$TS"
REMOTE_CURRENT="$BASE/current"

echo "==> Creating release on $REMOTE_HOST"
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p '$REMOTE_RELEASE'"

echo "==> Uploading build"
rsync -az --delete .output/public/ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_RELEASE/"

echo "==> Activating release + reload nginx"
ssh "$REMOTE_USER@$REMOTE_HOST" "ln -sfn '$REMOTE_RELEASE' '$REMOTE_CURRENT' && systemctl reload nginx"

echo "✅ Deployed $ENV → https://$DOMAIN"
