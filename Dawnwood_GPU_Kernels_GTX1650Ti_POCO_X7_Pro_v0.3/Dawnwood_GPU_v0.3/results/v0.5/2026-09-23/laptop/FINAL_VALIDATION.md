# Final GTX 1650 Ti validation — 23 September 2026

DWI-N1-0.5 uses the final split/monolithic runtime, portable arithmetic and integer LUT textures. Exact executable SHA-256: `f208a48e4cd6c4cad9403736cbbba398c8d283649c1a025418521c3d9de1bb10`. All seven compiled SPIR-V payloads were found byte-for-byte inside the measured executable. Frozen artifacts and hashes: `final_artifacts/identity.json`. This report supersedes the pre-compaction performance summary without deleting earlier evidence.

## Correctness

- Existing CPU fixtures: 30/30 pass; existing Python fixtures: 17/17 pass.
- All 29 active operator body changes affect numerical state; checkpoint replay passes.
- GTX split evolution: 257 states × 1,024 epochs, and 65,537 states × 4 epochs across the chunk boundary. Every state/operator word checked at every epoch; zero bitwise mismatches and zero absolute/scaled error.
- Final GTX monolithic evolution: 257 × 1,024 likewise bitwise exact at every epoch; the earlier 257 × 64 check also passed.
- All four comparisons enabled Vulkan core/synchronization validation: zero errors and warnings.
- Full 4,096 × 64 checkpoints are byte-identical across the pre-compaction CPU, compact CPU, final CPU, final monolithic GPU and final split GPU. Final CPU 257 × 1,024 also retains the pre-compaction checkpoint exactly. See `final_checkpoint_comparison.json`.

## Matched workload performance

4,096 complete states × 64 epochs; batch 8; three fresh processes per backend; validation disabled. Desktop CPU: Intel Core i7-1165G7, four cores/eight logical processors; the CPU reference is not advertised as an optimized parallel baseline. GPU: NVIDIA GeForce GTX 1650 Ti with Max-Q Design, driver 581.80.

| Metric | CPU reference | GTX monolithic |
|---|---:|---:|
| Median evolution time | 8.197473 s wall | 0.157168 s device |
| Median time per epoch | 128.086 ms | 2.456 ms |
| State updates per second | 31,979 | 1,667,926 |
| Median whole process | 8.218 s | 0.859 s |

GPU sample times: 199.791, 157.168 and 155.614 ms. All six CPU/GPU final digests agree. Device timestamps exclude setup, transfer, readback, digest calculation and host gaps; whole-process time includes them. The CPU-wall/GPU-device ratio is 52.16×; the whole-process ratio is 9.57×. These are distinct scopes and a normal desktop observation, with uncontrolled clock/background variation.

A subsequent interleaved comparison after capacity warmed the GPU measured monolithic median 155.282 ms versus split 161.961 ms for the same workload. Split was slower in two of three pairs and 4.3% slower at the median. Both process medians were 0.750 s and all outputs agreed. This supplies no measured reason to switch the GTX default. See `final_schedule_comparison.json`.

## Completed population capacity

**12,244,544 complete 128-byte states**, each advanced two epochs with full readback, health checking and digests. Payload: 1,494.70 MiB; two GPU state copies: 2,989.39 MiB. GPU time: **14.089905 s**, or **1,738,059 state updates/s**. Whole process: **36.485 s**. The 374 compute submissions peaked at 38.132 ms each.

The run reached 95% of the current reported free GPU budget minus a 128 MiB reserve; the GPU heap policy was the final limiter. This is a completed policy-boundary measurement, not an allocation-failure maximum. The large population was not CPU-compared and two epochs do not establish long-horizon stability. Full detail: `capacity_final95/summary.json`.

## Honest limits

The final small-workload and capacity timings are slower than the measured pre-compaction artifact. Correctness and real-phone portability improved; speed did not improve in these GTX observations. Earlier 24.817M and 2.830M updates/s measurements belong to other arithmetic/shader artifacts and must not be used as current performance. The memory payload model now includes integer-image row padding, bounded 16 MiB staging and optional split scratch (96 bytes per chunk state, at most 6 MiB); actual Vulkan allocation reports remain authoritative because padding and driver memory are additional.

These results validate the declared recurrence and measured hardware runs. They do not prove broad physical, universal-computation, permanent-cache or billion-state claims.

Machine-readable evidence: `final_summary.json`, `final_benchmark_summary.json`, `final_schedule_comparison.json`, and their referenced raw command/stdout/stderr files.
