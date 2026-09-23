# Dawnwood v0.5.0 - texture LUT, portable arithmetic and measured capacity

**Measured numerical revision, 23 September 2026.** Current artifacts pass recorded CPU/GPU comparisons on both physical devices at unchanged tolerances, with completed benchmark/capacity measurements. This develops the complete v0.4 formalization from the user-confirmed `Dawnwood_Interactive_Unified_v0.2.pdf`. Earlier PDFs, documents, failures and candidate-specific evidence remain unchanged. This is scoped numerical validation, not certification of the source's physical/universality claims or full architectural realization. `VALIDATION_v0.5.md` gives the quick status and detailed evidence.

## Actual mutable operator texture

| Change | Concrete implementation | Scope of the claim |
|---|---|---|
| Buffer LUT becomes a texture LUT | Two optimal-tiling `VK_FORMAT_R32G32B32A32_UINT` images, with four RGBA texels per 64-byte operator | Real sampled/storage image resources, not a renamed storage buffer |
| Full parameter precision survives packing | Twelve FP32 values are stored as their exact uint32 bit patterns; program, seed, kind and flags remain uint32 words | No interpolation, normalization or quantization; not one-bit geometry |
| Binary controls remain separate from parameters | Orientation uses flag bit 0; the complete 32-bit flag word survives transfer | Individual controls are one-bit; the whole operator is not |
| Finite bytecode remains explicit | Eight four-bit instructions encode the existing nine-opcode vocabulary | One bit cannot distinguish all nine instructions |
| GPU mutation updates the new image | Old image `texelFetch`, new image `imageStore`, compute write/read dependency, new image evolution fetch | No host upload or image-copy command between epochs |
| Common definitions are shared within a workgroup | Evolution shares 31 operators / 1,984 bytes; mutation shares records 5 and 30 / 128 bytes | Explicit shared storage for the workgroup; no permanent hardware-cache guarantee |
| Larger catalogues span image rows | Integer texel indexing wraps rows; records outside the core shared window use texture fetches | Default catalogue and larger route trees preserve full records |

The texture stores descriptors from which geometric fields are evaluated. It does not contain a precomputed spatial grid of signed distances. Mutable transforms and blends still need not be exact metric SDFs; the apex remains unsigned. Conceptual RGBA wavefront roles are distinct from physical RGBA32UI texture components.

## Arithmetic revision

Version 0.4 aligned FP32 constants and disabled unwanted multiply/add contraction, but independent native elementary-function implementations still left numerical discrepancies. The first v0.5 candidate provides shared ordered FP32 sine, cosine and exponential implementations in `include/numeric_math.inc`; `PORTABLE_MATH_v0.5.md` specifies reduction, polynomial evaluation, exceptional inputs and sampled error.

- Trigonometric reduction supports finite FP32 arguments without clipping them to a small artificial domain. Small arguments use split pi/2 constants; larger arguments use integer significand reduction with a 256-bit 2/pi constant. Reduced sine/cosine use degree-13/12 polynomials.
- Exponential uses split ln(2) reduction, a degree-8 polynomial and explicit exponent construction, including overflow and underflow branches. Producing subnormal bits does not prove preservation through every device's later arithmetic.
- Approximation replaces backend-native function choices explicitly. It changes individual FP32 results and therefore old bitwise trajectories. It does not remove fields, normalize amplitudes or change the real-function intent.
- The corrected candidate also replaces final native square-root/division results with integer-corrected round-to-nearest/even values. Native operations supply estimates on normalized inputs; exact high/low uint32 products and midpoint/remainder logic choose the output. Dynamic divisions include both geometry and RK division by six. Subnormal, signed-zero, infinity and NaN behavior is explicit in the arithmetic specification.
- A strict-CPU sample produced zero result-bit differences for 4,961,170 finite divisions with nonzero denominators and 4,980,524 finite nonnegative square-root inputs. The sample is implementation evidence, not an exhaustive proof over all devices.
- Optional SPIR-V `DontInline` annotations retain the six portable functions before offline optimization, reducing repeated expansion without changing the equations. Actual driver behavior and speed remain measurement questions.
- The absolute/relative CPU-GPU rule remains `1e-5 + 2e-5*max(abs(cpu),abs(gpu))`; integer words remain exact. Tolerance was not relaxed.

The ideal Hadamard plus complex-phase transform preserves norm mathematically. Implemented sine/cosine approximations and FP32 roundoff mean exact numerical conservation cannot be asserted; no renormalization hides accumulated error.

## Smaller entry points for the phone compiler

