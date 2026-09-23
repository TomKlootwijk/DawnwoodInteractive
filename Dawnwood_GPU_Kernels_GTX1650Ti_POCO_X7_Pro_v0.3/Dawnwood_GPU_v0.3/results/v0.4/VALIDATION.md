# Validation record - Dawnwood v0.4

Date: 16 September 2026. **Partially validated; two numerical agreement failures remain.** The final kernels build and execute on both physical targets. No test sources were added. Existing fixtures, existing comparison tools and recorded manual invocations were used. The original v0.3 archive and the latest supplied v0.2 formalization remain unchanged.

## Results on the final implementation

| Check | Recorded result |
|---|---|
| Desktop C++ and both SPIR-V shaders | Build and SPIR-V validation pass |
| Existing desktop CPU fixtures | 30/30 pass |
| Existing Python source/packing checks | 17/17 pass |
| Active operator numerical sensitivity | 29/29 pass; Bayer/BC5 are downstream |
| CPU checkpoint replay | Exact digest match |
| GTX 1650 Ti, 128 states x 16 epochs | All-word CPU/GPU comparison passes |
| GTX 1650 Ti, 257 states x 128 requested epochs | Fails at epoch 96; 95 preceding epochs pass |
| Desktop core and synchronization validation | Zero errors and zero warnings in the final long comparison |
| Near uint32 epoch limit, 257 states | One-step comparison passes through epoch 4294967295; overflow request rejected |
| Zero-epoch GPU readback | Passes with validation; ordinary zero-step runs remain supported |
| Invalid opcode checkpoint, malformed float, zero-step verify | Each rejected with nonzero exit |
| Android arm64 library and APK | Build successfully with recorded alternative toolchain |
| Actual POCO X7 Pro CPU fixtures | 30/30 pass |
| Actual POCO X7 Pro GPU pipeline creation | Passes after sharing one RK derivative call site |
| POCO, 128 states x 16 requested epochs | Comparison fails at epoch 1 |
| POCO, 4096 states x 64 epochs | Completes; finite valid records, no out-of-chart states |

The final desktop suite is `claims_rk_loop/`; final phone reports are `phone_rk_loop/`. `*.command.json`, stdout and stderr retain actual commands, exit codes and timings. Earlier directories record earlier revisions and retained failures; they do not override the final table. `summary.json` is the machine-readable edition summary.

## Numerical disagreement is retained

All comparisons use the original rule `abs(cpu-gpu) <= 1e-5 + 2e-5*max(abs(cpu),abs(gpu))`; integer words must be exact. The tolerance was not relaxed.

The GTX's first final mismatch is **epoch 96, state[222].ai**, CPU **-0.0367288142**, Vulkan **-0.0367168337**. There is one out-of-tolerance float at that epoch, with no integer mismatch, nonfinite value or invalid record. Across the checked epochs, maximum absolute error is **4.768371582e-5** and maximum scaled error is **1.116069538**. Starting both backends from the identical saved CPU epoch-95 state and advancing once passes, with maximum absolute error **1.907348633e-6**. This supports accumulated backend rounding drift as a diagnosis; it does not isolate every elementary-function discrepancy or establish an unlimited horizon.

The POCO's first mismatch is **epoch 1, state[1].ar**, CPU **-0.289921224**, Vulkan **-0.289942235**. There are **135** out-of-tolerance floats, **zero** integer mismatches, and no nonfinite or invalid records. Maximum absolute error is **4.159659147e-5**; maximum scaled error is **3.415186812**. The phone's comparison therefore does not pass even though it now executes the kernel. Residual backend arithmetic must be investigated before claiming the same numerical accuracy on Mali. No custom transcendental approximation was silently substituted.

The independent 4096-state phone run completed all 64 epochs with maximum reported energy error from the source norm five of **0.000226974**. A health pass checks finite/structural validity; it is not a backend-equivalence certificate. Android Vulkan validation layers were not installed for this run, so zero recorded layer errors on the phone is not a validation-layer result.

## The phone compilation improvement

Initial real-device attempts failed creating the evolve pipeline, including with a one-state probe. Own-process logs showed Scudo allocator exhaustion and native crashes; approximately 2.28 GB process RSS was observed during a compiler attempt. These were driver/compiler allocations, not the live-state buffer payload.

