# RISC TOY source review — five-stage CPU reconstruction

**Review date:** 2026-11-20
**Article:** `/projects/risc-cpu-five-stage-pipeline/`
**Primary evidence:** User-provided 13-page PDF, *RISC CPU 설계.pdf* (2024 course report, RISC TOY).
**Source exposure:** Original PDF, personal student identifiers and teammate details are **not** committed or published.

## Original report examined

| Report pages | Evidence used in the article |
| --- | --- |
| 1 | IF/ID/EX/MEM/WB architecture, PC/Instruction Memory/Register File/ALU wiring and signal widths |
| 2–4 | IF register PC/target selection, `start` and `IREQ`, `INST_M`, ID pipeline register, Store-specific source address selection |
| 5–7 | EX pipeline register, arithmetic and shift/rotate instruction cases, branch/link and memory addressing, MEM access |
| 8 | Writeback timing difference caused by the synchronous register file and the `*_MA` signals |
| 8–9 | Three separate data-hazard cases; exact `valB`, `valC`, `DWDATA` forwarding expressions |
| 9–11 | One-cycle `stall_MEM` for load-use dependencies; two-cycle `stall_ID` on branch/jump opcodes and detection via `INST_M` |
| 11–12 | Custom PC 0–380 instruction test, expected register states, branch target and no-branch test scenarios |
| 13 | Simulated multi-register waveform image for the original implementation |

## Corrections to the initial short article

- Replaced generic processor explanation with the actual **pipeline register and control-signal architecture**.
- Added original **Store-specific decoding** (`STORE` changes the second source register address).
- Documented **MEM ALU**, **WB ALU** and **load-result** forwarding as three separate cases with grounded RTL snippets.
- Added the **one-cycle load-use stall** and explicit Store-data dependency, alongside the **two-cycle decode-side branch stall** (1 → 2 → 0).
- Explained the synchronous Register File read/write timing problem and the project's `ALU_OUT_MA`, `dest_MA`, `WEN_MA`, `MOUT_MA`, `op_MA` path.
- Transcribed selected instruction-test expectations instead of inventing throughput or FPGA implementation metrics.
- Replaced the original five-box schematic with a source-grounded feedback-path drawing; added a second source-grounded hazard decision diagram. The figures are conceptual, not physical routing or cycle-accurate waveforms.
- Independently rewrote the Korean edition to preserve technical meaning without literal translation or inflated claims.

## Technical details that should not be silently normalized

1. The original WB bypass expression for the **WB ALU result** checks `!DREQ_MEM`, rather than clearly checking the WB instruction's request state. The public article reproduces the reported expression and marks this as a potential additional regression case—not a proven production defect or corrected implementation.
2. The original control-hazard report says **three cycles to reach the target instruction** and describes a **two-cycle `stall_ID` state sequence**. The article preserves the difference.
3. The `always` and stall logic excerpts describe an academic RTL implementation and a limited testbench; they are **not** presented as formal verification, FPGA synthesis sign-off or a frequency result.
4. Personal identifiers on the report cover and the raw waveform are not republished.

## Release gate

- English article: substantially expanded with implementation tables, targeted Verilog excerpts and original test cases.
- Korean edition: manually authored with the same source-backed mechanisms and test results.
- English/SVG catalog entries: must pass the strict Korean-localization build.
- Review rendered diagram SVGs, EN/KO paths and noindex before publication.
- Commit only the article, Korean edition, localized source hash, revised and new SVG, localization catalogs, roadmap and this audit note.

**Next article:** The 64-page *Mini-Desktop 결과보고서.pdf* should drive the FreeRTOS article's revision, including actual GPIO inter-board signaling, UART print path, ten tasks by board, ultrasonic sensor input capture and `CoordinateMutex` synchronization. This is explicitly outside the RISC CPU milestone.
