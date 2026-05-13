# Commit Summary Prompt

Given a Git commit range, generate a draft engineering log.

Focus on:
- What changed.
- Why it changed.
- Operational impact.
- Any deployment or rollback notes.
- Follow-up tasks.

Never publish automatically. The output must use `draft: true`.
Avoid release-note polish unless the source actually contains a release. Treat the draft as an engineering log that still needs review.
