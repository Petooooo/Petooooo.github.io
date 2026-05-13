# AGENTS.md

This file is the authoritative operational manual for future Codex sessions working in this repository. Preserve these rules unless the project owner explicitly changes the platform direction.

## Project Goal

Build and maintain a personal engineering and research lab notebook: projects, technical notes, research archive, DevOps journal, manual CMS, and automation-ready draft archive.

The platform should demonstrate real ownership of modern web engineering, deployment, operations, and automation on a Raspberry Pi 4 server.

## Long-Term Vision

This project is intended to evolve into:

- A practical engineering knowledge archive.
- A self-hosted technical lab notebook.
- A DevOps and research documentation platform.
- An automation-assisted content organization system.
- A credible proof that the owner can build, deploy, operate, and automate a production-quality platform independently.

Do not optimize only for a short-lived demo. Maintainability, clear architecture, and operational reliability matter.

## Tech Stack

- Astro with TypeScript
- Tailwind CSS
- MDX and Astro content collections
- Decap CMS under `/admin`
- Docker Compose
- Caddy
- GitHub as source of truth
- Raspberry Pi 4 deployment target

## Directory Structure

- `apps/web`: Astro application.
- `apps/web/src/content`: Markdown and MDX collections.
- `apps/web/public/admin`: Decap CMS admin.
- `infra/caddy`: Caddy configuration.
- `infra/scripts`: RP4 deploy and backup scripts.
- `automation`: n8n notes, prompt templates, and draft-generation scripts.
- `docs`: architecture, deployment, workflow, and automation docs.

## Commands

```bash
npm install --prefix apps/web
npm run dev
npm run check
npm run build
docker compose build
docker compose up -d
```

Use Node.js 20+ for local development and builds. Astro 5 requires a modern Node runtime.

## Architecture Philosophy

The platform is static-first, Git-first, and content-first.

Astro is used because it produces fast static sites, supports MDX, keeps JavaScript payloads low by default, and fits a technical notebook and knowledge archive better than a heavy full-stack framework. Prefer Astro server-side or client-side features only when the product genuinely needs them.

Markdown and MDX are used because technical writing, research notes, runbooks, and implementation records should be version-controlled, diffable, portable, and easy to edit outside any specific CMS.

GitHub is the source of truth. Code, content, generated drafts, infrastructure files, and documentation should be reviewable through Git history. Avoid workflows that create important state only inside a running service.

The static-first architecture is intentional. It lowers operational risk, improves performance, reduces memory usage, and makes the platform practical to host on a Raspberry Pi 4.

Decap CMS exists as a manual editing interface over the Git content model. It should not replace Git or introduce hidden content storage.

Docker Compose is used for repeatable deployment on the RP4 without requiring a complex orchestrator.

Caddy is used because it is lightweight, production-grade, easy to configure, and HTTPS-ready for DDNS/domain deployment.

RP4 self-hosting is part of the product identity. The site should feel personally built and operated, not like a generic hosted template.

Heavy backend and database complexity is intentionally avoided. Do not add a database, queue, custom API, SSR runtime, or background worker unless there is a clear product need that cannot be solved with static generation, Git, scripts, or n8n.

## Raspberry Pi 4 Constraints

The deployment target is resource-constrained compared to cloud servers. Optimize for reliability and low operating overhead.

- Prefer static rendering.
- Minimize runtime memory usage.
- Avoid unnecessary background services.
- Keep Docker images lightweight.
- Prefer multi-stage Docker builds.
- Avoid heavy SSR usage.
- Avoid unnecessary database usage.
- Optimize for ARM compatibility.
- Avoid dependencies that require fragile native builds on ARM unless clearly justified.
- Keep container count low.
- Prefer simple shell scripts for deploy and backup workflows.
- Do not introduce Kubernetes on the RP4 for this project unless the owner explicitly requests it.
- Treat idle CPU and memory usage as production concerns.

## UI/UX Philosophy

The platform should feel modern, premium, engineering-focused, self-hosted, systems-oriented, and technically serious.

Visual inspiration:

- Vercel
- Linear
- GitHub
- Raycast
- Apple Developer
- Anthropic

Typography should be clean, restrained, and readable for long technical posts. Use strong hierarchy, but avoid oversized marketing typography inside dense application or archive views.

Spacing should be consistent and calm. Favor generous section spacing, tight internal component spacing, and predictable rhythm across pages.

Cards should feel like professional system surfaces: subtle borders, restrained backgrounds, clear hierarchy, and no unnecessary decoration. Avoid nesting cards inside cards.

Borders should be soft and functional. Use them to separate surfaces, define cards, and organize dense information. Do not over-outline every element.

