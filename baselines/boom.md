# BOOM Performance Baseline

Date: 2026-11-13
Machine: Intel Xeon Gold 6530, 32 cores, 128GB RAM
Compiler: g++ 11.5.0 / Verilator 5.050

## Results (-O3, empty-cycle methodology)

| Path | cycles/s | Notes |
|---|---|---|
| fir2pyc → pycc C++ | **226,163** | BoomTrimHarness (571 modules, 58,012 regs) |
| Chisel (firtool) → Verilog → Verilator | **61,640** | Full BoomConfig (849 modules; CIRCT firtool-1.75.0 output) |

**Note**: The fir2pyc path uses a TRIMMED BOOM harness (BoomTrimHarness, smaller than full BoomConfig).
The Chisel path uses the FULL BOOM design from firtool. These are DIFFERENT design sizes — the
3.7× "advantage" of fir2pyc C++ is partly explained by the smaller design.

## Chisel-side build
- Source: demos/verilog-out/boom-BoomConfig.sv (11.4MB, 389 modules + behavioral SRAMs inline)
- Runtime: EICG_wrapper.v + SimDTM.v (DPI stub) + AsyncResetReg.v + plusarg_reader.v
- $stop/$fatal suppressed (sed → $display) for empty-input measurement
- Verilator: --cc -O3 -CFLAGS "-O3" --no-timing --no-assert

## fir2pyc-side build
- Input: /tmp/boom_trim.fir (BoomTrimHarness.stripped.fir)
- MLIR: 1.3M lines, pycc --emit=cpp --no-state-opt --logic-depth 1024
- C++: 191MB TU, g++ -O3 (9:39 compile, 10.48GB RSS)
