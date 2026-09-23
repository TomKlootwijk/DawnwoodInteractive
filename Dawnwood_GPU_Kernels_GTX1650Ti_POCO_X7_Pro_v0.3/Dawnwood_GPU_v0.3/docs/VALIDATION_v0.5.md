# Dawnwood v0.5.0: what works, what fails and what is justified

**Measured revision: 23 September 2026. Numerical validation passes on both physical targets for the listed workloads.** The current GTX and POCO CPU/GPU comparisons have zero bitwise differences at unchanged tolerances. Benchmark and complete-population capacity measurements are recorded for the final artifacts. Initial Mali pipeline failures were resolved by staged evolution; the failed candidates and superseded timings remain identified and retained. Full source-architecture and physical/universality claims are still outside the established result.

The current numerical profile is `DWI-N1-0.5`. The source discussion and unified v0.2 formalization supply the proposal; `FORMALIZATION_v0.5.md` specifies the executable bindings. This assessment separates implementation, measured behavior, missing architecture and unproved claims.

## Current measurements at a glance

| Measurement | GTX 1650 Ti laptop | POCO X7 Pro / Mali-G720 MC7 |
|---|---:|---:|
| 4,096 states × 64 epochs: median GPU seconds | 0.157167648 | 0.1693103924 |
| Mean ms per whole-population epoch | 2.4557445 | 2.6454749 |
| Million state updates/s at that workload | 1.667926 | 1.548304 |
| Largest completed population, two epochs each | 12,244,544 | 14,569,792 |
| GPU state ping-pong payload, MiB | 2,989.39 | 3,557.08 |
| GPU seconds for those two capacity epochs | 14.0899049 | 11.91558916 |
| Million state updates/s at that capacity | 1.738059 | 2.445501 |

Matched-workload timings use three fresh processes. GTX uses monolithic evolution in a Windows Release executable; POCO uses eight-stage evolution in the Android debug native build. They share the numerical profile, while host-native initialization can differ across platforms. Device timestamps exclude setup/readback/host gaps. Capacity counts every completed 128-byte record once despite two GPU copies, and neither population is an absolute hardware maximum or a full-capacity CPU/GPU comparison.

## Quick claim scan

