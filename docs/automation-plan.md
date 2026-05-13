# Automation Plan

Automation should assist writing, not bypass review.

## Future Flow

1. n8n trigger receives a GitHub event, schedule, webhook, or manual request.
2. Workflow collects source material.
3. AI model summarizes and classifies the source.
4. Workflow writes MDX with `draft: true`.
5. Workflow commits to GitHub.
6. Human reviews in Decap CMS or editor.
7. Published content deploys to RP4.

## Quality Control

- Keep generated drafts unpublished.
- Include source metadata.
- Include a review checklist.
- Avoid low-value spam posts.
- Never include secrets.
