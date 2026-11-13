# BOOM Performance Baseline

Date: 2026-11-13
Machine: Intel Xeon Gold 6530, 32 cores, 128GB RAM
Compiler: g++ 11.5.0 / Verilator 5.050

## Results (-O3, empty-cycle methodology)

| Path | cycles/s | Notes |
|---|---|---|
| fir2pyc → pycc C++ | **226,163** | BoomTrimHarness (571 modules, 58,012 regs) |
| Chisel FIRRTL → Verilog → Verilator | **60,300–60,500** | Full BoomConfig (849 modules; scala firrtl 1.6.0, 3-run median) |
| Chisel (firtool) → Verilog → Verilator | **61,640** | Same design; CIRCT firtool-1.75.0 output (cross-validated) |

**Note**: The fir2pyc path uses a TRIMMED BOOM harness (BoomTrimHarness, smaller than full BoomConfig).
The Chisel path uses the FULL BOOM design from firtool. These are DIFFERENT design sizes — the
3.7× "advantage" of fir2pyc C++ is partly explained by the smaller design.

## Chisel-side build (scala FIRRTL path — primary)
- Input: boom.system.TestHarness.BoomConfig.fir (27.4MB, 849 modules, chisel3 3.2)
- Node hoisting: 13 when-scoped nodes hoisted (chisel3 3.2 scoping → firrtl 1.6.0 compatibility)
- FIRRTL compiler: firrtl 1.6.0 (coursier cache), ~1 min compile
- Verilog: 21.7MB, 330 modules + behav_srams.v (11 SRAM macros incl. 32Mi×64 DDR)
- Runtime: boom-template vsrc + SimDTM_clean.v + DPI stub
- CRITICAL: -DSTOP_COND=0 required (pipeline-hang assertion fires on empty memory)
- Verilator: --cc -O3 -CFLAGS "-O3" --no-timing
- Liveness: 500k cycles take 8.27s, 71.5MB generated C++, hang-assert fired pre-fix

## Chisel-side build (CIRCT firtool shortcut — cross-validation)
- Source: demos/verilog-out/boom-BoomConfig.sv (11.4MB, 389 modules + behavioral SRAMs inline)
- Runtime: EICG_wrapper.v + SimDTM.v (DPI stub) + AsyncResetReg.v + plusarg_reader.v
- $stop/$fatal suppressed (sed → $display) for empty-input measurement
- Verilator: --cc -O3 -CFLAGS "-O3" --no-timing --no-assert
- Result: 61,640 cycles/s (~2% vs scala FIRRTL — cross-validated)

## fir2pyc-side build
- Input: /tmp/boom_trim.fir (BoomTrimHarness.stripped.fir)
- MLIR: 1.3M lines, pycc --emit=cpp --no-state-opt --logic-depth 1024
- C++: 191MB TU, g++ -O3 (9:39 compile, 10.48GB RSS)
