#!/usr/bin/env sh
set -eu

REPO_DIR="${REPO_DIR:-$HOME/portfolio-platform}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/portfolio-platform}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_DIR/$STAMP"

mkdir -p "$DEST"
cd "$REPO_DIR"

echo "Creating Git bundle backup..."
git bundle create "$DEST/repository.bundle" --all

echo "Copying deployment and content files..."
mkdir -p "$DEST/files"
cp -R apps/web/src/content "$DEST/files/content"
cp -R apps/web/public/admin "$DEST/files/admin"
cp -R infra "$DEST/files/infra"
cp docker-compose.yml Dockerfile .env.example "$DEST/files/"

if [ -f .env ]; then
  cp .env "$DEST/files/env.redacted"
  sed -i 's/=.*/=REDACTED/' "$DEST/files/env.redacted"
fi

if docker compose ps portfolio-web >/dev/null 2>&1; then
  docker compose ps > "$DEST/docker-compose-ps.txt" || true
  docker compose logs --tail=200 portfolio-web > "$DEST/docker-compose-logs.txt" || true
  docker compose exec -T portfolio-web caddy list-modules > "$DEST/caddy-modules.txt" || true
fi

tar -czf "$BACKUP_DIR/portfolio-platform-$STAMP.tar.gz" -C "$BACKUP_DIR" "$STAMP"

echo "Backup written to $BACKUP_DIR/portfolio-platform-$STAMP.tar.gz"
echo "Contents: Git bundle, content, admin config, infra, Docker files, redacted env, and recent container diagnostics when available."