Native Mali pipeline creation still failed after elementary-function/interpreter compaction and an authorized background-app cleanup. The new ARM path divides each bounded evolution partition into eight dependent dispatches using five entry points: prepare, slope called four times, combine, geometry and finish. It uses the same shared helper equations as CPU/monolithic evolution. Mutation remains once per global epoch, every stage reads the same old population and new LUT, and state/LUT exchange remains after complete population evolution.

The new transient `EvolutionScratch` structure is **96 bytes per active partition state**, at most **6 MiB** for a 65,536-state partition. Binding 5 holds device scratch; `Config.reserved0/1` carry transient partition offset/slope stage without changing saved configuration or checkpoint layout. Dependencies separate each dispatch, and scratch is reused only after all stages finish that partition. Each dispatch initializes its own workgroup LUT; this does not extend shared-memory lifetime across dispatches. ARM vendor ID `0x13b5` selects the path automatically; GTX defaults to monolithic evolution, with `DAWNWOOD_SPLIT_EVOLUTION=1` available for desktop inspection. Extra dispatches/barriers/scratch traffic require their own timings.

The staged APK with SHA-256 **8c86dbcd791a824b1402a5561c3ef3926a8f539900d0dcdf95b1563d89726430** passes **128 states × 16 epochs**, **257 × 1,024**, **4,096 × 256** and **65,537 × four** on the actual POCO with zero bitwise word differences. Repeated timing and complete-population capacity measurements also finish successfully. Phone validation layers are disabled; zero message counters do not prove layer validation.

Initialization is a separate remaining portability boundary: `src/cpu.cpp` uses host-native C++ math to create the initial population. Local verification supplies identical snapshots to its CPU and GPU, but identical Windows/Android CLI seeds/configuration need not produce identical starting FP32 bits. No cross-device bitwise replay is claimed without importing the same initial-state/checkpoint payload and measuring it.

## Large-population execution and memory

| Change | Previous restriction or cost | Current behavior |
|---|---|---|
| Bounded staging | One full-state-sized transfer allocation | Reusable staging is at most 16 MiB; state transfers and image-row copies are chunked |
| Release initialization snapshot in ordinary GPU runs | Initial and final CPU snapshots could coexist with GPU copies and staging | Initial host vectors are released before final full readback allocation |
| Partition evolution | A large single dispatch/submission was the work unit | At most 65,536 states per current evolution partition, further bounded by device dispatch limits |
| Preserve whole-population semantics | Naive independent sub-populations would change feedback | Mutation once per epoch; all slices read the same old state and new LUT; swap only after every slice finishes |
| Transient dispatch offset | Need a global index across partitions | Push-constant copy uses `Config.reserved0`; stored config and checkpoint ABI stay unchanged |
| Prefer suitable discrete memory | Small state buffers could choose a coherent aperture heap | Discrete state allocations prefer non-host-visible device-local memory when available |
| Report actual allocation roles | Buffer-only totals missed image storage | State buffers, LUT images, staging, padding, per-heap placement and device limits are reported separately |
| Explicit capacity budget | Nominal VRAM/RAM suggested an unmeasured maximum | Runtime `--budget-fraction` and a fresh-probe capacity runner state the policy and stopping condition |
| Pipeline allocation order | Compiler memory competed with an already allocated near-capacity population | Compile pipelines first, refresh memory observations, then allocate large data resources |

The new `tools/measure_capacity.py` runs real populations through the normal recurrence and full readback. Defaults are two epochs, one epoch per requested batch, 95% of current Vulkan application headroom minus a 128 MiB reserve, and a host-memory limit using 85% of available physical memory. It grows the population, refines recoverable allocation failures and preserves every command and output. A counted result requires the requested population and epoch count, healthy records and full-state digests. Serious device errors, timeouts or unhealthy output stop growth.

Two GPU state copies consume 256 bytes per evolving state; they are not twice as many states. A host snapshot adds 128 bytes/state, plus operator records. On shared-memory hardware these allocations use the same physical RAM. API limits, allocation padding, driver memory and changing system pressure also constrain a practical population. Filling spare buffers around a small kernel would not establish the same result as advancing every claimed state; this runner advances the full claimed population.

## Recorded candidate evidence

These observations distinguish the initial texture/shared sin-cos-exp candidate from the later integer-corrected sqrt/div candidate. Raw records are under `results/v0.5/`; earlier timings do not automatically describe the corrected arithmetic.

