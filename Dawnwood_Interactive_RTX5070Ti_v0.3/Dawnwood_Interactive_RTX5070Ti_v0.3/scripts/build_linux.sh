#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release '-DCMAKE_CUDA_ARCHITECTURES=120-real;120-virtual'
cmake --build build --parallel
ctest --test-dir build --output-on-failure -LE gpu
printf '%s\n' 'Built build/dawnwood. Run --self-test next.'
