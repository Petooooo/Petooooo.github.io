# DevOps Log Summary Prompt

Convert infrastructure logs into a human-reviewable DevOps journal draft.

Include:
- Timestamp range.
- Services affected.
- Symptoms or reason for work.
- Commands run, if safe to include.
- Outcome.
- Lessons or monitoring improvements.

Remove sensitive paths, IPs, hostnames, tokens, and user data unless explicitly approved.

The output is a draft note, not a status update or blog post. Keep the writing factual: symptom, action, result, verification, rollback, and follow-up.
