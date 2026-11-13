# RocketChip DefaultConfig Performance Baseline

Date: 2026-11-13
Machine: Intel Xeon Gold 6530, 32 cores, 128GB RAM
Compiler: g++ 11.5.0 / Verilator 5.050
Design: freechips.rocketchip.system.DefaultConfig (FIRRTL 1.1.0, 628 modules, 275k lines)

## Results (-O3, empty-cycle methodology)

| Path | cycles/s | Notes |
|---|---|---|
| Chisel FIRRTL → Verilog → Verilator | 119,644 | CPU executing boot ROM, full design alive |
| fir2pyc → pycc C++ | 52,272 | Full design (29,047 regs), empty-input |
| fir2pyc → pycc Verilog → Verilator | blocked | pycc EliminateDeadInstances removes SimAXIMem |
| ESSENT C++ (reference) | 2,039 Dhrystones/s | Full-system dhrystone (471,043 cycles) |

## Chisel-side build
- FIRRTL compiler: rocketchip.jar (from essent-rocket-demo)
- Verilog: 9.77MB, 203k lines (TestHarness.v + behav_srams.v + SimDTM.v)
- Verilator: --cc -O3 -CFLAGS "-O3", DPI stub for debug_tick

## fir2pyc-side build
- .fir surgery: tools/fir_surgery.py (SimDTM extmodule → top-level ports)
- MLIR: 586k lines, pyc-opt PASS, pycc --emit=cpp --no-state-opt --logic-depth 1024
- C++: 56MB TU, g++ -O3 (2:44 compile, 3.79GB RSS)
