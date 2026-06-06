# Petooooo.github.io

This repository contains the public site for my personal engineering notebook. It is a static Astro/MDX site for projects, study notes, DevOps records, research-oriented writing, paper reviews, and archived drafts.

The site is intentionally simple: write in Markdown or MDX, review changes in Git, push to `main`, and let GitHub Pages publish the static build. A Raspberry Pi 4 Docker/Caddy path is kept as optional self-hosting documentation, but GitHub Pages is the primary public deployment for this repository.

## What This Repo Is

- A public technical notebook and archive.
- A place for engineering notes, implementation records, infrastructure writeups, and study material.
- A static-first site built with Astro content collections.
- A Git-backed writing workflow built around local editing, Workbench notes, and reviewed MDX commits.
- A deployable site that can run on GitHub Pages or, optionally, behind Caddy on a Raspberry Pi 4.

This repository is not the private Workbench itself. Some writing and experiments may start in a local Workbench or RP4 setup, but the material that lands here is the reviewed, public-facing MDX content and the site code that presents it.

## Structure

- `apps/web`: Astro app, Tailwind CSS, MDX content collections, layouts, and components.
- `apps/web/src/content`: public content collections.
- `docs`: architecture, deployment, content workflow, and troubleshooting notes.
- `infra`: optional Docker, Caddy, deploy, and backup scripts for RP4/self-hosted operation.
- `automation`: helper notes and draft utilities for organizing raw technical notes before manual review.

## Content Areas

- `projects`: larger implementations and project-level records.
- `notes`: study notes and conceptual learning material.
- `devops`: infrastructure, deployment, operations, and troubleshooting notes.
- `research`: computer science and electrical/electronic engineering research notes.
- `paper-reviews`: concise paper reading notes.
- `archive`: old drafts, temporary material, and lower-confidence notes that should not crowd the main sections.

Drafts use `draft: true` and are excluded from public routes. Published content should avoid secrets, private hostnames, internal IPs, tokens, and sensitive operational details.

## Local Development

Use Node.js 20 or newer. The repository includes `.nvmrc` and `.node-version` pins.

```bash
npm install --prefix apps/web
npm run dev --prefix apps/web
```

Open `http://localhost:4321`.

Useful checks:

```bash
npm run check --prefix apps/web
npm run build --prefix apps/web
npm run preview --prefix apps/web
```

## GitHub Pages Deployment

GitHub Pages is the primary deployment target for `Petooooo/Petooooo.github.io`.

The workflow in `.github/workflows/deploy-pages.yml` builds `apps/web` and publishes `apps/web/dist` with:

```bash
SITE_URL=https://petooooo.github.io/
```

Repository settings should use **Pages -> Build and deployment -> GitHub Actions**. Pushing to `main` runs the deployment workflow.

See `docs/deployment-github-pages.md` for verification and troubleshooting.

## Optional RP4 Self-Hosting

The RP4 path is kept for self-hosting practice and operational ownership. It builds the same static Astro site and serves it with Caddy through Docker Compose.

```bash
cp .env.example .env
docker compose build
docker compose up -d
```

For the Raspberry Pi:

```bash
git clone https://github.com/Petooooo/Petooooo.github.io.git ~/Petooooo.github.io
cd ~/Petooooo.github.io
cp .env.example .env
chmod +x infra/scripts/deploy.sh infra/scripts/backup.sh
./infra/scripts/deploy.sh
```

Set `SITE_URL`, `SITE_DOMAIN`, and `CADDY_EMAIL` before production-style RP4 builds. `SITE_URL` affects canonical URLs, RSS, Open Graph metadata, and sitemap output. `SITE_DOMAIN` is used by Caddy.

See `docs/deployment-rp4.md` for the longer runbook.

## Writing Workflow

The normal flow is:

1. Write or collect notes locally, often through Workbench or a local editor.
2. Convert useful material into MDX under `apps/web/src/content`.
3. Keep unfinished material as `draft: true`.
4. Review the diff.
5. Run `npm run check --prefix apps/web` and `npm run build --prefix apps/web`.
6. Commit and push to `main`.
7. GitHub Pages publishes the static site.

The `automation` directory is for helper scripts and draft organization. It should support note cleanup and structure, not replace manual review or turn the site into bulk publishing.

## Backups

GitHub is the primary backup. The optional RP4 script `infra/scripts/backup.sh` can create a timestamped backup containing a Git bundle, content files, infrastructure files, Docker files, a redacted `.env`, and recent container diagnostics when available.

Recommended operational habits:

- Keep important content in Git.
- Test restore steps occasionally.
- Store sensitive local notes outside the public repository.

## Troubleshooting

- Build fails: run `npm run check --prefix apps/web` and inspect frontmatter.
- Draft is missing from the site: confirm `draft: false`.
- GitHub Pages does not update: check the Actions run and Pages settings.
- Caddy cannot issue HTTPS: confirm DNS, router forwarding, and inbound port availability.
- RP4 deploy script fails with shell errors: run `./infra/scripts/deploy.sh` directly after `chmod +x`; the script expects bash behavior.
