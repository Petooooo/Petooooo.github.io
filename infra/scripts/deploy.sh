#!/usr/bin/env sh
set -eu

REPO_DIR="${REPO_DIR:-$HOME/portfolio-platform}"
BRANCH="${BRANCH:-main}"
SERVICE="${SERVICE:-portfolio-web}"

log() {
  printf '\n==> %s\n' "$1"
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

on_error() {
  echo "Deployment failed. Inspect with: docker compose logs --tail=100 $SERVICE" >&2
}

trap on_error ERR

need git
need docker

cd "$REPO_DIR"

if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.example to .env and set SITE_URL, SITE_DOMAIN, and CADDY_EMAIL." >&2
  exit 1
fi

log "Validating Docker Compose configuration"
docker compose config >/dev/null

log "Pulling latest $BRANCH from GitHub"
git fetch origin "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "Building Docker image"
docker compose build --pull "$SERVICE"

log "Recreating service"
docker compose up -d --remove-orphans "$SERVICE"

log "Container status"
docker compose ps

log "Recent logs"
docker compose logs --tail=80 "$SERVICE"
