# Dawnwood v0.5.0 implementation and validation record

**23 September 2026: implementation and recorded device-validation work completed for v0.5.0.** `VALIDATION_v0.5.md` is the current human-readable evidence index. Both physical targets pass the stated CPU/GPU workloads with zero bitwise differences at unchanged tolerances, and have completed benchmark/capacity measurements. That scope does not establish the source's full self-defining architecture or stronger physical/universality claims. Identified results do not erase earlier failures.

## Accepted scope

1. Diagnose and correct CPU/GPU disagreement without loosening `atol=1e-5`, `rtol=2e-5`, or exact integer comparisons. Preserve connected operator/state feedback, the six primitive fields, fourth-stage double Y-up, inverse T, history and the discrete Klein carrier.
2. Store packed one-bit operator/control flags and full-precision SDF parameters in an actual LUT texture. The user selected this representation on 16 September 2026. One-bit flags do not encode distance magnitude. The existing nine-instruction vocabulary still requires four bits per opcode.
3. Reuse the compact operator working set in on-chip workgroup memory where supported; distinguish explicit reuse from unmeasured hardware cache occupancy.
4. Measure substantial, near-capacity live state allocations on the actual GTX and POCO. Use current per-heap budget/available system memory, account ping-pong copies, staging, host snapshots and driver overhead, and advance every allocated state. Allocation alone is not a throughput result.
5. Report accessible metrics: how many complete evolving records fit, how long one complete update takes, how many record-updates happen per second, how much memory is occupied, and whether the same calculation agrees across backends.
6. Version and formalize changes and retain raw commands, exit status, numerical failures and limitations. No new test sources are authorized; use existing fixtures, comparisons, diagnostic observations and benchmarks.

## Accepted device sequence

The user initially requested GTX first while the phone was absent, then connected the POCO on 23 September and explicitly authorized actual-device testing of both laptop and phone. The target identities and changing memory observations are recorded with each run.

## Completed implementation and evidence

- Actual ping-pong `RGBA32_UINT` LUT images preserve four integer texels per 64-byte operator; full FP32 parameter bits and flag words survive transfer.
- Evolution shares 31 core records in 1,984 bytes; mutation shares two control records in 128 bytes. No permanent-cache claim is made.
- Shared FP32 trigonometric/exponential approximations and integer-corrected division/root rounding preserve the real-function intent at the cost of changing older FP32 trajectories. Sampling/boundary diagnostics are recorded; tolerance is unchanged.
- At most 16 MiB staging, 65,536-state evolution partitions, one mutation per global epoch and one final parity exchange preserve whole-population feedback. Pipelines compile before large data allocations; the initial host snapshot is released before readback allocation.
- Existing 30 CPU fixtures and 17 Python checks pass. All 29 active operator records affect numerical state in the existing sensitivity suite. CPU checkpoint replay passes.
- Corrected 16 September GTX comparisons are bitwise equal at every compared epoch for 257 × 4,096, 4,096 × 256, 65,537 × 4, and 65 states/511 operators × 64. Core/synchronization validation reports zero errors/warnings.
- Exact roundtrips cover high flag bits, signed zero, multirow images and an image payload larger than staging. Requested batch sizes 17 and 1 produce identical checkpoints after 17 epochs.
- The corrected 23 September pre-compaction executable passes 257 × 1,024 and 65,537 × 4 bitwise comparisons with layers enabled. It completes a 12,256,960-state/two-epoch capacity run at 2.830 million state updates/s under the stated memory policy. Its frozen artifacts and raw records are in `results/v0.5/2026-09-23/laptop/`.

## Phone outcome

ADB identifies POCO X7 Pro, model 2412DPC0AG, and the attempted GPU pipeline identifies Mali-G720 MC7. Android reports 11,861,921,792 bytes of system RAM; this is shared RAM, not dedicated VRAM.

The initial 23 September v0.5 APK passes CPU fixtures but fails creation of the GPU evolution pipeline with `VkResult -3`; a later ordinary run terminates the native process. Logs remain in `results/v0.5/2026-09-23/phone_validation/`. Compiler compaction and an authorized app cleanup still fail to compile the monolithic kernel, so app pressure alone does not explain the observation.

The new ARM schedule divides evolution into eight dependent dispatches (prepare, slope × four, combine, geometry, finish), retaining one mutation per whole epoch. It shares helpers with CPU/monolithic execution and adds 96 bytes of scratch per active partition state, at most 6 MiB. Persistent state/operator/config and checkpoint ABI remain unchanged. The staged APK SHA-256 `8c86dbcd791a824b1402a5561c3ef3926a8f539900d0dcdf95b1563d89726430` passes 128 × 16, 257 × 1,024, 4,096 × 256 and 65,537 × four states/epochs with zero bitwise differences. Phone layers are disabled; zero counters are not a layer-validation pass.

Three fresh 4,096-state/64-epoch runs have median 0.1693103924 seconds of device time (1.548304 million state updates/s), healthy output and identical same-device digests. Median app native wall time is 5.818 seconds, including setup/readback but excluding ADB polling. Capacity completes 14,569,792 states × two epochs at 2.445501 million state updates/s, with 77.546 seconds ADB launch-to-report time and 3,557.078125 MiB state ping-pong payload. The runner stops at the current Android physical-memory policy boundary without allocation/health failure, not an absolute hardware maximum. Final evidence is `phone_benchmark/summary.json` and `phone_capacity/summary.json` under the dated results directory.

The current desktop executable SHA-256 `f208a48e4cd6c4cad9403736cbbba398c8d283649c1a025418521c3d9de1bb10` passes staged 257 × 1,024 and 65,537 × four comparisons with zero bitwise differences/layer errors/warnings, plus monolithic 257 × 64 and 257 × 1,024. Complete checkpoints demonstrate sampled equivalence across the refactor and both GPU schedules. Its new 4,096 × 64 median is 0.157167648 seconds device time (1.667926 million state updates/s); this is slower than the earlier 0.09632352-second executable. Gains are demonstrated correctness and phone execution, not a measured speed gain. Current capacity completes 12,244,544 records × two epochs at 1.738059 million state updates/s under the 95%-budget/128 MiB-reserve policy, with full readback/health/digest and no allocation failure. Paired staged execution is 4.3% slower on GTX; the default remains monolithic.

Initialization remains host-native in `src/cpu.cpp`. Local CPU/GPU pairs use the same snapshot, while independently initialized Windows/Android runs need not start with identical FP32 bits. Cross-device bitwise replay from identical CLI parameters/seed is not established.

## Historical results retained

The v0.4 GTX epoch-96 and POCO epoch-1 failures remain in their original reports. The first v0.5 trig-only candidate fails GTX comparison at epoch 305. Its separate 12,490,752-state capacity run achieves 24.817 million state updates/s, but that number measures the older arithmetic and must not be reused for the corrected build. Neither historical capacity is an absolute hardware maximum.

## Scope beyond this numerical revision

Current-artifact GTX and phone verification, benchmarks and capacity runs are complete and recorded separately from older candidates. The improvements establish the measured numerical behavior and actual phone execution. They do not demonstrate a speed gain over the earlier corrected desktop artifact, and they do not eliminate the limitations below.

Separately, define the desired boundary of an editable operator language before implementing the full source architecture. The current LUT changes scalar programs, parameters, controls and positions; native RK4, Hadamard, primitive formulas, Klein wrapping, scheduling and route/tree structure remain fixed. It does not grow its own tree/population. Backend agreement cannot establish that missing architecture, smooth quotient dynamics, modified-RK4 fourth-order convergence, physical quantum behavior, automatic noise removal, one-bit distance storage or universality.
