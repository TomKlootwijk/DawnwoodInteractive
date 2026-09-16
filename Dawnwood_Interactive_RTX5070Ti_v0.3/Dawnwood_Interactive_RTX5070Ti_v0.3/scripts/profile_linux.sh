#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p work
# This is deliberately a fixed small workload, not a VRAM-capacity measurement.
compute-sanitizer --tool memcheck --error-exitcode 99 ./build/dawnwood --self-test
compute-sanitizer --tool racecheck --error-exitcode 99 ./build/dawnwood --pages 2 --page-side 64 --blocks-per-step 31 --steps 8 --report work/racecheck.json
compute-sanitizer --tool synccheck --error-exitcode 99 ./build/dawnwood --pages 2 --page-side 64 --blocks-per-step 31 --steps 8 --report work/synccheck.json
ncu --set full --kernel-name regex:evolve_window --launch-count 1 -o work/dawnwood_ncu ./build/dawnwood --pages 4 --steps 2 --no-graph --report work/profile.json
