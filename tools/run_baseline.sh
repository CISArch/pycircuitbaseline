#!/bin/bash
# Run full baseline: fir2pyc → pycc → C++ → perf
# Usage: ./run_baseline.sh <fir_file> <top_module> [output_dir]
set -e
FIR=$1; TOP=${2:-TestHarness}; OUT=${3:-/tmp/baseline}
PYCC=~/pycircuit-workspace/pyCircuit-dev/.pycircuit_out/toolchain/install/bin/pycc
FIR2PYC=~/pycircuit-workspace/fir2pyc

mkdir -p $OUT
echo "=== Step 1: .fir surgery (SimDTM → top-level ports) ==="
python3 "$(dirname $0)/fir_surgery.py" $FIR $OUT/surgery.fir

echo "=== Step 2: fir2pyc emit ==="
cd $FIR2PYC
python3 -m src.fir2pyc.cli emit $OUT/surgery.fir --top $TOP -o $OUT/model.mlir

echo "=== Step 3: pycc C++ ==="
$PYCC $OUT/model.mlir --emit=cpp --no-state-opt --logic-depth 1024 -o $OUT/gen.cpp

echo "=== Step 4: compile & run ==="
echo "Adapt main.cpp to include $OUT/gen.cpp"
echo "g++ -O3 -std=c++20 -ftemplate-depth=4096 -I<pyc-include> main.cpp -o $OUT/perf"
echo "$OUT/perf 100000"
