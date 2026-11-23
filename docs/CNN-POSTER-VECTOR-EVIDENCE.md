# Bit-Shift-Based CNN Accelerator — evidence-to-diagram map

## Original poster checked

I reopened and visually inspected the user's actual **one-page 2024 Kyung Hee University team graduation poster**, *Bit-Shift-Based CNN Accelerator: A Compact and Energy-Efficient Solution*. The PDF is 2383.92 × 3370.32 pt and contains 19 bitmap image objects plus vector text and ornamentation.

The poster is team-authored, not a public source asset. **The website does not redistribute the original PDF or upscale its small FPGA placement screenshots.** The 13 new SVGs are true-vector *reconstructions* based on readable poster diagrams/measurements, not pixel-perfect originals. The earlier five analytical SVGs remain.

## Source-to-new-figure mapping

| Figure | Actual poster panel | Faithfulness boundary |
| --- | --- | --- |
| 01 custom-net | Background / Custom Net | 28×28 input; C1 4@25×25; S1 4@12×12; C2 8@9×9; S2 8@4×4; C3 16; output 10 |
| 02 ps-pl-architecture | Architecture / Full Architecture | FP32 and INT8/INT4 training→inference, PS, 16+16 BRAM banks, FSM and WS/IS arrays |
| 03 systolic-buffers | Background / Systolic Array | Weight/Activation/Accumulation buffers, illustrative subset of PEs |
| 04 ws-is-dataflow | Background / WS vs IS | Full WS 4×16 and IS 1×16 configurations; drawn grid is shortened |
| 05 im2col-mkn | Background / IM2COL | M=Cout, K=Ck×Ck×Cin, N=Hout×Wout |
| 06 single-pe | Architecture / Single PE | Input/Weight → shift → partial-sum addition, not actual gate netlist |
| 07 weight-cells | Multiply-free Calculation / Bitwise Shift | Exact 3×3 displayed source examples, encoding remains illustrative |
| 08 ste-training | Multiply-free Calculation / STE | Quantization forward, surrogate gradients backward |
| 09 inq-stages | Multiply-free Calculation / INQ | Stagewise quantization; colored selected indices are illustrative |
| 10 output-bram-dataflow | Architecture / Data Flow | DP1–DP8 and Output BRAM0–15, not measured cycle timing |
| 11 fpga-resources | Experiment Result / FPGA Implementation | LUT 12,603 vs 19,833; FF 8,786 vs 11,114; BRAM 34 vs 34 |
| 12 top1-accuracy | Experiment Result / Accuracy | All nine source-labeled scores, not a controlled cross-architecture study |
| 13 runtime-table | Experiment Result / Run Time | PS-only 15.9 ms vs PS+PL 8.83 ms, dual-core A9 667MHz |

## Boundaries

- Original bitmap screenshots are not zoomed to fictitious resolution. Native SVGs use scalable text and paths instead.
- The PE and BRAM layouts represent source-level component connections, not exact routed nets, waveforms or recovered clocks.
- Poster bit-shift notation for negative powers/sign has not been assumed to be a bit-exact hardware specification.
- The 36.5% LUT reduction, 0.6 percentage-point accuracy difference and PS-versus-PS+PL runtime have different baselines. The poster does not measure power/energy.
- Each new diagram has independent English/Korean figure labels; the Korean edition is not a literal translation.

Regenerate with: python3 apps/web/scripts/build-cnn-poster-vectors.py
Then build: npm run build --prefix apps/web
