# Historical CV project recovery and chronology audit

**Review date:** 2026-11-20
**Repository:** Petooooo/Petooooo.github.io
**Decision:** Publish six evidence-supported retrospectives, preserve two existing 2024 feature articles, and retain a concise four-project CV.

## Scope and source selection

I compared the older CV/portfolio project candidate lists and the author's later conversations against the currently published Projects. The older CV included meaningful **computer architecture, embedded/RTOS, compiler and application development** that had been almost entirely absent from the new site.

The strongest historical evidence includes a prior four-project CV shortlist, earlier project timelines, detailed descriptions from author conversations, the original 2024 TFLM report and CNN team poster already used on this site, and the public [Green Reviewer repository](https://github.com/Petooooo/green-reviewer) (confirmed to contain a Flutter client and server-side components). Other historical projects have only CV/discussion summaries, so no lost source code, synthesis report, benchmark or test count was invented.

## Article and timeline decisions

| Project | Recorded original period | 2026 publication decision | Evidence / boundary |
| --- | --- | --- | --- |
| Escape From the Dark · Verilog VGA FPGA game | May–Jun 2023 | New archived project article and bilingual figure | Original CV identifies DE2/VGA/Verilog; no unverifiable controls or resource counts |
| Green Reviewer · Flutter + backend | Sep–Dec 2023 | New archived project article and bilingual figure | Public GitHub client/server, README for backend services and Docker Compose; no live-service guarantee |
| PyTokenizer · C/Lex/Yacc | Oct–Nov 2023 | New archived compiler front-end article and bilingual figure | CV records tokenization and syntax analysis; no full Python grammar conformance claim |
| FreeRTOS Mini-Desktop · three STM32 boards | Oct–Nov 2023 | New CV-core + archived project article and bilingual figure | Ten concurrent tasks, UART/GPIO, priorities, mutexes, desktop interactions and sleep/resume from earlier CV |
| Systolic Array matrix multiplier on FPGA | Apr–May 2024 | New archived hardware-dataflow article and bilingual figure | CV records separate FPGA matrix-multiply project; CNN metrics are not ascribed to this precursor |
| Five-stage RISC CPU | May–Jun 2024 | New CV-core + archived project article and bilingual figure | Two-person project; user implemented datapath/control and forwarding, load-use stalls, branch/jump hazards, custom testbenches |
| TFLite Micro memory planning | Sep–Dec 2024 | Existing featured + CV-core article preserved; project chronology metadata corrected | Original report and quantified 28.33%/14.06% memory reductions |
| Bit-shift CNN accelerator on Zynq | Sep–Dec 2024 | Existing featured + CV-core article preserved; chronology metadata corrected | Team poster and detailed implementation ownership; fixed a duplicated English sentence |

## Site information architecture

- Existing two prominent 2024 projects remain featured alongside the K3s platform overview.
- A new **Undergraduate · 2023–2024** section presents six additional projects in original **completion-period chronology**.
- The CV contains the four strongest and most relevant systems/embedded projects: TFLite Micro, Bit-shift CNN, RISC CPU and FreeRTOS.
- Homepage experience chronology and About introduction now include CPU/RTOS background.
- Eight historically archived project pages display **Project period** and **Retrospective edited**, not a false claim that the articles were published during 2023–2024. The `date` front matter uses an approximate month-appropriate ordering value; the actual year/month is carried in `period`.
- English content and independently edited Korean essays have matching figures. Korean editions remain opt-in through the existing `/kr/` implementation and `noindex`.

## Not promoted to standalone projects

- **Crime Prevention IoT:** previously expressly excluded from the final CV; do not undo that preference without new direction.
- **PTSD/Arduino study-time tracker** and **basic digital clock:** valid learning experience but insufficient differentiation and detailed evidence for prominent case studies.
- **Linux as a main OS for a semester:** appropriately part of early Linux background and study notes; not represented as an independently built production system.
- **M8 Remote Chat/MCP, later infrastructure work and document translation:** modern projects or future candidates, not historically backdated 2023–2024 undergraduate work.

## Validation and maintenance

- `npm run check --prefix apps/web`: 34 published titles, 0 Astro errors/warnings/hints.
- `npm run build --prefix apps/web`: 151 generated static pages; 34 manually edited Korean project pages, 150 opt-in Korean HTML pages, 96 bilingual SVGs, zero unknown English strings and zero Korean edition checker errors.
- Old public project URLs were kept stable; newly written pages use their own subject-led slugs.
- A paired EN/KO audit should verify the six new pages, old 2024 pages, figures, CV, project chronology and displayed period labels before publishing.
- The user-authorized publication decision to write these retrospectives is not a claim that historical source repos or all original project files are available today.

**Editorial principle:** Preserve substantial historical work, but place the strongest four projects in the short CV and the supporting implementations in an archive. Distinguish **when the work was done** from **when the retrospective was written**.
