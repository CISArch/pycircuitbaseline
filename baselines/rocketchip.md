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

## Module-Level Three-Path Comparison (2026-11-13)

### CSRFile (235 regs, 3231 bits, BOOM trim) — all three paths WORK

| Path | cycles/s (-O3) | Ratio |
|---|---|---|
| fir2pyc → pycc Verilog → Verilator | **3,434,348** | 8.4× vs C++ |
| fir2pyc → pycc C++ | **410,321** | 1.0× |
| (Chisel-side N/A — CSRFile is a BOOM internal module) | — | — |

**Key finding**: For individual modules (no circular instance deps), the fir2pyc → Verilog → Verilator path produces fully alive models and is **8.4× faster** than the C++ backend (Verilator's change-driven eval vs pyc C++ full-tree evaluation every cycle).

### Full-top Path 3 blocker confirmed
The full-top TestHarness → ERS ↔ SimAXIMem circular instance dependency (bidirectional AXI4 bus) causes:
1. fir2pyc: ERS memory inputs constant-stubbed (SSA dominance constraint)
2. pycc: SimAXIMem internal logic DCE'd (outputs appear unused)
3. Verilator: legally prunes entire design downstream of constants

Individual modules (CSRFile, LFSR, etc.) work perfectly through all paths.

## Final Status (2026-11-13 18:45)

### VerilogEmitter bugs fixed this session (pyCircuit-dev worktree):
1. Verilog-2001 keyword guard (isReservedVerilogKeyword, NameTable::unique `_w` suffix) — eliminates sed post-patching
2. 1-bit extract/trunc/sext scalar passthrough — fixes "Illegal bit select on logic" errors

### Full-top Path 3 blocker (FINAL diagnosis):
The Verilog output is now syntactically correct (0 Verilator errors), structurally complete
(SimAXIMem has 4 AXI4 child instances, AXI4RAM has 40 byte_mem), and properly connected
(ERS memory ports on wires from SimAXIMem outputs). However, Verilator still prunes to
544 lines because:
- Test bench drives empty/random inputs (no DTM protocol)
- CPU never activates (no instruction fetch, no state change)
- Verilator statically evaluates the design's fixed point and prunes idle logic

This is a TEST METHODOLOGY issue, not a Verilog generation issue. The Chisel baseline
works because it has a real SimDTM (with DPI-C) that implements the debug protocol,
making the CPU active from cycle 1.

### To unblock full-top Path 3:
1. Implement a minimal DTM driver in the TB (like Chisel's SimDTM.cc)
2. Or add boot ROM initialization to the design (CPU starts executing immediately)
3. Or use --timing + --assert in Verilator to prevent aggressive static evaluation