| Work performed | Recorded outcome |
|---|---|
| Existing CPU fixtures, initial and corrected candidates | 30/30 pass on each |
| Corrected sqrt/div candidate, GTX 257 states, 1,024 epochs | All epochs pass, maximum absolute difference zero, exact integer words |
| Corrected candidate, GTX 257 states, 4,096 epochs | Zero bitwise word differences at every epoch |
| Corrected candidate, GTX 4,096 states, 256 epochs | Zero bitwise word differences at every epoch |
| Corrected candidate, GTX 65,537 states, four epochs | Zero bitwise word differences across the partition boundary |
| Corrected candidate, GTX 65 states, 511 operators, 64 epochs | Zero bitwise word differences with a larger route tree and multirow LUT |
| GTX, 128 states, 16 epochs | Per-epoch CPU/GPU comparison passes |
| Initial trig-only candidate, GTX 257 states, 1,024 requested epochs | Fails at epoch 305; 304 preceding epochs pass |
| GTX, 65 states, 511 operators, 16 epochs | Pass; exercises two-row LUT |
| GTX, 65,537 states, two epochs | Pass across the partition boundary |
| Multirow LUT exact roundtrip | Checkpoint SHA-256 matches, including exercised high flag bits and signed-zero parameters |
| LUT transfer larger than staging | 262,145 operators roundtrip exactly through the 16 MiB staging allocation |
| Batching semantics | 257-state, 17-epoch checkpoints agree byte-for-byte with requested batch sizes 17 and 1 |
| Vulkan validation in those comparisons | Layer enabled; zero recorded errors and warnings |
| GTX real-population capacity candidate | 12,490,752 states each complete two epochs, healthy full readback |
| Corrected arithmetic, 23 September GTX verification | 257 states × 1,024 epochs and 65,537 × four epochs pass with zero bitwise differences; layers enabled, zero errors/warnings |
| Corrected arithmetic, 23 September GTX capacity | 12,256,960 states × two epochs, healthy full readback, 2.830 million state updates/s under the recorded policy |
| Initial 23 September POCO v0.5 APK | CPU fixtures pass; GPU evolution-pipeline creation fails with VkResult -3; a later run terminates the native process |
| Staged phone APK, 128 × 16, 257 × 1,024, 4,096 × 256 and 65,537 × four | Zero bitwise word differences on actual Mali; healthy 4,096-state/64-epoch run also completes |
| Current desktop capacity | 12,244,544 states × two epochs, healthy full readback, 1.738 million state updates/s |
| Current phone benchmark and capacity | Median 0.1693103924 s for 4,096 × 64; 14,569,792 records × two epochs at 2.445501 million updates/s, healthy full readback |

The initial long failure is `epoch 305 state[205].ai`, CPU `0.0916269422`, Vulkan `0.0916389078`. One float exceeded tolerance; there were no integer mismatches, nonfinite values or invalid records. This is retained as a failed candidate, not a success because it ran longer than v0.4. After corrected division and square root were added, `verify_corrected_257_1024_v05.stdout` records all 1,024 epochs passing with zero numerical difference, exact integer words, no invalid/nonfinite values, and zero errors/warnings with core and synchronization validation enabled. That is a measured workload result, not an all-device or unlimited-horizon guarantee.

`results/v0.5/capacity_candidate1/summary.json` records **12,490,752 states**, two complete epochs, **3,049.5 MiB** of state ping-pong payload, **1.006620256 seconds** of Vulkan device time, **24.817 million state updates/second**, and **22.969 seconds** for the whole process. The largest individual recorded submission was **3.05962 ms**. The full-state/LUT digest was `ce1eb05b401c0a1a`; health passed. This run reached its current memory policy boundary without an allocation failure. It is not an absolute hardware maximum, not a final-arithmetic benchmark and not a CPU/GPU equivalence check. Vulkan validation layers were disabled for this capacity timing, so its zero message counts are not a layer-validation result.

## Corrected-build performance on 23 September

The current desktop executable SHA-256 **f208a48e4cd6c4cad9403736cbbba398c8d283649c1a025418521c3d9de1bb10** has all seven shaders embedded. Its forced staged path passes 257 states × 1,024 epochs and 65,537 states × four epochs with zero bitwise differences, with core/synchronization layers enabled and zero errors/warnings. Default monolithic execution also passes 257 states × 64 and 257 × 1,024 epochs. Full 4,096-state/64-epoch checkpoint bytes agree across pre-compaction CPU, compact CPU, current CPU, current monolithic GPU and current staged GPU. `laptop/final_checkpoint_comparison.json` records that preservation evidence.

For **this current executable**, three-sample medians at 4,096 states × 64 epochs are **0.157167648 seconds GPU device time**, **2.4557445 ms per whole-population epoch**, **1.667926 million state updates/s** and **0.859 seconds whole-process time**. CPU medians are **8.1974733 seconds** evolution wall time and **8.218 seconds** whole-process time. `laptop/final_benchmark_summary.json` retains every sample, artifact identity and timing scope. The current median is slower than the preceding measurement below. Numerical agreement and phone compilation/execution improved; a speed improvement has not been demonstrated.

