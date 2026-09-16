#!/usr/bin/env sh
# Run real-device checks after building the desktop executable.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BIN=${1:-"$ROOT/build/dawnwood"}
OUT=${2:-"$ROOT/results/gtx1650ti_local"}
mkdir -p "$OUT"
"$BIN" selftest > "$OUT/cpu_selftest.json"
"$BIN" probe --device "1650 Ti" > "$OUT/device.json"
"$BIN" verify --device "1650 Ti" --count 128 --steps 16 > "$OUT/cpu_gpu_comparison.json"
"$BIN" run --backend vulkan --device "1650 Ti" --count 4096 --steps 64 --batch 8 \
    --checkpoint "$OUT/working_state.dwk" > "$OUT/numerical_session.json"
printf 'Saved real-device results to %s\n' "$OUT"
