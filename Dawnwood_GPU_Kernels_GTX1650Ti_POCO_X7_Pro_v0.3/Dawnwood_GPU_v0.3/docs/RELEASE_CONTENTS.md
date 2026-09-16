# Dawnwood GPU kernels — release contents

**Tom Klootwijk / Dawnwood Interactive**  
Identifier: **NL200678942** · Date of birth: **10-07-1990** · Telephone: **+31655954068**

The target configurations are the owner's **GTX 1650 Ti laptop with 4 GB VRAM** and **POCO X7 Pro with 12 GB shared system RAM**. Device discovery, rather than these labels, supplies the executable's actual capabilities and memory budget.

## The executable definition

This release implements the declared **DWI-N1 numerical profile**. Read `NUMERICAL_PROFILE.md` beside the original PDF: it identifies the source relationship behind each numerical binding. The source's changed operator bodies, situated fields, pinion transport, BST route, RK4/Y-up event, phase/history and inverse-T return stay in one recurrent numerical state. CPU and Vulkan evaluate shared numerical source code.

The desktop implementation uses Vulkan compute. The phone application packages the same native implementation through the Android NDK/JNI and provides device, CPU-test, CPU/GPU-comparison and run commands. Its optional downstream output is separate from the recurrent numerical input.

## What is shipped

* `include/`, `src/`, `shaders/`: numerical C++/GLSL operators, mutable records, CPU reference, Vulkan dispatches and shader build tooling.
* `android/`: native Android application, Java launcher, JNI bridge and reproducible Gradle/NDK settings.
* `tests/`, `tools/`, `scripts/`: numerical and source-claim checks, checkpoint tools, downstream readout, device tests and packing calculations.
* `docs/`, `profiles/`, `source/`: equations, source page mapping, claim matrix, target profiles and the supplied source material.
* `results/`: commands and outputs from release preparation. Read `STATUS.md` and `release_status.json` for the actual result of each stage.
* `bin/`: only binaries successfully produced during preparation; an absent target binary is not represented as a successful build.

`CLAIMS.md` distinguishes numerical checks, counterexamples to stronger interpretations, measured device quantities and claims requiring experimental data or a constructive proof. A successful compiled shader, software Vulkan run, or CPU test is not recorded as an actual NVIDIA or POCO execution.

## Start

Read `BUILD_AND_RUN.md`, then build the desktop executable or Android APK as described there. The GTX scripts deliberately select a device whose name contains `1650 Ti` and do not permit a software device fallback. `tools/test_phone.py` executes the Android application through an authorized ADB connection and retains the phone's actual reports.

The complete source and the supplied personal details are included in this archive. SHA-256 hashes verify file identity; they are not a signature or ownership registration.