| Claim or requirement | Status | Evidence or boundary |
|---|---|---|
| Connected double pinion, Hadamard phase action, log-polar state, six primitive fields, double fourth-stage Y-up, inverse T and history | Implemented and checked for the declared bindings | Existing 30 CPU fixtures, 29 active-operator state-sensitivity checks and per-epoch GTX comparisons |
| Operators change and affect later numerical state | Working in measured GTX runs | GPU mutation changes scalar bodies, parameters and positions; body coverage inspects state-only digests |
| All algorithms are geometrically defined by the mutable LUT | **Not implemented in full** | RK4, Hadamard matrix, primitive formulas, topology/wrapping, interpreter and schedule remain native algorithms |
| The tree or state population grows itself | **Not implemented** | Population, catalogue and route depth are configured; child addressing is fixed |
| One-bit controls with full-precision field parameters | Implemented | Flag bit 0 is active orientation control, full 32-bit flags are retained, twelve FP32 parameters remain full width |
| One-bit distances or one-bit complete operators | **Not the agreed representation** | Each operator remains 64 bytes; the nine-opcode vocabulary uses four bits per instruction |
| A real texture LUT | Implemented and exercised on GTX | Two `RGBA32_UINT` sampled/storage images, four integer texels/operator, exact point reads |
| All tested LUT words survive transfer | Measured pass | Multirow/high-flag/signed-zero roundtrip; a 262,145-operator roundtrip also crosses the 16 MiB staging boundary |
| Core operator data is explicitly reused on chip | Implemented | 1,984 bytes of workgroup shared storage in evolution and 128 bytes in mutation |
| Permanent cache residence, optimal occupancy or all-zero bus traffic | **Not established** | No epoch copy commands is narrower than a hardware traffic/cache measurement |
| Corrected GTX CPU/GPU agreement | Measured pass for listed workloads | Zero bitwise differences at every compared epoch, including 257 states × 4,096 epochs |
| Corrected phone CPU/GPU agreement | All recorded broader workloads pass | 128 × 16, 257 × 1,024, 4,096 × 256 and 65,537 × four states/epochs are bitwise equal within each local CPU/GPU pair |
| Same CLI seed/configuration gives bitwise-identical state on Windows and Android | **Not guaranteed** | Initialization still uses host-native math; local verification compares CPU/GPU from the same local snapshot |
| Near-capacity full-state populations | Measured on both current artifacts | GTX 12,244,544 and POCO 14,569,792 records each complete two epochs under their recorded memory policies; not absolute hardware maxima |
| Smooth Klein tangent dynamics | **Not established** | Discrete position/orientation wrapping works; asymmetric transported frames remain unresolved |
| Fourth-order convergence of the modified RK4 rule | **Not established** | The extra fourth-stage displacement changes the rule; no convergence result is inferred from its name |
| Inverse T automatically removes noise | **Generic assertion contradicted** | Existing numerical counterexample retains added channel noise after inversion |
| Every transformed/blended field is an exact metric SDF | **Generic assertion contradicted** | Scaling counterexample; apex field is unsigned |
| Quantum hardware behavior, a new double-slit law or universality | **Not established** | Numerical recurrence and classical interference examples do not supply experimental evidence or an encoding/simulation proof |
| Billions of complete states from pointer removal or BC5 | **Not justified for this implementation** | A state is 128 bytes; two device copies cost 256 bytes/state before snapshots/overhead; BC5 is lossy and downstream |

## Corrected GTX evidence from 16 September

Physical device: **NVIDIA GeForce GTX 1650 Ti with Max-Q Design**, vendor 4318, device 8085. These are actual Vulkan runs, not a software ICD. Each comparison checks all state and operator words after every epoch at the unchanged tolerance `1e-5 + 2e-5*max(abs(cpu),abs(gpu))`; integer words are exact. The separate bitwise counter is stronger than tolerance acceptance.

| States | Operators | Epochs checked | Result | Raw report under `results/v0.5/` |
|---:|---:|---:|---|---|
| 257 | 31 | 4,096 | Zero bitwise differences | `verify_final_257_4096.stdout` |
| 4,096 | 31 | 256 | Zero bitwise differences | `verify_final_4096_256.stdout` |
| 65,537 | 31 | 4 | Zero bitwise differences across a dispatch-partition boundary | `verify_final_65537_4.stdout` |
| 65 | 511 | 64 | Zero bitwise differences with a larger, multirow LUT and route depth 8 | `verify_final_65_511_64.stdout` |

All four runs have core/synchronization validation enabled and report zero errors and warnings. There are no nonfinite values or invalid snapshots in these comparisons. This establishes those measured trajectories, not all possible inputs, every GPU or unlimited time horizons. The subsequent setup-order adjustment builds pipelines before large data allocations; fresh measurements identify that executable separately.

`results/v0.5/claims_corrected/summary.json` records 17 existing Python checks, 30 existing CPU fixtures, exact CPU checkpoint replay and numerical-state sensitivity for all 29 active operator records. Bayer and BC5 are checked downstream. These checks passed; no new test sources were added. A suite PASS includes deliberate counterexamples and must not be read as approval of every source claim.

`manual_edge_checks_v05.json` records byte-identical 257-state checkpoints after 17 epochs with requested batch sizes 17 and 1. Actual submission counts were 3 and 17; the runtime caps small-population batches at eight epochs. It also records an exact 262,145-operator LUT roundtrip with a 1,024 × 1,025 image and 16 MiB staging. `lut_roundtrip_identity.json` separately covers high flag bits and signed zero. These checks establish the exercised transfer/batching behavior, not cache residence.

