# pycircuitbaseline

BOOM / RocketChip 在 pyCircuit 编译器管线上的性能基线，与 Chisel 直出 Verilog→Verilator 对比。

## 结构

```
pycircuitbaseline/
├── tools/           # 自动化脚本（.fir 手术、基线运行）
├── mods/            # 设计适配补丁（SimDTM 替换等）
├── baselines/       # 性能数据（markdown）
├── designs/         # fork 的设计工程（rocket-chip / boom-template）
└── README.md
```

## 当前基线数据（2026-11-13, -O3, Rocket DefaultConfig）

| 路径 | cycles/s | 口径 |
|---|---|---|
| Chisel FIRRTL → Verilog → Verilator | **119,644** | 全设计活体（CPU 执行 boot ROM） |
| fir2pyc → pycc C++ | **52,272** | 全设计（29,047 regs 全求值，空激励） |
| fir2pyc → pycc Verilog → Verilator | 待修 | pycc 管线 SimAXIMem DCE 问题 |
| ESSENT C++（参照） | 2,039 D/s | 全系统 dhrystone |

BOOM trim 全顶层 C++ -O3: 226,163 cycles/s。

## 已知 pycc 管线问题

1. **SimAXIMem 实例被 EliminateDeadInstances 清除**（Verilog 路径独有）：pycc 管线从顶层输出反向追踪时，错误地将存储器子系统判为死代码。C++ 后端不做此消除（每周期全树求值）。
2. SimDTM extmodule 常量 stub：已通过 .fir 手术解决（`tools/fir_surgery.py`）。

## 用法

```bash
# RocketChip 基线
python3 tools/fir_surgery.py <rocket.fir> <output.fir>   # SimDTM → 顶层端口
python3 -m src.fir2pyc.cli emit <output.fir> --top TestHarness -o model.mlir
pycc model.mlir --emit=cpp --no-state-opt --logic-depth 1024 -o gen.cpp
g++ -O3 -std=c++20 -ftemplate-depth=4096 -I<pyc-install>/include main.cpp -o perf
./perf 100000
```
