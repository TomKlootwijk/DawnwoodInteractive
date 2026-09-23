# Build and run v0.5.0 on the two target devices

Current measured status is `docs/VALIDATION_v0.5.md`, with identified artifacts and raw results under `results/v0.5/`. Older failures remain under their original version/candidate directories. Commands below are reproduction instructions, not compatibility guarantees. The current Android build uses available NDK **29.0.14206865** and CMake **3.31.6** through the retained `results/v0.4/android-local-toolchain.gradle` init script; the original project pins remain unchanged. The historical name of that init script does not determine the executable profile. Build success and actual phone execution are separate results.

On a machine with those alternative dependencies, reproduce that Android build from `android/` with `gradlew.bat --no-daemon -I ../results/v0.4/android-local-toolchain.gradle assembleDebug`. Set `ANDROID_HOME`/`ANDROID_SDK_ROOT` or `android/local.properties` to the installed SDK first. The pinned Gradle 8.9 wrapper and its checksum are included. The normal command below uses the project's original pinned NDK/CMake unless the init script is supplied.

## Desktop — GTX 1650 Ti laptop, owner-confirmed 4 GB

Install a C++17 compiler, CMake 3.22 or later and the Vulkan SDK/development files. Use the current NVIDIA driver provided for your operating system. The shipped SPIR-V is embedded in the executable; a shader compiler is only needed when changing the numerical/shader sources.

Windows, from a developer terminal:

```powershell
cmake -S . -B build -A x64
cmake --build build --config Release
build\Release\dawnwood.exe selftest
build\Release\dawnwood.exe probe --device "1650 Ti" --count 1
python tools\run_claims.py --binary build\Release\dawnwood.exe --device "1650 Ti" --bench --out results\gtx1650ti
```