The arithmetic diagnostics retain zero sampled division/root bit mismatches: 4,961,170 finite divisions, 4,980,524 finite nonnegative roots, all 16,777,216 normalized inputs in [1,4) for square root, 2,496,400 division boundary cases and 1,580 root edge/special cases. Sine/cosine/exp remain explicit FP32 approximations with documented sampled errors. `PORTABLE_MATH_v0.5.md` contains the algorithm and limits; these observations do not replace actual phone execution.

## Phone attempt on 23 September

ADB identifies **POCO X7 Pro**, model **2412DPC0AG**, device **rodin**, serial **XOVSTSHYNREMZ5D6**. The initial probe reports **11,861,921,792 bytes** of Android system RAM and **3,998,412,800 bytes** available before the attempt. Those are observations at launch, not dedicated GPU capacity. Android thermal status was 0 and battery temperature 34.4 °C.

The initial `probe` and 128-state/16-epoch `verify` both return `vkCreateComputePipelines evolve on Mali-G720 MC7 (VkResult -3)`. The existing CPU fixtures pass. A later ordinary GPU run terminates its native process; own-process logs and exit information are retained. Those failures precede a valid completed GPU workload and cannot be reported as zero-error numerical comparisons, a throughput of zero or allocation-capacity measurements.

Raw evidence: `results/v0.5/2026-09-23/phone_validation/`, including `device.json`, `probe.json`, `selftest.json`, `verify.json`, launch records and own-PID logs. This failed candidate remains part of the history despite the later staged build's success.

Several compiler-compaction attempts and an authorized background-app cleanup did not make the monolithic phone pipeline compile. The cleanup increased Android `MemAvailable` from 5,374,512 KiB to 5,771,476 KiB, while the compilation failure persisted. The evidence therefore does not support attributing the failure solely to a background video app. Cleanup observations and retained failure candidates are in the dated `phone_memory_cleanup/`, `phone_clean_memory/` and other explicitly named attempt directories.

### Staged evolution now executes

APK SHA-256 **8c86dbcd791a824b1402a5561c3ef3926a8f539900d0dcdf95b1563d89726430** implements prepare, four slopes, combine, geometry and finish as eight dependent evolution dispatches per partition. It retains one mutation per logical epoch and adds at most 6 MiB of scratch. All of these actual Mali-G720 MC7 comparisons have **zero bitwise word differences**, zero absolute/scaled error and no nonfinite/invalid records:

| States | Epochs checked | Evidence below `2026-09-23/` | App wall seconds |
|---:|---:|---|---:|
| 128 | 16 | `phone_split/verify.json` | 6.527 |
| 257 | 1,024 | `phone_extended/verify_257_1024_sep23.json` | 46.684 |
| 4,096 | 256 | `phone_extended/verify_4096_256_sep23.json` | 132.419 |
| 65,537 | 4 | `phone_extended/verify_65537_4_sep23.json` | 32.562 |

Comparison wall time includes CPU work and per-epoch comparison/readback overhead; it is not kernel throughput. The completed repeated benchmark and capacity runs below use ordinary `run` commands and separate timers.

The phone report has **`validation_layer_enabled: false`**. Its zero validation-message counters are not a layer-validation result. Desktop checks of the same staged schedule can inspect synchronization, but do not replace execution on the Mali device.

These are local CPU/GPU comparisons from a common initial snapshot. `initialize()` still uses native host `sqrt/sin/cos/log/fmod` and ordinary division. Windows and Android can therefore create different initial FP32 bits from the same CLI parameters and seed. The observed Windows/Android 4,096-state run digests differ; no cross-device bitwise replay is asserted. An identical imported checkpoint/initial-state payload and an explicit cross-device comparison are required to establish that stronger result.

### Completed phone timing and capacity

