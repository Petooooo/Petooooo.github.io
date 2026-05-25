# Content Taxonomy

The automation layer supports draft organization only. It does not decide what is worth publishing.

## Collections

- `projects`: implementation records for systems in the lab. Use manually or with explicit `--collection projects` because projects require role, period, and status metadata.
- `research`: computer science, electrical/electronic engineering, systems engineering, AI infrastructure, software engineering, algorithms, and embedded/system-level engineering notes.
- `devops`: deployment notes, troubleshooting logs, terminal logs, infrastructure decisions, rollback notes, and operating records.
- `notes`: implementation notes, study notes, practical observations, and reusable technical references.
- `paper-reviews`: concise reviews of computer science, electrical/electronic engineering, systems, AI infrastructure, software engineering, algorithms, and embedded/system-level engineering papers.
- `archive`: temporary notes, experiments, migrated material, and older archive entries.

## Content Types

Use `type` for writing format:

- `concept`
- `troubleshooting`
- `problem-solving`
- `project-log`
- `runbook`
- `paper-review`
- `research-note`
- `implementation-note`
- `decision-record`
- `experiment-note`

Keep older `contentType` values only for legacy automation compatibility.

## Tags

Prefer concrete tags over broad identity tags.

Good examples:

- `astro`
- `github-pages`
- `docker-compose`
- `caddy`
- `raspberry-pi`
- `deployment`
- `debugging`
- `algorithms`
- `embedded`
- `ai-infrastructure`
- `systems`
- `typescript`

Avoid tags such as `thought-leadership`, `productivity`, `growth`, `viral`, or unrelated science labels that do not match this site.
