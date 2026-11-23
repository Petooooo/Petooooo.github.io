# RISC TOY — source-to-SVG editorial evidence map

Review date: 2026-11-24

## Primary source reopened

User-provided 13-page PDF: **RISC CPU 설계.pdf** (2024, *Project 2 – RISC TOY*). The original includes the names and student IDs of two teammates and is **not committed or redistributed**. Existing contextual notes: docs/RISC-CPU-ORIGINAL-REPORT-REVIEW-2026-11-20.md.

Important original figures and their intrinsic raster dimensions:

| Source page | Figure and original pixel dimensions | Public handling |
| --- | --- | --- |
| 1 | Overall IF/ID/EX interface diagram, 1254 × 684 | Recreated as a native SVG with the component/field/bus layout, not a bitmap stretch |
| 2 | EX/MEM/WB continuation, 1072 × 621 | Recreated as a native SVG, retaining ALU/Data Memory/WB/target relationships |
| 12 | Original multi-signal simulator screenshot, 1534 × 881 | Retained only in the original PDF; no fabricated transition locations |
| 13 | Original multi-signal simulator screenshot, 1536 × 757 | Retained only in the original PDF; no fabricated transition locations |

Reconstruction is **not equivalent to copying the original signal coordinates, netlist, or waveform**. The SVGs are independently authored, scalable text/path illustrations. A screenshot transcribed with unverified wave edges would distort the original evidence.

## Source-to-vector mapping

| New SVG file | Original report page(s) | Grounding and limitation |
| --- | --- | --- |
| 01 if-id-original | 1 | IF Pipe-reg, PC Mux, PC+4, Instruction Memory, ID Pipe-reg, Register File and EX Pipe-reg; bus paths simplified |
| 02 ex-mem-original | 2 | ALU, MEM Pipe-reg, Data Memory, WB Pipe-reg, target and writeback; not an exact physical schematic |
| 03 instruction-fields | 1, 4–5 | INST[31:27], INST[26:22], INST[21:17], INST[16:12], offset_17/22 and shift/branch fields |
| 04 fetch-stall-path | 2–3 | PC hold/redirect, INST_M and INST capture; schematic rather than measured timing |
| 05 store-register-select | 4 | ST/STR select rc_ADDR_M from INST[26:22] instead of INST[16:12] |
| 06 forwarding-cases | 8–9 | MEM ALU, WB ALU, and load after stall |
| 07 forwarding-priority | 9 | valB/valC ternary ordering and unusual !DREQ_MEM guard in the WB branch preserved, not silently corrected |
| 08 load-use-stall | 9–10 | stall_MEM, one-cycle hold, MOUT and Store Data dependencies |
| 09 branch-stall-states | 10–11 | BR/BRL/J/JL opcodes 15–18; detection from INST_M[31:27]; stall_ID 1→2→0 |
| 10 writeback-ma-timing | 8 | MA Writeback signals and synchronous Register File behavior |
| 11 rotate-right-datapath | 5–6 | {valB,valB} >> shamt or valC[4:0] followed by lower 32-bit selection |
| 12 testbench-checkpoints | 11–12 | Real test-plan expectation values, not rerun test measurements |
| 13 waveform-evidence | 12–13 | Describes that no-branch and redirect-to-PC0 screenshots exist; does not impersonate the actual trace |

Earlier SVGs (risc-five-stage-hazards.svg and risc-hazard-control-timeline.svg) remain conceptual summary diagrams and are not claimed to match every source bus.

## Report details retained without fictitious precision

- PC normally increases by 4; the conditional logic holds PC during stalls, or redirects to target on Branch.
- Register File is synchronous and changes the Read/Write timing assumptions.
- Three original forwarding cases and one load-use stall are explicitly documented.
- Two stall_ID states 1 and 2 are explicitly used; the report separately speaks of three cycles to the branch target. Neither claim implies an independently recovered timing waveform.
- Original validation was an instruction-level test plan (PC 0–380) and simulator waveforms, not a current formal verification suite.
- The original forwarded WB result guard uses !DREQ_MEM where a WB-stage memory control condition might otherwise be expected. It remains a review question, not a confirmed defect.
- Source screenshots are approximately 1254×684, 1072×621, 1534×881 and 1536×757; small bitmaps were not artificially enlarged on the site.
- The raw PDF, names, student IDs, and unedited source screenshots were not copied into the site.
- No fresh FPGA frequency, IPC, clock trace, LUT count or performance metric has been invented.

## Regeneration and release checks

Regenerate figures with:

```bash
python3 apps/web/scripts/build-risc-report-figures.py
npm run check --prefix apps/web
npm run build --prefix apps/web
```

Review the English and Korean editions of /projects/risc-cpu-five-stage-pipeline/, confirm 15 figures in each version, verify both old and new SVGs have localized text, and inspect SVGs on desktop/mobile layouts before publication.