`phone_benchmark/summary.json` records three fresh-process **4,096-state × 64-epoch, batch 8** device times: **0.1692938539**, **0.1693103924** and **0.177697162 seconds**. Median time is **2.64547488125 ms per whole-population epoch**, or **1.548304 million state updates/s**. All reports are healthy and all same-device digests agree. Median **app native wall time is 5.818 seconds**, including initialization, pipeline setup, transfers, execution and health/digest work, but excluding ADB launch/report polling. This is a different scope from desktop whole-process wall time. Phone layers are disabled; the debug native build runs under normal USB charging/background conditions. Thermal status is 0 and battery temperature 37 °C for all three samples; this is not a controlled peak-performance or thermal study.

`phone_capacity/summary.json` completes **14,569,792 full records × two epochs**, with full readback, health and digest. One state payload is **1,778.5390625 MiB** and the two GPU copies use **3,557.078125 MiB** of shared RAM. Runtime resource allocations total **3,753,000,960 bytes**, including 16 MiB staging, 6 MiB scratch and image/alignment overhead; host snapshots and unreported driver/compiler memory are additional. GPU device time is **11.91558916 seconds**, throughput **2.445501 million state updates/s**, ADB launch-to-report wall time **77.546 seconds**, and maximum submission **41.1456 ms**. Digest is `9ae99cb7c910cae5`; all records are finite/chart-valid.

Phone growth is limited by **85% of current available Android physical memory**, accounting for 384 bytes/state at peak (two GPU copies plus a host snapshot), staging/scratch and an effective reserve of **226,492,416 bytes**. That reserve is the larger of 128 MiB and Android's low-memory threshold. Mali reports no Vulkan memory-budget extension, so its heap size is not free memory. The final refreshed policy target falls below the highest already completed population as availability changes; the runner stops at the current policy boundary with **no allocation or health failure**. It does not establish an absolute maximum or long-horizon stability of that full population. The last capacity report has thermal status 0, battery 36.6 °C and low-memory false; its after-run memory observation is not a measurement of peak process usage.

## Fresh corrected GTX build on 23 September

### Current accepted shader architecture

The current desktop executable SHA-256 is **f208a48e4cd6c4cad9403736cbbba398c8d283649c1a025418521c3d9de1bb10**, with the complete payloads of all seven identified shader modules verified inside it. Its forced staged path passes **257 states × 1,024 epochs** and **65,537 states × four epochs**; its default monolithic path passes **257 states × 64 epochs** and **257 × 1,024**, all with zero bitwise differences and core/synchronization validation enabled, zero errors/warnings. `final_mono_verify_257_1024.stdout` records the longer default-path check. `claims_final_split/summary.json` records the existing fixture, body-sensitivity and checkpoint checks passing.

`final_checkpoint_comparison.json` establishes byte-identical full checkpoints for **4,096 states × 64 epochs** across pre-compaction CPU, compact CPU, current CPU, current monolithic GPU and current staged GPU. The 257-state/1,024-epoch CPU checkpoints also match across the recorded refactors. This directly checks preserved sampled behavior while changing interpreter structure and dispatch organization. It does not prove all possible inputs or all GPUs. Current benchmark evidence is `final_benchmark_summary.json`; earlier `benchmark_summary.json` describes the preceding artifact.

The **current capacity result** in `capacity_final95/summary.json` completes **12,244,544 records × two epochs**, full readback and health/digest checks. One state payload is **1,494.70 MiB** and the two GPU copies total **2,989.39 MiB**. Device time is **14.0899049 seconds**, or **1.738059 million state updates/s**; whole-process time is **36.485 seconds**, and maximum individual submission is **38.1315 ms**. Reported runtime resource allocation is **3,151,412,224 bytes**, including padded LUT images and 16 MiB staging, excluding unreported driver/compiler allocations and host snapshots. No scratch is allocated on the default monolithic GTX path.

