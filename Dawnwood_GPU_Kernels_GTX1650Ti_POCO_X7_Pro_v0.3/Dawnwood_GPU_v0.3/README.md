# Dawnwood Interactive — Numerical GPU Kernel, v0.5.0

**Numerical validation: pass for the recorded workloads on both physical devices, 23 September 2026.** Current GTX and POCO CPU/GPU comparisons have zero bitwise differences at unchanged tolerances, including 257 states over 1,024 epochs on both. The POCO also passes 4,096 × 256 and 65,537 × four; initial Mali pipeline failures remain recorded. Read **`docs/VALIDATION_v0.5.md`** for artifact identities, exact scope, performance costs and the quick claim table. The source's full self-defining architecture and stronger physical/universality claims remain unestablished.

The current formalization is **`docs/FORMALIZATION_v0.5.md`**, developed from the supplied **Dawnwood_Interactive_Unified_v0.2.pdf** through the reviewed v0.4 edition. **`docs/CHANGES_v0.5.md`** records corrections and compatibility limits. The working-directory name is historical; current executable reports identify **DWI-N1-0.5**. Original v0.3/v0.4 documents and results remain historical evidence, including the v0.4 GTX epoch-96 and POCO epoch-1 numerical failures.

**Tom Klootwijk · Dawnwood Interactive**  
**Targets:** GTX 1650 Ti laptop, owner-confirmed 4 GB; POCO X7 Pro, owner-specified 12 GB edition.

At **4,096 states × 64 epochs**, three-sample median GPU times are **0.157168 s on GTX** and **0.169310 s on POCO**: **1.668 million** and **1.548 million state updates/s**. Capacity runs complete **12,244,544 GTX states** and **14,569,792 POCO states**, two epochs each, under their stated memory policies. These are full 128-byte states with complete readback, not raw texel counts or absolute hardware maxima. GPU timers exclude setup/readback. Correctness and phone execution improved; a speed improvement over earlier candidates was not demonstrated.

The source names the whole a **Universal Spatial State Automaton**. This package implements the Dawnwood recurrence numerically in **C++ and Vulkan compute**, with a desktop executable and an **Android NDK application using the same compute kernels**. It is not another symbolic-only workbench. The original source is included, and every major source requirement/claim has a linked test or measurement entry.

Start with **`docs/VALIDATION_v0.5.md`** for what has actually completed on each device. Then read **`docs/BUILD_AND_RUN.md`** for your laptop and phone. `results/STATUS.md` indexes the current packaged campaign; files under older version directories describe their identified builds. The previous root status is preserved as `results/v0.4/historical_root_STATUS.md`. A source tree, SPIR-V file or APK is not evidence of successful physical-device execution.

## The implemented circulation

A mutable operator LUT and a whole numerical state feed one another. The GPU first changes operator bodies, field parameters and pinion-held Klein-surface positions from preceding feedback. It then evaluates the changed operators through the double-pinion/Hadamard, log-polar, binary route, four-slot RK4 with double Y-up, geometric/colon/phyllotaxis/blend, RGBA/history/inverse-T, and surface-return stages. The result feeds the next interval.

The operator body is executable scalar bytecode in a mutable integer texture: four `RGBA32_UINT` texels preserve each 64-byte record. One-bit controls coexist with full FP32 field parameters; the nine-opcode vocabulary still uses four bits per instruction. The core 31 descriptors use 1,984 bytes of shared workgroup storage. Body edits and GPU mutation affect actual numerical outputs without per-interval host uploads. This is explicit descriptor reuse, not proof of permanent hardware-cache residence.

**The full source proposal is only partly implemented.** The RK4 algorithm, Hadamard matrix, primitive formulas, Klein wrapping, update order and tree-address rules remain fixed native algorithms. Mutable records change their declared inputs and scalar responses; they do not rewrite those algorithms or grow a tree. Numerical backend agreement does not close that architectural gap or establish quantum physics, universality or automatic noise removal.

The original discussion leaves several numerical equations open. **`docs/NUMERICAL_PROFILE.md`** states the complete DWI-N1 choices—including the Klein quotient/embedding, local fields, derivative, jitter, coupling and inverse representation—so no new equation is disguised as text already supplied in the source. The kernel uses FP32 and uint32 with an explicit 128-byte state and 64-byte operator ABI.

