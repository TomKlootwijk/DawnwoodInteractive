# Build and run on the two target devices

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

`--batch` is the number of Ψ intervals recorded in one submission, not a reset or a truncation of the recurrence. Small batches are useful during device bring-up. Actual buffer/dispatch limits are queried; a resource failure returns an error instead of clipping values or silently changing the state count.

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

The app also has four buttons for those operations. The native runtime runs on a worker thread, not the UI thread. It uses the same two compiled Vulkan kernels as the desktop. No root access, operating-system kernel replacement, CUDA runtime, swapchain or rendering pipeline is needed.

A desktop shader build is not an APK build. An APK build is not a phone test. The archive's generated status distinguishes those stages.

## Inspect device conditions

The Vulkan report includes the actual device name/vendor, API/driver versions, storage-buffer limits, shared-memory limit, heap sizes, optional memory-budget values, BC5/EAC/ASTC sampled-format support, transfer-byte counters and timing source. Android reports additionally include actual model/ABI, system RAM availability, Android thermal status and battery temperature. Battery temperature is not labelled GPU temperature.

Initial uploads and final downloads are explicit and counted. `advance()` contains no buffer-copy commands. That source-code fact is not substituted for a PCIe bus monitor or a permanent-cache-residency measurement. Hardware counters or vendor traces can be attached to the saved report as separate evidence.

## Rebuild after editing equations

```sh
python3 tools/build_shaders.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
python3 tools/run_claims.py --binary build/dawnwood --device '1650 Ti'
```

`numeric_types.inc` and `numeric_evolve.inc` are shared between CPU and GLSL. Regenerate SPIR-V after editing either or a shader entry point. CMake checks the shared-source fingerprint against the bundled shader fingerprint; it will not quietly compile a new CPU model against stale bundled shader equations.

To request the installed desktop Vulkan validation layer, set `DAWNWOOD_VALIDATION=1`. The runtime errors when the layer is requested but absent. Keep validation stderr with the report. For a headless software test use `--allow-software` and retain its actual device identity.