The final run reaches the **95%-of-reported-free-budget minus 128 MiB reserve** policy boundary without allocation/health failure. The full capacity population is not CPU-compared, two epochs do not prove long-horizon stability, and layers are disabled for this timing. The result is not an absolute hardware maximum. `final_summary.json` and `FINAL_VALIDATION.md` consolidate the current desktop evidence.

### Preserved pre-compaction evidence

`results/v0.5/2026-09-23/laptop/summary.json` identifies executable SHA-256 **20b944a181d52e105150196b1f7e2a4f309b79cc478ebd9185f161e9686085e0**, retained with its shader files in `laptop/pre_compaction_artifacts/`. This evidence precedes the subsequent phone compiler-compaction experiment. A later accepted build must be checked and attributed separately even if the mathematical equations are intended to remain unchanged.

On this executable, 30 CPU fixtures pass and GTX comparisons for **257 states × 1,024 epochs** and **65,537 states × four epochs** have zero bitwise differences, zero absolute/scaled error and no invalid/nonfinite records. Core/synchronization validation is enabled with zero warnings and errors. The device uses driver 581.80. The CPU is an Intel Core i7-1165G7 with four cores/eight logical processors; no claim that the CPU path uses all cores follows from that identity.

The fresh complete-population capacity run advances **12,256,960 full records for two epochs** and completes full readback, digest and health checks. One state payload is **1,496.21 MiB**; its two GPU copies are **2,992.42 MiB**. GPU device time is **8.661623776 seconds**, giving **2.830176 million state updates/s** and **4,330.812 ms per whole-population epoch**. Whole-process time is **37.266 seconds** and the largest submission is **24.454 ms**. The runtime splits the full population into bounded evolution submissions; all records still complete both epochs.

The capacity runner stops at **95% of reported free device budget minus 128 MiB**, without an allocation failure. This is the highest population completed under that changing policy, not an absolute maximum. Smaller growth candidates overlap one Android build; the final capacity candidate starts after it and is GPU-policy limited rather than host-memory limited. The full capacity population is not CPU-compared, and two epochs do not prove long-horizon stability. The exact evidence is `laptop/capacity95/summary.json`.

## Performance: what the numbers mean

One **state update** is one complete recurrence for one 128-byte record. A population of N records completing E epochs performs N × E state updates. A kernel rate is that count divided by the recorded GPU execution seconds. It is not a FLOPS measurement or a count of arbitrary logical operations. Mean milliseconds/epoch describe updating the entire population once.

Kernel device timestamps exclude initialization, pipeline creation and full readback. Whole-process time includes those costs. Setup/upload, advance wall time and readback timing are also reported by current builds. Health means finite and structurally valid output; it is not a numerical-equivalence verdict or a guarantee of negligible norm drift. Memory size does not measure bandwidth, arithmetic occupancy or cache hits.

The **current executable f208a48e…** uses **4,096 states × 64 epochs, batch 8**, three fresh processes/backend and no validation layer for timing. GTX uses its default monolithic path. All six final state/LUT digests agree. `laptop/final_benchmark_summary.json` records these medians:

| Metric | Desktop CPU | GTX Vulkan |
|---|---:|---:|
| Evolution time | 8.1974733 s wall | 0.157167648 s device |
| Mean per whole-population epoch | 128.085520 ms | 2.4557445 ms |
| State updates/s | 31,979 | 1,667,926 |
| Whole process | 8.218 s | 0.859 s |

GPU device-time samples are 0.199790944, 0.157167648 and 0.1556144 seconds; normal desktop/background and clock variation are uncontrolled and retained. The CPU-wall/GPU-device median ratio is 52.16, while the whole-process ratio is 9.57. Neither is a universal speedup. The current GPU median is slower than the preceding 0.09632352-second artifact. The demonstrated gains are numerical agreement and successful phone execution, **not a demonstrated speed improvement**.

