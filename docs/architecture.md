# Architecture

The site is static-first and notebook-shaped. Astro builds content collections into static pages, GitHub Pages serves the public site, and GitHub stores both source code and content history. The Raspberry Pi 4 deployment path remains documented for self-hosting experiments with Docker Compose and Caddy.

## Components

- Astro web app: presentation, routing, content rendering, RSS, sitemap.
- Workbench/local editor: manual writing surface for Markdown and MDX before Git review.
- Docker Compose: repeatable optional RP4 runtime.
- Caddy: optional RP4 static server, compression, security headers, HTTPS readiness.
- n8n: future automation orchestrator.

## Information Architecture

- Projects: larger implementations and ongoing engineering work.
- Notes: technical study notes, infrastructure operations, deployment runbooks, troubleshooting, and paper reading notes.
- Research: computer science, electrical/electronic engineering, systems, AI infrastructure, algorithms, and embedded/system-level research notes.
- Archive: unreviewed drafts, automation outputs, temporary notes, and experimental content.

## Publishing Model

Public pages filter out `draft: true`. Generated content is committed as draft MDX and reviewed before publishing.
