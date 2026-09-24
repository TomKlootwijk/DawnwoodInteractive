# RTX 5070 Ti Laptop campaign — work in progress

Target: MSI Vector 16 HX AI A2XWHG, NVIDIA GeForce RTX 5070 Ti Laptop GPU,
12,227 MiB reported framebuffer, driver 591.59, 16,558,415,872 bytes system RAM.
The numerical definition remains DWI-N1-0.5. No clocks, power limits or cooling
settings have been changed. The user's request includes optimization, a laptop
edition and saturation testing.

Completed evidence:

- Existing 17 Python checks, 30 CPU fixtures, all active operator sensitivity
  checks and checkpoint replay pass (`claims/`).
- Original executable: 257 states × 1,024 epochs has zero bitwise CPU/GPU
  differences with Khronos core and synchronization validation enabled.
- The first baseline load reaches 98% device utilization, 119.43 W and 58°C.
- Runtime workgroup specialization and bounded configurable dispatch sizes
  compile. Workgroups 32/64/128/256 pass existing `verify` at 257 × 64 with
  layers enabled. All 32 scheduling sweep outputs have identical state/LUT
  digests (`tuning_sweep.json`). These are exploratory timings, not a final
  paired speedup measurement.

Further completed evidence:

- Paired 1,048,576-state × 64-epoch comparison: median device time falls from
  6.396526464 s to 5.786616128 s (10.54% higher throughput), with matching full
  output digests. RTX defaults are now 32 lanes and 1,048,576 states/dispatch.
- Two physical pages preserve one logical population. Bounded initialization
  and complete readback use an 8 MiB host-state chunk. Normal, streamed and
  preceding-build checkpoints for 8,190 states × 16 epochs are byte-identical.
- Final runtime 0.5.1-rtx1 passes the existing suite and bitwise per-epoch
  comparisons at 257 × 4,096, 4,096 × 256 and 1,048,577 × 2; forced page splits
  and both schedules also pass. Core and explicitly enabled synchronization
  validation report zero errors and warnings.
- The final capacity campaign completes 43,609,664 states × four epochs with
  complete readback. A second page layout gives the same whole-population
  digest with core/synchronization validation enabled. This reaches the current
  98%-budget-minus-32-MiB policy, not an absolute hardware maximum.
- The first final-suite attempt exposed the old Python memory-accounting
  helper's 65,536-dispatch cap. Its bound now matches the configurable runtime;
  `final_claims_r2/` passes. The failed attempt remains preserved.

Remaining: finish the running 43,609,664-state × 177-epoch sustained campaign,
inspect its full readback, package the exact binary, and publish the final
report, provenance, manifests and reproduction commands. The sustained process
was launched by the ignored `tmp/rtx-build/sustain.py`; no result is assumed
while it is running.

Build dependencies (workspace-local, ignored under `tmp/`):

- [LLVM-MinGW 20260922](https://github.com/mstorsjo/llvm-mingw/releases/tag/20260922),
  UCRT x86-64 archive SHA-256
  `e3ad77d117a4bea19a7a3b333341824d79a5a371004a10e25b8504e7b3047666`.
- [LunarG Vulkan SDK 1.4.357.0](https://vulkan.lunarg.com/sdk/home), Windows
  installer SHA-256
  `81f474711e9042f4cd22b31b2f7a8870db2e428b21586fb43dd80150be97310d`,
  Authenticode signature valid for LunarG, Inc. Extracted with `copy_only=1`.
  [LunarG documents copy-only mode](https://vulkan.lunarg.com/doc/view/1.3.296.0/windows/release_notes.html).

Command receipts preserve executable hashes, environment, exit codes and wall
times. `.stdout`/`.stderr` remain raw. Device timestamps exclude setup/readback;
NVIDIA telemetry is device-wide and includes setup/readback. Failed attempts
must remain recorded. No new test source is introduced.
