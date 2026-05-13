# Architecture

The platform is static-first. Astro builds content collections into static pages, Caddy serves the output, and GitHub stores both source code and content history.

## Components

- Astro web app: presentation, routing, content rendering, RSS, sitemap.
- Decap CMS: manual editing interface that commits Markdown or MDX to GitHub.
- Docker Compose: repeatable RP4 runtime.
- Caddy: static server, compression, security headers, HTTPS readiness.
- n8n: future automation orchestrator.

## Publishing Model

Public pages filter out `draft: true`. Generated content is committed as draft MDX and reviewed before publishing.