Version 0.5 makes elementary-function arithmetic explicit across CPU/GPU and keeps the original acceptance tolerance. It caps staging at 16 MiB and partitions large populations while preserving one mutation per epoch and whole-population feedback. Practical capacity counts records that actually finish the requested updates and full readback under a stated memory policy. The phone's 12 GB system RAM is shared with Android and is not 12 GB of dedicated GPU memory.

The ARM path splits each evolution partition into eight dependent dispatches and adds bounded scratch of at most 6 MiB to reduce compiler workload. GTX defaults to one evolution dispatch per partition. Timing and memory reports identify the selected path. Each local CPU/GPU comparison starts from the same snapshot, but initialization still uses host-native math: identical CLI parameters do not currently guarantee bitwise-identical initial state across Windows and Android.

## Laptop bring-up

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/dawnwood selftest
./build/dawnwood probe --device '1650 Ti' --count 1
python3 tools/run_claims.py --binary build/dawnwood --device '1650 Ti' --bench --out results/gtx1650ti
```

On Windows, build with `--config Release` and use `build\Release\dawnwood.exe`. The full Windows instructions are in the build guide. A C++ compiler, CMake and Vulkan development files are required. The generated SPIR-V is bundled and embedded; a shader compiler is needed when changing the equations.

## POCO bring-up

Open `android/` in Android Studio or use the pinned command-line build:

```sh
cd android
./gradlew assembleDebug
cd ..
python3 tools/test_phone.py --apk android/app/build/outputs/apk/debug/app-debug.apk --out results/poco_x7_pro
```

The phone must authorize the computer's ADB connection. The app runs native Vulkan work on a worker thread and saves probe, CPU fixture, CPU/GPU comparison and numerical-run reports. No root or replacement operating-system kernel is involved. Its system RAM and thermal context are reported separately from Vulkan heap budgets.

## Source-claim tests

**`docs/CLAIMS.md`** maps the source's original relationships and stronger AI assertions to concrete tests. The suite covers exact parity/indexing, source-vector preservation, primitive fields, Klein transport, hinge norm, double Y-up, numerical operator changes, inverse residual/history, checkpoint replay, all-word CPU/GPU agreement, real BC5 block encoding/decoding and byte accounting. Device probes and count-scaling runs collect hardware evidence when the target is present.

Counterexample tests are retained: an inverse does not automatically delete noise, a transformed field need not remain an exact metric SDF, and removing pointers cannot multiply an already pointer-free payload count. The physical and universality rows are not falsely labelled successful by software unit tests. `tools/evaluate_experiment.py` accepts supplied detector observations and explicit candidate/reference predictions for a separate experimental comparison.

## Work with actual state and operator bodies

```sh
./build/dawnwood run --device '1650 Ti' --count 4096 --steps 64 --batch 8 --checkpoint state.dwk --out run.json
./build/dawnwood run --device '1650 Ti' --resume state.dwk --steps 64 --checkpoint continued.dwk
./build/dawnwood run --device '1650 Ti' --count 4096 --steps 64 --program 6:0x2
python3 tools/edit_checkpoint.py state.dwk --index 6
python3 tools/readout.py state.dwk --out returned_channels.csv
```

`--backend cpu` selects the numerical CPU implementation. `verify` compares both backends after **every** interval and reports the first mismatching field. Checkpoints contain all live state and operator records. `tools/edit_checkpoint.py` can replace fields from a JSON object and write a changed checkpoint; the next run uses those changed definitions.

## Package map

| Location | Contents |
|---|---|
| `include/`, `src/`, `shaders/` | Numerical equations, actual CPU/Vulkan runtime, GPU mutation/evolution kernels and SPIR-V. |
| `android/` | Java activity, JNI bridge, arm64 native build and pinned Gradle configuration. |
| `tools/`, `tests/` | Build, claims, phone automation, checkpoint editing, output, compression and observation-comparison tools. |
| `profiles/` | Numerical and target-device inputs, plus source operator catalogue. |
| `docs/` | Numerical binding, source-claim map, build/run instructions and primary references. |
| `results/` | Actual build/test status, raw command logs, device identity and numerical evidence. |
| `source/` | Original PDF and prior project material available during this build. |
| `author.json` | Supplied attribution and personal identifiers. |
| `MANIFEST.sha256` | Integrity hashes for the shipped files. |

The full package includes the original source and supplied personal attribution. Review those before any public redistribution.
