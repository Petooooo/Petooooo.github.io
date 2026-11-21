# Source-grounded technical figure editorial standard

This is the default procedure for **one engineering project article at a time**. It supplements the portfolio's writing and publication checks. Source fidelity matters more than decorative consistency.

## Work from the original evidence

1. Locate the project's reports, PDFs, presentation files, simulations, code, screenshots, and figures.
2. Read the original technical context and inspect **every relevant figure** at readable resolution. Record figure number, caption, what the image actually proves, and whether underlying numerical data are available.
3. Preserve the original figure order and group related evidence by experiment. If the report has console logs, grid plots, kernel traces, or screenshots, do not replace them only with generic summary cards.
4. Identify restrictions before publication: ownership, private/internal architecture, addresses, credentials, personal information, unauthorized data, and publication rights. Extracted original material is not automatically safe to publish.

## Keep two different figure layers

**Source-faithful archive** comes first in the results appendix. Prefer a genuine SVG recreation preserving the original visual structure, labels, colors, geometry, and relative proportions. When the source is a raster screenshot or numeric reconstruction is impossible, place the **unmodified source image inside an SVG container** as an archival preservation option. This preserves appearance but is **not** a vector trace: state that distinction in the introduction or captions.

**Analytical vector redraws** come afterward. Show precisely the mechanism the reader needs: time–address layout, allocation conflict graph, dependency, measured comparison, timing sequence, or other subject-appropriate view. When source data contain exact values, use them; if individual offsets or coordinates were not recorded, explicitly label the diagram illustrative and avoid invented numerical precision.

These roles can coexist: a source image demonstrates what was recorded; an analytical diagram explains why it matters. Include a rich assortment of meaningful figures without creating redundant or irrelevant decoration.

## Build bilingual, verifiable evidence

- Integrate figures into the main narrative where relevant and into a labeled end-of-article archive when the report includes multiple images.
- Maintain an independent, natural Korean account at the opt-in `/kr/` route and preserve the original English/default route. Keep Korean figure captions distinct from raw Markdown syntax.
- Distinguish measured peak buffer allocation from total device RAM, kernel correctness, latency, energy use, or hypothetical gains.
- Preserve original numerical discrepancies with attribution instead of silently correcting the report or calling it a fresh rerun.
- Keep source screenshot wrappers, exact-data vectors, and schematic explanatory diagrams distinguishable in filenames and captions.
- Verify source-file integrity (hash when available), SVG XML parsing, figure links and counts, responsive layout, all localization strings, Astro check/build, Git diff safety, and the live Pages deployment.

## Completion protocol

Finish **one article before starting the next**. At the end of the actual publication cycle, report:

- the exact English and opt-in Korean article URLs;
- original figures preserved, native-vector figures added or retained, and what remains unverified;
- build and Pages deployment status, with actual Git commit when available;
- **one** recommended next article, with a brief explanation of the next source-based figure opportunities.

Do not claim publication or remote deployment from a local build alone. Do not stage unrelated personal or internal review documents.