Explicit loop controls, removal of artificial return-macro loops and offline optimization alone did not resolve the failure. Replacing four expanded RK derivative call sites with one call in a non-unrolled four-iteration loop reduced optimized evolution SPIR-V from **578,760 to 268,608 bytes** and instructions from **36,200 to 16,724**. All four slope records and two separate fourth-stage Y-up additions remain. The 257-state, 95-epoch CPU state/LUT digest stayed **0380ebf43a2cfb07**, and the existing Y-up fixture passed. With this change the actual Mali pipeline compiles and the 64-epoch run completes. This demonstrates a compilation-resource improvement; it is not a claim of universal driver compatibility.

`phone/`, `phone_loop_control/` and `phone_optimized/` preserve unsuccessful attempts. Early broad system logcat files are excluded from the release archive; the retained release evidence uses the application's own PID logs. Final build uses `tools/build_shaders.py --optimize` and retains arithmetic `NoContraction` and loop `DontUnroll` decorations.

## Hardware, memory and build provenance

Desktop: **NVIDIA GeForce GTX 1650 Ti with Max-Q Design**, driver **581.80**, NVML-reported **4096 MiB**. Windows 11 build 26200; MSVC 19.44; CMake 3.31.6; shader tools from NDK 29.0.14206865. Vulkan headers were copied separately from the installed NDK; the import library was generated from the installed Vulkan loader's exported functions. The first baseline configuration accidentally included the whole Android sysroot; that failed build and the corrected configuration remain logged. It was a local setup error, not a kernel defect.

The official LunarG 1.4.357.0 validation layer was extracted into a local directory and its download checksum verified. No system SDK installation/registry changes were needed. Final desktop commands set `DAWNWOOD_VALIDATION=1`, `VK_LAYER_PATH` and `VK_LAYER_VALIDATE_SYNC=1` per process. The first layer run emitted a deprecated-setting warning; later recorded runs use the new setting and report zero warnings. See `layers_provenance.json`.

Phone: **POCO X7 Pro**, model **2412DPC0AG**, Android API **36**, arm64-v8a, **Mali-G720 MC7**, raw driver version **205524992**. The device reports **11,861,921,792 bytes of system RAM**, not dedicated VRAM. The final 4096-state run allocates **1,576,832 padded buffer bytes**, uploads **526,272 bytes** and downloads **526,272 bytes**. These omit driver/pipeline allocations. The phone does not expose `VK_EXT_memory_budget`; heap size is a fallback limit, not free RAM. BC5 sampled-image and BC compression support are **false**; EAC/ASTC sampled support is true. The exact recurrent state remains in storage buffers.

The APK uses pinned Gradle 8.9 / AGP 8.7.3 / SDK 35 with the available **NDK 29.0.14206865 and CMake 3.31.6**, selected by `android-local-toolchain.gradle`. Original NDK/CMake pins are unchanged. The authorized phone ran the built APK; it was force-stopped after measurement. Initial failures and the final successful execution are distinct from the remaining failed numerical comparison.

## Timing observations

Three desktop samples per count, 16 epochs, batch size eight; medians below. These are measurements for the final build, not a controlled before/after speedup study.

| States | CPU host compute ms | GTX device-timestamp ms |
|---|---|---|
| 256 | 45.967 | 3.336 |
| 1024 | 219.892 | 3.414 |
| 4096 | 734.800 | 4.146 |

CPU and GPU use different timing scopes; GPU initialization, pipeline compilation and transfers are excluded from device timestamps. The final phone's single 4096-state, 64-epoch run reports **98.019 ms** from device timestamps, with Android thermal status zero. No sustained thermal or cross-device speedup claim follows.

## Scope and reproducibility

Final equations are in the shared include files; the full definition is `docs/FORMALIZATION_v0.4.md`. Reproduce desktop source-linked checks with `python tools/run_claims.py --binary build/Release/dawnwood.exe --device "1650 Ti" --bench --out results/reproduction`. Reproduce the known long failure with `dawnwood verify --device "1650 Ti" --count 257 --steps 128`. Use the recorded Android init script and `tools/test_phone.py` for the phone; its comparison correctly returns a failing overall status.

Record layout remains `DWKN0003`; valid old snapshots seed corrected v0.4 dynamics, not bitwise v0.3 trajectories. The synthetic near-limit checkpoint sets only the epoch of a zero-step snapshot to 4294967294; it is not a claim of running billions of intervals. No smooth Klein tangent-flow proof, physical detector experiment, universality proof, automatic noise deletion, permanent cache residence or lossless full-state BC5 representation was supplied by these checks.
