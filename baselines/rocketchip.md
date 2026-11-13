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

## Path 3 (fir2pyc → pycc Verilog → Verilator) — BLOCKED (2026-11-13)

**Status**: Design pruned to empty shell by Verilator. Root cause chain:

1. `.fir` has circular instance dependency: ERS (ldut) ↔ SimAXIMem (mem) — bidirectional AXI4 bus
2. fir2pyc emits instances in .fir order → ERS first → ERS's memory input operands get constant stubs (SimAXIMem not yet in `inst_out_ssa`)
3. pycc canonicalizer sees ERS memory inputs as constants → SimAXIMem outputs appear unused
4. pycc EliminateDeadInstances removes SimAXIMem internal logic (debug_keep preserves the instance op but not the logic)
5. Verilog output has correct structure but constant-stubbed memory connections
6. Verilator legally prunes design tree downstream of constants

**Attempted fixes** (all documented in session logs):
- .fir surgery v3/v4: expand bidirectional aggregate connect to leaf connects ✅ (correct directions) but fir2pyc still can't emit ERS after SimAXIMem (operand count mismatch)
- .fir reordering (mem before ldut): operand count mismatch in ERS instance
- MLIR post-processing: too fragile (SSA name matching)
- Verilog post-processing (rewiring): correct structure but internal logic already pruned
- Two-phase instance emission in fir2pyc: SSA dominance violations in child modules
- pyc.debug_keep on SimAXIMem: preserves instance op but not internal logic

**Required fix**: Either (a) MLIR-level wire breaking for circular instance dependencies, or (b) pycc EliminateDeadInstances to not prune based on constant-folded consumers, or (c) pyc.ext_module black-box support (PR#12 direction).