Dark mode is the primary design mode. Light mode may be supported, but it must not degrade contrast, hierarchy, or brand feel.

Animation should be minimal and purposeful. Use subtle hover states and small transitions. Avoid excessive motion, decorative animation, or effects that distract from technical content.

Responsive design must be first-class. Pages should feel polished on mobile, tablet, and desktop, with no overlapping text, broken grids, or cramped navigation.

UI anti-patterns:

- Avoid Bootstrap-like appearance.
- Avoid clutter.
- Avoid random colors.
- Avoid noisy gradients.
- Avoid excessive animation.
- Avoid generic blog-template appearance.
- Avoid childish colors or novelty visuals.
- Avoid decorative UI that does not support the content.
- Avoid making the site feel like a marketing landing page instead of a living engineering platform.

## Astro Architecture Rules

- Use layouts for shared page shell, metadata, navigation, and article rendering.
- Use reusable components for cards, section headers, lists, tags, and repeated UI patterns.
- Treat content collections as the source of truth for projects and posts.
- Keep typed schemas in `apps/web/src/content/config.ts`.
- Add fields to schemas deliberately and keep Decap CMS config aligned with schema changes.
- Organize pages by route under `apps/web/src/pages`.
- Keep dynamic routes simple and collection-driven.
- Filter out `draft: true` content from public routes.
- Handle SEO metadata at the layout level where possible.
- Include useful page titles, descriptions, canonical URLs, RSS, sitemap, and Open Graph metadata.
- Render MDX through shared content layouts unless a page needs a specialized case-study presentation.
- Do not scatter one-off metadata logic across many pages.

## Component Rules

- Keep components focused, reusable, and composable.
- Avoid duplicated styling across pages.
- Avoid page-specific hardcoded components when a reusable component would be clearer.
- Keep components small and maintainable.
- Prefer props over copying variants.
- Preserve accessible HTML semantics.
- Keep visual primitives consistent across cards, tags, buttons, lists, and article headers.
- Do not create abstractions that hide simple Astro markup without reducing real complexity.

## Coding Conventions

- Keep components focused and reusable.
- Prefer Astro static rendering unless a real runtime need exists.
- Use TypeScript for config and automation scripts.
- Keep content schemas typed in `apps/web/src/content/config.ts`.
- Use accessible HTML and semantic page structure.
- Avoid large monolithic files.
- Prefer clear naming over clever naming.
- Keep comments short and useful.
- Avoid hardcoded production-specific values unless they are documented placeholders.

## Content Rules

- Do not publish generated content by default.
- Generated content must use `draft: true` and `autoGenerated: true`.
- Include source metadata where available.
- Remove secrets, private IPs, tokens, and sensitive personal data.
- Use realistic technical writing, not filler.

## Content Writing Rules

Writing should be concise, technical, and useful to a future reader.

- Avoid AI filler text, generic summaries, and vague claims.
- Prefer concrete context, decisions, commands, outcomes, risks, and follow-ups.
- Use meaningful headings that describe the content below them.
- Keep Markdown structure clean and scannable.
- Use syntax-highlighted fenced code blocks with language identifiers.
- Include diagrams only when they clarify architecture, flow, or tradeoffs.
- Use images and figures when they show real systems, screenshots, outputs, or research artifacts.
- For math-heavy research notes, use consistent notation and explain assumptions before conclusions.
- Do not invent sensitive personal details, credentials, incident data, or production facts.
- Keep DevOps logs factual: what changed, why, impact, verification, and rollback notes.

## Auto-Generated Content Rules

Generated content is allowed only as draft material until reviewed.

- Auto-generated posts must default to `draft: true`.
- Auto-generated posts must include `autoGenerated: true`.
- Auto-generated posts must include `source` metadata.
- Auto-generated posts should include `sourceUrl` when available.
- Auto-generated posts must include `generatedAt` once the schema supports it.
- Auto-generated posts must include `reviewed: false` once the schema supports it.
- Include a human review checklist in the body.
- Avoid meaningless activity spam.
- Never auto-publish infrastructure incidents.
- Never include secrets, tokens, private IPs, internal hostnames, or sensitive logs.
- Prefer fewer, higher-quality generated drafts over frequent low-value summaries.
- Publishing requires explicit human review and changing the draft status.

## Automation Workflow Philosophy

Automation should assist knowledge capture, not replace engineering judgment.

Future workflow:

1. Collect GitHub activity, repository changes, infrastructure logs, or study notes.
2. Summarize and classify source material using AI.
3. Generate MDX drafts with safe frontmatter.
4. Commit drafts to GitHub.
5. Review through Decap CMS, editor, or pull request.
6. Publish only after human approval.