Current capacity is **12,244,544 states × two epochs**, with healthy full readback and digest. State ping-pong payload is **2,989.39 MiB**, device time **14.0899049 seconds**, throughput **1.738059 million state updates/s**, and whole-process time **36.485 seconds**. Maximum submission is **38.1315 ms**. The run reaches 95% of reported free budget minus a 128 MiB reserve without allocation/health failure; it is not an absolute maximum or CPU comparison of the full population. `laptop/capacity_final95/summary.json` identifies the evidence. A separate three-pair 4,096 × 64 schedule comparison finds staged evolution **4.3% slower** than monolithic at the median with identical digests, supporting the retained GTX monolithic default.

The following preserved measurements describe the **preceding pre-compaction executable**, not the current artifact:

The corrected arithmetic is substantially slower in the measured large workload: the 23 September pre-compaction executable completes **12,256,960 states × two epochs** in **8.661623776 seconds** of device time, or **2.830 million state updates/second**. State ping-pong payload is **2,992.42 MiB** and whole-process time is **37.266 seconds**. This reaches the stated 95%-budget/128 MiB-reserve policy; it is not a fixed-population speed-ratio experiment, an absolute capacity maximum or a comparison of that full population against CPU. `results/v0.5/2026-09-23/laptop/summary.json` identifies the executable and retained artifacts. Later compiler changes must be measured separately. Numerical agreement was improved at a real measured performance cost; the old 24.817 million rate must not be advertised for the corrected build.

For a 4,096-state, 64-epoch workload, that same corrected executable's three-sample GTX median is **0.09632352 seconds** of device time, **1.505055 ms per whole-population epoch**, or **2.721 million state updates/second**. Median whole-process time is **0.688 seconds**. The CPU median is **6.4672045 seconds** of evolution wall time and **6.5 seconds** for the whole process. Every final state/LUT digest agrees. Timing scopes, first-sample variation and ordinary-desktop conditions are retained in `benchmark_summary.json`.

## Current phone performance and capacity

The same final APK has a three-sample median **0.1693103924 seconds GPU device time** for 4,096 states × 64 epochs, batch 8: **2.64547488125 ms per whole-population epoch**, or **1.548304 million state updates/s**. All reports are healthy and same-device digests agree. Median app native wall time is **5.818 seconds**, including native initialization/setup/transfers/readback/health but excluding ADB launch/polling. That timer differs from desktop whole-process wall time. These are ordinary-condition observations of a Windows Release executable and Android debug native build, not peak hardware ratings.

The final POCO capacity is **14,569,792 complete 128-byte states × two epochs**, with full readback, health and digest. Device time is **11.91558916 seconds**, or **2.445501 million state updates/s**, and ADB launch-to-report time **77.546 seconds**. Two GPU state copies consume **3,557.078125 MiB** of shared RAM; staging is 16 MiB and staged scratch is 6 MiB. The limiting policy uses 85% of currently available Android physical memory, accounts for a host snapshot, and reserves the larger of 128 MiB or the OS low-memory threshold (**226,492,416 bytes** here). No allocation/health failure occurs. Available memory changes during growth; this is a completed population under policy, not an absolute maximum. Raw final records are `phone_benchmark/summary.json` and `phone_capacity/summary.json` under `results/v0.5/2026-09-23/`.

## Formalization and compatibility

`FORMALIZATION_v0.5.md` retains all fifteen sections and all 31 catalogue entries from the complete source-aligned v0.4 edition. It adds exact texture layout, the distinction between one-bit controls and four-bit bytecode, shared-storage lifetime, bounded transfers and epoch-preserving partitions. Plain definitions explain state updates/second, kernel versus whole-process time, actual allocation versus nominal memory and capacity versus occupancy/cache/bandwidth.

The formalization now explicitly separates **mutable descriptors and scalar bodies** from the **fixed native algorithms** that interpret them. RK4, the Hadamard matrix, primitive formulas, topology/wrapping, tree-address rules and update order remain native. Editing their named records modulates the documented responses; it does not replace those algorithms or grow the tree/population. That stronger source architecture remains unfinished even when the numerical backend comparisons pass.

The 128-byte state, 64-byte operator, 64-byte configuration and `DWKN0003` checkpoint layout remain compatible. Old snapshots may seed the new recurrence, but new arithmetic does not promise replay of an old bitwise trajectory. The semantic profile must be recorded separately because the checkpoint has no profile tag.

No new repository test sources were added. Existing checks and explicit measurement/diagnostic invocations supply the evidence. Smooth intrinsic Klein dynamics, ordinary RK4 convergence order for the altered fourth stage, universality, physical detector behavior, automatic noise deletion, permanent cache residence and hypothetical full-state compression remain unproved. This revision makes the executable representation more concrete; it does not convert those proposals into established results.
