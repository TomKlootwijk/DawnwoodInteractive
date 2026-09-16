#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec ./build/dawnwood --codec bc5 --fill 0.98 --reserve-mib 256 --steps 0 --report work/rtx5070ti_saturation.json