n8n is the likely orchestration layer for triggers, scheduled jobs, webhooks, GitHub operations, and AI calls.

OpenAI integration should use environment variables or n8n credentials. Never hardcode API keys.

Automation should preserve source traceability. A reader should be able to understand where a generated draft came from and why it exists.

## Design Rules

- Dark mode first, light mode supported.
- Professional, systems-oriented visual language.
- Avoid generic blog-template appearance.
- Avoid excessive animation and clutter.
- Keep responsive layouts polished on mobile, tablet, and desktop.

## Deployment Rules

- RP4 should pull from GitHub and deploy with Docker Compose.
- Caddy serves the built static site.
- Keep runtime small and RP4-friendly.
- Do not introduce a database unless there is a clear need.

## Deployment Workflow

Expected flow:

1. Local development.
2. Push to GitHub.
3. RP4 pulls latest changes.
4. Rebuild containers.
5. Restart services.

Local development may happen on Windows, WSL, or VSCode Remote SSH. Keep commands and scripts portable where practical, but deployment scripts may target Linux on the RP4.

GitHub remains the source of truth. The RP4 should not contain uncommitted production-only code or content.

Docker Compose builds and runs the production container. The runtime should serve static Astro output through Caddy.

Caddy serves the site and handles compression, headers, and HTTPS when a real domain is configured.

ipTIME DDNS assumptions:

- A DDNS hostname points to the home network.
- Router port forwarding sends `80` and `443` to the RP4.
- Caddy can request certificates when DNS and ports are correct.
- If HTTPS is not available yet, leave clear placeholders and documentation.

## Asset Management Rules

- Prefer optimized images.
- Prefer WebP for new raster assets when browser support is acceptable.
- Keep thumbnails consistent in aspect ratio.
- Store content assets in predictable public folders.
- Avoid oversized original images in the repository.
- Use descriptive filenames.
- Add alt text for meaningful images.
- Do not commit private screenshots, internal dashboards, tokens, logs, or identifiable sensitive data.
- Use generated or placeholder visuals only when they support the page purpose.

## Security Rules

- Never commit secrets.
- Use environment variables for credentials and deployment-specific values.
- Never hardcode API keys.
- Never use fake production credentials.
- Never expose private infrastructure details.
- Sanitize auto-generated content before publishing.
- Do not publish private IPs, hostnames, access tokens, SSH details, logs with personal data, or internal network diagrams unless explicitly approved.
- Keep `.env` out of Git.
- Document required variables in `.env.example`.
- Treat Decap CMS authentication and GitHub OAuth configuration as production security concerns.

## Performance Rules

- Optimize for Lighthouse performance.
- Minimize JavaScript payload.
- Prefer static generation.
- Minimize client-side hydration.
- Optimize image loading.
- Avoid heavy client libraries unless they provide clear value.
- Keep CSS maintainable and avoid unnecessary global complexity.
- Prefer progressive enhancement over client-only behavior.
- Watch bundle size when adding dependencies.

## Documentation Rules

README and docs must always explain:

- Architecture.
- Local development.
- RP4 deployment.
- Docker deployment.
- Caddy configuration.
- Decap CMS setup.
- GitHub workflow.
- Automation plans.
- Backup strategy.
- Troubleshooting.

Update documentation whenever behavior, commands, deployment assumptions, content schema, or automation workflow changes.

## Git Workflow Recommendations

Branch naming:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `content/<short-description>`
- `infra/<short-description>`

Commit style:

- Use clear imperative commit messages.
- Prefer small, reviewable commits.
- Keep code, content, and infrastructure changes separated when practical.

Content update workflow:

1. Create or edit MDX content.
2. Keep drafts as `draft: true` until reviewed.
3. Run checks/build.
4. Push to GitHub.
5. Deploy from RP4.

Deployment workflow:

1. Merge or push approved changes.
2. SSH into RP4.
3. Pull latest repository state.
4. Run `./infra/scripts/deploy.sh`.
5. Verify the site and logs.

## Done Criteria

A task is only complete when:

- Code builds successfully, unless blocked by a documented environment issue.
- Changed files are summarized.
- Deployment impact is explained.
- RP4 compatibility is preserved.
- Documentation is updated if necessary.
- Content schema and Decap CMS config remain aligned when content fields change.
- Draft and auto-generated content rules are preserved.
- No secrets or private infrastructure details are introduced.

## Do Not

- Do not expose secrets.
- Do not hardcode real tokens.
- Do not use fake production credentials.
- Do not publish auto-generated content by default.
- Do not create unnecessary backend complexity.
- Do not replace Markdown content workflow with a heavy CMS.
- Do not make the UI look like a generic template.
- Do not break Raspberry Pi 4 compatibility.
