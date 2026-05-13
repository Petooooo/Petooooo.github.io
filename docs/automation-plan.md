# Automation Plan

Automation should assist writing, not bypass review.

This site is not for unattended publishing or bulk generated posts. Automation exists to turn raw engineering material into structured drafts that can be reviewed, corrected, and refined by a human.

## Supported Source Material

- troubleshooting logs
- terminal logs
- deployment notes
- implementation notes
- algorithm study notes
- system design notes
- infrastructure decisions
- debugging notes
- experiment notes
- paper review drafts within the site research scope
- practical engineering observations

Research automation is limited to computer science, electrical/electronic engineering, systems engineering, AI infrastructure, software engineering, algorithms, and embedded/system-level engineering.

## Future Flow

1. Raw notes, terminal logs, study notes, or scratch text land in `automation/raw/inbox`.
2. A local utility or future n8n workflow parses and sanitizes the source.
3. The source is classified by collection, content type, tags, and sensitivity.
4. A draft MDX file is written into `apps/web/src/content`.
5. The draft keeps `draft: true`, `reviewed: false`, and `reviewStatus: "needs-review"`.
6. A human reviews in Decap CMS or an editor.
7. Reviewed content is committed and pushed.
8. GitHub Pages deploys the public site. Optional RP4 deployment remains documented separately.

## Current Local Utility

```bash
npm run draft:from-note -- --source automation/raw/inbox/example.md
```

Useful options:

- `--collection notes|devops|research|auto-archive|projects`
- `--type troubleshooting-log|terminal-log|deployment-note|implementation-note|algorithm-study|system-design|infrastructure-decision|debugging-note|experiment-note|paper-review|engineering-observation`
- `--tags "docker,github-pages,deployment"`
- `--tech "Astro,Docker,Caddy"`
- `--title "GitHub Pages Deployment Check"`

## Quality Control

- Keep generated drafts unpublished.
- Include source metadata.
- Include a review checklist.
- Avoid low-value spam posts.
- Never include secrets.
- Prefer concise technical observations over polished article tone.
- Keep commands and evidence separate from interpretation.
- Use `automation/taxonomy.md` for collection and tag choices.