A separate paired follow-up after warming the GTX compares its two schedules at 4,096 states × 64 epochs. Three-pair medians are **155.282368 ms monolithic** and **161.960992 ms staged**, making staged execution **4.3% slower** in that measurement; every final digest agrees, and median whole-process time is 0.750 seconds for both. `final_schedule_comparison.json` preserves the pairs and ordinary-desktop conditions. This supports retaining the monolithic GTX default while using the staged path to obtain phone compiler compatibility.

For attribution, the **preceding executable 20b944a1…** used the same workload with these medians in `laptop/benchmark_summary.json`:

| Metric | Desktop CPU | GTX Vulkan |
|---|---:|---:|
| Evolution time | 6.4672045 s wall | 0.09632352 s device |
| Mean per whole-population epoch | 101.050070 ms | 1.505055 ms |
| State updates/s | 40,534 | 2,721,495 |
| Whole process | 6.500 s | 0.688 s |

Those older GPU samples are 0.153940768, 0.09632352 and 0.090845888 seconds; normal desktop and first-sample/clock variation remain visible. The numbers remain evidence for that executable only and are not relabeled as current-artifact performance.

For historical context, the corrected 16 September count-scaling benchmark uses three samples per row, 16 epochs, 31 operators, no validation layer. `results/v0.5/claims_corrected/benchmark_scaling.json` records these medians. CPU elapsed time and Vulkan device time have different timing scopes.

| States | CPU median seconds | GTX device median seconds | GTX mean ms/epoch | GTX million state updates/s |
|---:|---:|---:|---:|---:|
| 256 | 0.1075365 | 0.022644192 | 1.415262 | 0.180885 |
| 1,024 | 0.4620861 | 0.023300384 | 1.456274 | 0.703164 |
| 4,096 | 1.6145976 | 0.037177152 | 2.323572 | 1.762803 |

The current large-population rate of **1.738 million updates/s**, and the preceding corrected candidate's **2.830 million**, are materially lower than the initial trig-only candidate's **24.817 million**. Populations and launch conditions differ, so this is not a controlled fixed-population speed-ratio experiment. It does establish that the older headline rate does not describe the current build. Numerical agreement and phone portability have a real measured performance cost here.

## Preserved failed and superseded candidates

| Candidate | Recorded result | Interpretation |
|---|---|---|
| v0.4 GTX | First mismatch at epoch 96 for 257 states | Historical numerical failure |
| v0.4 POCO | First mismatch at epoch 1 for 128 states | Historical numerical failure |
| First v0.5 sin/cos/exp-only candidate | First mismatch at epoch 305, `state[205].ai`; CPU 0.0916269422, GPU 0.0916389078 | Division/root correction was still needed; 304 passing preceding epochs do not make this a pass |
| First v0.5 candidate capacity | 12,490,752 states × 2 epochs, healthy full readback; 3,049.5 MiB state ping-pong payload | A completed population for that earlier arithmetic and policy only |
| First 23 September v0.5 phone APK | Evolution-pipeline creation failure, followed by a separate run's native-process termination | Actual unsuccessful device attempt, not an untested phone or a numerical tolerance failure |

The earlier capacity run used 1.006620256 seconds of Vulkan device time (24.817 million state updates/s), 22.969 seconds for the whole process, and a maximum submission of 3.05962 ms. It reached its 95%-of-current-budget minus 128 MiB policy boundary without an allocation failure. Validation layers were disabled. `results/v0.5/capacity_candidate1/summary.json` and its identity record preserve the candidate. It is **not** an absolute hardware maximum, the speed of the later corrected arithmetic or an independent accuracy check.

## What remains beyond this revision

Numerical validation and the recorded device benchmark/capacity work are complete for these artifacts. Further work is substantive: specify and implement which native algorithms become editable substrate programs; address the host-native initialization boundary before claiming cross-device replay from CLI seeds; establish smooth transported-frame dynamics and convergence properties if those are required; and provide separate experiments/proofs for physical, universality, cache or optimization claims. Current successful trajectories do not supply those missing results.
