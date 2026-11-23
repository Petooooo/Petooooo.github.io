# FPGA Systolic Array — evidence, scope and vector diagrams

## Historical basis

User-supplied personal 2024 project/CV entry, titled **Systolic Array Calculator on FPGA Board**:
- Period: April–May 2024
- Role: full development
- Language: Verilog
- Outcome described: FPGA systolic-array matrix multiplication accelerator designed for convolution-oriented operations; IM2COL mentioned

An older portfolio sentence makes a qualitative GPU comparison, but **does not preserve** the device model, matrix shapes, baseline implementation, memory-transfer cost, benchmark repetitions, clocks, or numeric measurements. Do not turn that sentence into a quantified speedup.

No recovered original RTL repository, simulation trace, PE dimensions, bit widths, actual input sequence, FPGA utilization report, logic analyzer data or reproducible hardware benchmarks were located in the material available to this editorial pass. The project date and hardware achievement are supported as *the personal project record*, not reverified from the original source hardware.

## Separate modern educational example

To explain *why* operand timing matters without fabricating original traces, the portfolio contains a new, independently reproducible **2×2 output-stationary reference model**, not claimed as the 2024 topology.

- A = [[1,2],[3,4]]
- B = [[5,6],[7,8]]
- Reference result: C = [[19,22],[43,50]]
- Reference schedule: t = i + j + k, where i/j/k start at 0, and t labels an **abstract logical MAC slot**, not a physical FPGA register edge
- Eight multiply-accumulate events across logical slots 0 through 3
- C00 completes t=1; C01/C10 complete t=2; C11 completes t=3
- An independent 3×3 input and 2×2 filter IM2COL example yields four -4 outputs
- Width, reset, integer sign handling, overflow and exact latency remain implementation-dependent

Reproduce the checks and redraws:

```bash
python3 apps/web/scripts/build-fpga-systolic-figures.py
npm run build --prefix apps/web
```

## Figure inventory and evidential boundaries

| Asset | What it represents | What it must not be read as |
| --- | --- | --- |
| 01 matmul-example | Exactly checked new A × B = C example | An archived test-vector screenshot |
| 02 pe-grid | Output-stationary A-right, B-down reference | Recovered physical FPGA PE floorplan |
| 03 pe-anatomy | Illustrative registers, MAC, accumulator, output | Original RTL/block schematic |
| 04 skew-streams | Computed edge-injection schedule for t=0..3 | 2024 testbench input trace |
| 05 wavefront-steps | Per-PE intermediate sums from reference model | Original waveform or hardware result |
| 06 valid-timeline | Computed output-ready slots | Exact FPGA clock-edge latency |
| 07 skew-counterexample | Deliberate error from missing B-column skew | A bug observed in 2024 |
| 08 im2col-example | Synthetic 3×3 image and 2×2 kernel arithmetic | Original CNN model/data/buffer placement |
| 09 evidence-boundaries | Separation between archival claims and new illustrative proof | An engineering KPI chart |

All are newly authored native SVGs; no rasterized original diagram, screenshot upscaling, or source file impersonation. The existing generic array SVG remains in the repo but is replaced in the revised case-study figure narrative.

## Editorial requirements

The English and manually edited Korean editions must each start with a matching project-context blockquote, include all nine figures in equivalent technical order, and end with natural engineering reflection and source boundaries. Korean text may retain established terms such as Systolic Array, Input Skew, PE, MAC and Output Valid. Technical illustration terminology is localized in the SVG translation dictionary without overwriting pre-existing glossary entries.

The later **Bit-Shift CNN Accelerator on Zynq** is a separate team capstone with its own design and measured resource/accuracy/runtime results. It may be cross-linked as a later learning step, but those measurements cannot be assigned to this earlier Verilog project.

## Background only

N. P. Jouppi et al., *In-Datacenter Performance Analysis of a Tensor Processing Unit*, ISCA 2017. Used only for general background on systolic dataflow; it does not supply evidence about the user's 2024 FPGA.
