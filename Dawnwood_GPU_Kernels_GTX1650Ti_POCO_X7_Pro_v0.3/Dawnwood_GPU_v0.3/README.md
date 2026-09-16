# Dawnwood Interactive — Numerical GPU Kernel, v0.3

**Tom Klootwijk · Dawnwood Interactive**  
**Targets:** GTX 1650 Ti laptop, owner-confirmed 4 GB; POCO X7 Pro, owner-specified 12 GB edition.

The source names the whole a **Universal Spatial State Automaton**. This package implements the Dawnwood recurrence numerically in **C++ and Vulkan compute**, with a desktop executable and an **Android NDK application using the same compute kernels**. It is not another symbolic-only workbench. The original source is included, and every major source requirement/claim has a linked test or measurement entry.

Start with **`results/STATUS.md`** for what was actually built and tested in this archive. Then read **`docs/BUILD_AND_RUN.md`** for your laptop and phone. Your physical devices are not marked tested merely because source code, SPIR-V or an APK exists.

## The implemented circulation

A mutable operator LUT and a whole numerical state feed one another. The GPU first changes operator bodies, field parameters and pinion-held Klein-surface positions from preceding feedback. It then evaluates the changed operators through the double-pinion/Hadamard, log-polar, binary route, four-slot RK4 with double Y-up, geometric/colon/phyllotaxis/blend, RGBA/history/inverse-T, and surface-return stages. The result feeds the next interval.

The operator body is executable scalar bytecode in a mutable device buffer. Body edits and GPU mutation affect actual numerical outputs. There are no per-interval host uploads of those changes. Several dispatches schedule one recurrence; they do not separate it into unrelated engines.

The original discussion leaves several numerical equations open. **`docs/NUMERICAL_PROFILE.md`** states the complete DWI-N1 choices—including the Klein quotient/embedding, local fields, derivative, jitter, coupling and inverse representation—so no new equation is disguised as text already supplied in the source. The kernel uses FP32 and uint32 with an explicit 128-byte state and 64-byte operator ABI.

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
