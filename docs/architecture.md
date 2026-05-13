# Architecture

The site is static-first and notebook-shaped. Astro builds content collections into static pages, GitHub Pages serves the public site, and GitHub stores both source code and content history. The Raspberry Pi 4 deployment path remains documented for self-hosting experiments with Docker Compose and Caddy.

## Components

- Astro web app: presentation, routing, content rendering, RSS, sitemap.
- Decap CMS: manual editing interface that commits Markdown or MDX to GitHub.
- Docker Compose: repeatable optional RP4 runtime.
- Caddy: optional RP4 static server, compression, security headers, HTTPS readiness.
- n8n: future automation orchestrator.

## Publishing Model

Public pages filter out `draft: true`. Generated content is committed as draft MDX and reviewed before publishing.