Linux:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/dawnwood selftest
./build/dawnwood probe --device '1650 Ti' --count 1
python3 tools/run_claims.py --binary build/dawnwood --device '1650 Ti' --bench --out results/gtx1650ti
```

A Vulkan loader/development package and working device driver are required. The software ICD used for a headless test, when present, is explicitly marked `software_device: true` and is rejected unless `--allow-software` is supplied. Do not add that switch to a test intended to establish results on your GTX.

## A live numerical session

```sh
./build/dawnwood run --count 4096 --steps 64 --batch 8 --device '1650 Ti' --checkpoint state.dwk --out run.json
./build/dawnwood run --resume state.dwk --steps 64 --batch 8 --device '1650 Ti' --checkpoint continued.dwk
./build/dawnwood run --count 4096 --steps 64 --device '1650 Ti' --program 6:0x2
python3 tools/edit_checkpoint.py state.dwk --index 6
```

`run` is Vulkan by default; `--backend cpu` evaluates the same numerical profile on the CPU. `verify` advances both one interval at a time and compares all state and operator words. Integer words must match exactly. Float tolerances are printed with the comparison. The first mismatch is retained with its interval and field name.

`bitwise_word_mismatches` and `bitwise_equal` separately report stronger word-for-word identity; tolerance acceptance still uses `atol=1e-5`, `rtol=2e-5`. A local CPU/GPU pair starts from the same initialized snapshot. Initialization still uses host-native C++ math, so independently initialized Windows and Android runs need not have the same initial FP32 bits despite equal CLI parameters. Use an identical checkpoint/initial payload before claiming cross-device bitwise replay.

`--batch` requests how many Ψ intervals are grouped by the driver. Small populations use at most eight complete epochs per submission. Large populations are divided into bounded evolution partitions of at most 65,536 states, with one mutation per global epoch and parity exchange after every partition finishes. Each partition is submitted/fenced; `--batch` cannot bypass that bound. Actual buffer/dispatch limits are queried; a resource failure returns an error rather than silently changing the population.

Capacity uses real full-population work followed by complete readback, not filler allocations. A desktop example is:

```powershell
python tools\measure_capacity.py --binary build\Release\dawnwood.exe --device "1650 Ti" --steps 2 --budget-fraction 0.95 --reserve-mib 128 --out results\v0.5\my_laptop_capacity
```

The result is the highest completed population under that current-memory policy, not an absolute hardware maximum. Read the reported stopping condition, timer scope, artifact identity and health result.

## Android — POCO X7 Pro, owner-specified 12 GB edition

Open `android/` in Android Studio, or use its command-line SDK tools. The project pins JDK 17, Gradle 8.9, Android Gradle Plugin 8.7.3, compile/target SDK 35, NDK `27.2.12479018`, CMake `3.22.1`, and arm64-v8a. These are reproducible build inputs, not an assertion that they are the newest releases.

Set the Android SDK path in `android/local.properties` (`sdk.dir=...`) or through your SDK environment. Install the pinned platform/NDK/CMake packages. Then:

```sh
cd android
./gradlew assembleDebug
cd ..
python3 tools/test_phone.py --apk android/app/build/outputs/apk/debug/app-debug.apk --out results/poco_x7_pro
```

On Windows use `gradlew.bat` and `python`. If the wrapper JAR was not downloaded during package preparation, the launcher runs `tools/bootstrap_gradle.py`, which fetches the official pinned wrapper and checks its official checksum. This is build-tool retrieval; the Android application itself has no Internet permission.

Connect the phone with USB debugging enabled and authorize this computer in the phone's prompt. `adb devices` must list it as `device`, not `unauthorized`. For multiple connected devices, pass `--serial SERIAL` to the script. The script installs the debug APK, opens the app for probe/tests/verification/run, and retrieves actual reports with `run-as`.

The app also has four buttons for those operations. The native runtime runs on a worker thread, not the UI thread. Desktop and Android embed the same **seven shader modules**: `mutate`, monolithic `evolve`, and staged `prepare`, `slope`, `combine`, `geometry`, `finish`. ARM devices use the staged path automatically. It dispatches prepare, slope four times, combine, geometry and finish for each evolution partition; mutation still runs once per global epoch. GTX defaults to monolithic evolution. No root access, operating-system kernel replacement, CUDA runtime, swapchain or rendering pipeline is needed.

Staged evolution adds 96 bytes of scratch per active partition state, capped at 6 MiB with the current partition limit. Each dispatch has its own shared LUT initialization and compute dependency. This is one recurrence split to reduce compiler workload, not eight separate epochs. The checkpoint record sizes remain unchanged.

After the basic actual-phone comparison succeeds, the capacity tool can run the same application's larger populations:

```powershell
python tools\measure_phone_capacity.py --serial SERIAL --apk bin\android\Dawnwood_GPU_v0.5_debug.apk --steps 2 --budget-fraction 0.95 --reserve-mib 128 --out results\v0.5\my_phone_capacity
```

Use the intended APK path and authorized serial. `docs/PHONE_CAPACITY_v0.5.md` describes the recording/policy details. Available Android RAM and low-memory threshold constrain the population separately from Vulkan heap size; 12 GB system RAM is not dedicated VRAM.

A desktop shader build is not an APK build. An APK build is not a phone test. The archive's generated status distinguishes those stages.

## Inspect device conditions

The Vulkan report includes actual device name/vendor, API/driver versions, resource limits, memory heaps/budgets, format support, transfer counters and timer source. It also identifies texture layout/precision, selected heaps and padded allocations, bounded staging, `split_evolution`, dispatches per partition and scratch allocation. Android reports include model/ABI, system RAM availability/threshold, thermal status and battery temperature. Battery temperature is not GPU temperature. A zero validation counter establishes no validation-layer check unless `validation_layer_enabled` is true.

Initial uploads and final downloads are explicit and counted. `advance()` contains no buffer/image-copy commands. Staged scratch storage still causes device-memory reads/writes. Neither fact substitutes for a bus monitor or permanent-cache-residency measurement. Hardware counters or vendor traces can be attached to the saved report as separate evidence. Device timestamps exclude pipeline creation, upload, readback and gaps between host submissions; whole-process and phase wall timings answer different questions.

## Rebuild after editing equations

```sh
python3 tools/build_shaders.py --optimize --preserve-math-functions --preserve-interpreter-functions
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
python3 tools/run_claims.py --binary build/dawnwood --device '1650 Ti'
```

`include/numeric_types.inc`, `include/numeric_math.inc` and `include/numeric_evolve.inc` are shared between CPU and GLSL. The fingerprint also covers all seven entry points plus `shaders/operator_texture.inc` and `shaders/evolution_pass.inc`. Regenerate SPIR-V after editing these inputs. CMake checks their fingerprint against the bundled shader fingerprint and rejects stale embedded equations. A shader compiler, `spirv-opt`, and preferably `spirv-val` must be on PATH for the shown generation command; retained function/loop hints reduce offline expansion but cannot require every device compiler to preserve those boundaries.

To request the installed desktop Vulkan validation layer, set `DAWNWOOD_VALIDATION=1`. The runtime errors when the layer is requested but absent. Keep validation stderr with the report. For a headless software test use `--allow-software` and retain its actual device identity.

To inspect the same staged evolution schedule on the GTX with an installed Vulkan layer, use a fresh PowerShell process or remove the temporary overrides afterward:

```powershell
$env:DAWNWOOD_SPLIT_EVOLUTION = '1'
$env:DAWNWOOD_VALIDATION = '1'
$env:VK_LAYER_VALIDATE_SYNC = '1'
build\Release\dawnwood.exe verify --device "1650 Ti" --count 257 --steps 1024
build\Release\dawnwood.exe verify --device "1650 Ti" --count 65537 --steps 4
Remove-Item Env:DAWNWOOD_SPLIT_EVOLUTION, Env:DAWNWOOD_VALIDATION, Env:VK_LAYER_VALIDATE_SYNC
```

If the layer is in a nonstandard directory, set `VK_LAYER_PATH` to that actual installed directory as well. A desktop staged-path pass does not establish Mali execution or phone validation-layer coverage; retain both devices' actual reports.
