# Raspberry Pi 4 Deployment

Raspberry Pi 4 deployment is an optional self-hosted mode. GitHub Pages is the primary public hosting target, but the Pi can still run the same static Astro site through Docker Compose and Caddy.

The Raspberry Pi 4 runs one Docker Compose service: a multi-stage image that builds the Astro app from `apps/web` and serves the static output with Caddy.

## First-Time Setup

SSH into the Pi:

```bash
ssh rp4
```

Install baseline packages:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
```

Install Docker using Docker's official convenience script, then enable the service:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
sudo systemctl enable --now docker
```

Log out and back in so the `docker` group applies, then verify Docker and the Compose plugin:

```bash
docker --version
docker compose version
```

Clone the repository:

```bash
git clone https://github.com/Petooooo/Petooooo.github.io.git ~/Petooooo.github.io
cd ~/Petooooo.github.io
```

Create the production environment file:

```bash
cp .env.example .env
nano .env
```

Set these values:

- `SITE_URL`: full public URL, for example `https://your-name.iptime.org`.
- `SITE_DOMAIN`: hostname only, for example `your-name.iptime.org`.
- `CADDY_EMAIL`: email for Let's Encrypt account notices.
- `PUBLIC_GITHUB_URL`, `PUBLIC_RESUME_URL`: public profile placeholders.

Do not commit `.env`.

## ipTIME DDNS and Ports

Configure ipTIME DDNS so the hostname points to the home network. On the router, forward:

- TCP `80` to the Raspberry Pi.
- TCP `443` to the Raspberry Pi.

Caddy can issue HTTPS certificates automatically when `SITE_DOMAIN` resolves to the public IP and both ports reach the Pi. If the ISP blocks inbound ports, HTTPS issuance will fail until networking is corrected.

## Initial Deploy

Run:

```bash
chmod +x infra/scripts/deploy.sh infra/scripts/backup.sh
./infra/scripts/deploy.sh
```

The deploy script resolves the repository root from its own location, so it works from any clone directory name. It validates Compose config, fetches the latest `main`, builds the image, recreates the service, prints container status, and shows recent logs. Set `REPO_DIR=/path/to/repo` only when you intentionally want to override the auto-detected root.

Verify locally on the Pi:

```bash
docker compose ps
docker compose logs --tail=100 portfolio-web
curl -I http://localhost
```

Verify through the public domain after DNS and forwarding are ready:

```bash
curl -I https://your-name.iptime.org
curl -I https://your-name.iptime.org/rss.xml
```

## Normal Update

From your local machine, push approved changes to GitHub. On the Pi:

```bash
ssh rp4
cd ~/Petooooo.github.io
./infra/scripts/deploy.sh
```

## Logs and Service Control

```bash
cd ~/Petooooo.github.io
docker compose ps
docker compose logs -f portfolio-web
docker compose restart portfolio-web
docker compose down
docker compose up -d
```

## Backups

Run:

```bash
cd ~/Petooooo.github.io
./infra/scripts/backup.sh
```

The backup script writes a timestamped tarball under `$HOME/backups/portfolio-platform` by default. It includes a Git bundle, content files, Decap admin config, infrastructure files, Docker files, a redacted copy of `.env` when present, and recent container diagnostics when the service is running.

## Failed Deployment Recovery

Check logs:

```bash
cd ~/Petooooo.github.io
docker compose logs --tail=200 portfolio-web
```

If the latest Git commit is bad, return to the previous commit and rebuild:

```bash
git log --oneline -5
git checkout <known-good-commit>
docker compose build --pull portfolio-web
docker compose up -d --remove-orphans portfolio-web
docker compose ps
```

After fixing the issue on the main branch, return the Pi to `main`:

```bash
git checkout main
git pull --ff-only origin main
./infra/scripts/deploy.sh
```

## Troubleshooting

If deployment fails with:

```text
trap: ERR: bad trap
```

the script was executed by POSIX `sh`, which does not support bash `ERR` traps. Update to the latest script, ensure it is executable, and run it directly:

```bash
chmod +x infra/scripts/deploy.sh
./infra/scripts/deploy.sh
```

Do not run it as `sh infra/scripts/deploy.sh`.

## Caddy Behavior

Caddy serves `/srv`, which is copied from `apps/web/dist` during the Docker build. It enables `zstd` and `gzip`, applies conservative security headers, caches immutable Astro/static assets aggressively, and falls back to `/404.html` for missing static routes.

`SITE_URL` is used at build time by Astro for canonical URLs, RSS, Open Graph metadata, and sitemap output. For RP4 hosting, set it to the Pi's public URL. `SITE_DOMAIN` is used at runtime by Caddy to decide which hostname to serve.
