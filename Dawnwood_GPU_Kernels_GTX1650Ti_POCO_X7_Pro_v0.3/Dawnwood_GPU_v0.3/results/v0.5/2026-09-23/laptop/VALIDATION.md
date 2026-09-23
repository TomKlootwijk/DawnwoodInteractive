# GTX 1650 Ti validation — 23 September 2026

This evidence measures DWI-N1-0.5 corrected arithmetic before the subsequent phone compiler compaction experiment. The exact measured binary and SPIR-V files are retained in `pre_compaction_artifacts/`. SHA-256 of executable: `20b944a181d52e105150196b1f7e2a4f309b79cc478ebd9185f161e9686085e0`.

- Existing CPU fixtures: 30/30 pass.
- CPU/Vulkan comparison, every epoch/all state and operator words: 257 states × 1,024 epochs and 65,537 states × 4 epochs both bitwise equal. No tolerance change.
- Both comparisons enabled the Vulkan validation layer and synchronization checking: 0 errors, 0 warnings.
- Actual device: NVIDIA GeForce GTX 1650 Ti with Max-Q Design; driver 581.80.

## Matched workload timing

4,096 states × 64 epochs, batch 8, three fresh processes, validation disabled for performance. All six final full-state/operator digests agree.

| Metric | Desktop CPU | GTX Vulkan |
|---|---:|---:|
| Median evolution time | 6.467205 s wall | 0.096324 s device |
| Median per epoch | 101.050 ms | 1.505 ms |
| State updates per second | 40,534 | 2,721,495 |
| Median whole process | 6.500 s | 0.688 s |

GPU device-time samples were 0.153941, 0.096324 and 0.090846 seconds; the variation remains visible in `benchmark_summary.json`. Device timestamps exclude setup, upload, readback, digest calculation and gaps between host submissions. CPU evolution wall / GPU device time is 67.14× for this workload; median whole-process speed ratio is 9.45×. These are different scopes.

## Actual population capacity

12,256,960 complete 128-byte states each advanced two epochs, followed by complete readback, health inspection and digest calculation. Single payload: 1,496.21 MiB; two GPU state copies: 2,992.42 MiB. Device time: 8.661624 s, or 2,830,176 state updates/s. Whole process: 37.266 s. Largest compute submission: 24.454 ms.

The run reached 95% of the reported free device budget minus a 128 MiB reserve. This is a measured current-policy capacity, not the absolute hardware limit. No allocation failure occurred. Capacity candidates overlapped an Android build; the final candidate began after it and was limited by the GPU policy rather than host memory. The full population was not CPU-compared, and two epochs do not establish long-horizon stability.

The earlier 24.817M state-updates/s capacity number used the earlier arithmetic candidate. It is not the performance of this corrected build.

Full evidence and exact command exit codes are in `summary.json`, `benchmark_summary.json`, and `capacity95/summary.json`, with their referenced raw outputs.
