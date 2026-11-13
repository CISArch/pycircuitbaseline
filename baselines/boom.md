# BOOM Trim Harness Performance Baseline

Date: 2026-11-13
Design: BoomTrimHarness.stripped.fir (FIRRTL 3.3.0, 571 modules, 344k lines)

## Results (-O3, empty-cycle methodology)

| Path | cycles/s | Notes |
|---|---|---|
| fir2pyc → pycc C++ | 226,163 | Full design (58,012 regs) |
| Chisel-side Verilator | pending | Needs FIRRTL compilation of BOOM .fir |

## Notes
- BOOM .fir is FIRRTL 3.3.0 (modern format), needs different FIRRTL compiler than RocketChip
- Chisel-side baseline will use boom-template from essent demos
