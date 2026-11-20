# TFLite Micro — source-driven technical and visual reconstruction

**Editorial review:** 2026-11-21
**Published article:** `/projects/tflite-micro-lifecycle-memory-planning/`
**Historical project period:** Sep–Dec 2024
**Primary source:** user-provided eight-page undergraduate paper *Memory Management through Lifecycle Analysis in TFLite Micro for Resource-Constrained Devices* (2024). The original PDF and its personal identifiers remain out of the public repository.

## Source review and reasoning restored

| Source | Updated article |
| --- | --- |
| Report pp. 1–2, Figures 1–4 | Why lifetime-aware Greedy already reuses disjoint tensor lifetimes, and why it cannot infer safe in-operator partial overlap from the available information alone |
| Report p. 3, Figures 5–7 | Convolution last-read motivation, valid input/output overlap vs overwrite-too-early case, `Conflict[A,B] = [-L, K]` and `{A,B,-L}` descriptor |
| Report p. 4, Figures 8–9 | Output-first reverse BFS graph traversal, original non-conflict buffers first, candidate-offset modification `offset(B) + size(B)` vs `offset(B) + L` |
| Report p. 5, Figures 10–16 | Constructed eight-buffer trace; non-conflict IDs 0/1/5/7 before conflict IDs 2/3/4/6; distinct overlap decisions for 3–4, 4–6 and 2–3; 4,101 → 3,585 B |
| Report pp. 5–7, Figures 17–21 | TFLM integration using Conflict Data array and count, Person Detect baseline/optimized layout, 55,296 → 39,636 B |
| Report pp. 7–8, Figures 22–26 | Tiny U-Net baseline/optimized layout, 230,416 → 198,120 B, source notes about long lifetimes/large tensor sizes |
| Later 2024/2026 implementation discussions | Header-based manual `conflict.h` data, known input last-use reasoning, observed too-aggressive overlap boundary and its correction; distinction from broad model correctness verification |

## Ownership and accuracy rules

- The author analyzed the original memory planner, implemented conflict-aware C++ buffer ordering and offset-selection logic, integrated the planner with TFLM and evaluated its planned peak allocations.
- The actual model-specific Conflict Data in the experiments was **manually computed by a teammate**. The article now explains *how* such input/output boundary information is derived (read order, last-use, output-write order, and other consumers) rather than falsely attributing automatic conflict extraction to the author.
- Automatic compiler/kernel profiling and exhaustive baseline-vs-optimized inference equivalence were **not completed** as a general system. They are explicitly presented as follow-up research.
- Avoid claiming an unconditional safe in-place convolution: SIMD, tiling, stride, padding, data layout and other live readers can change the bound.
- A remembered local too-aggressive overlap bug was corrected in the project, but that local debugging event is not rebranded as formal end-to-end validation.
- The article keeps numeric source discrepancies visible: report quotes Person Detect 28.33% and Tiny U-Net 14.06%; percentages computed from its recorded byte totals are ~28.32% and ~14.02%.

## New illustrations and results gallery

The previous article stopped after a summary table and only three conceptual figures. The revision adds an in-operator last-use progression and a manual Conflict Data extraction flow, then closes with a **final experimental results gallery**.

All new on-site diagrams are **native SVG** and have Korean SVG-localized versions.

| New SVG | Source and role |
| --- | --- |
| `tflm-convolution-last-use.svg` | Explains the last-read intuition of Figure 5 (illustrative kernel progression) |
| `tflm-conflict-extraction.svg` | Separates manual model-specific extraction from planned automatic profiling |
| `tflm-result-constructed-baseline.svg` | Figures 10–13, baseline 4,101 B |
| `tflm-result-constructed-optimized.svg` | Figures 14–16, optimized 3,585 B |
| `tflm-result-person-detect-baseline.svg` | Figures 17–18, baseline 55,296 B |
| `tflm-result-person-detect-optimized.svg` | Figures 19–21, optimized 39,636 B |
| `tflm-result-tiny-unet-baseline.svg` | Figures 22–23, baseline 230,416 B |
| `tflm-result-tiny-unet-optimized.svg` | Figures 24–26, optimized 198,120 B |
| `tflm-result-peak-summary.svg` | Exact source byte totals and source-reported percentages, grouped comparison |

**Disclosure about visual evidence:** The numeric SVGs reproduce confirmed **peak byte results** and high-level ordering/placement constraints. Their colored memory bars are not an exact transcription of *each* original buffer offset and should not be mistaken for the original simulation screenshots or a new run. Original screenshot images were inspected for evidence but the raw PDF is not publicly hosted.

For preservation outside the repo, the 17 **original screenshots** from report Figures 10–26 were additionally extracted and packaged as self-contained SVG containers with the JPEG pixels embedded. This archive is a separate downloadable user artifact, not part of the published site. Embedding source JPEG pixels is **not a pure vector trace**, and the distinction is documented in its README.

## Regression checks

- English MDX / manually authored Korean article and all figure URLs
- `npm run check --prefix apps/web`
- `npm run build --prefix apps/web`
- All new and existing public SVG XML well-formed
- Source/English editorial SHA acknowledgment and opt-in Korean `/kr/` noindex
- Rendered HTML must show the results gallery as the article's **last section**, with each baseline and optimized SVG pair
- Numeric totals and declared scope correct; no fabricated runtime timings, per-buffer offsets or private report metadata

Next source-based revision remains the FreeRTOS 64-page report.
