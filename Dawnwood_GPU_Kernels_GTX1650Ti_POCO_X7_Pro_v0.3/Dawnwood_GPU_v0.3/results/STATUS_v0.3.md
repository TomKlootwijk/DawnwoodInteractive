# Actual build and test status — Dawnwood GPU 0.3

| Stage | Recorded result |
|---|---|
| SPIR-V compilation | False |
| Desktop C++ compilation | False |
| CPU CTest suite | False |
| Combined source-claim suite | False |
| Vulkan device used | No completed Vulkan probe |
| Software Vulkan device | not established |
| Every-epoch CPU/Vulkan comparison | None |
| Numerical operator-body coverage | not executed |
| Checkpoint replay | False |
| Android arm64 native compilation | False |
| Android APK build | False |
| Actual GTX 1650 Ti test | False |
| Actual POCO X7 Pro test | Not executed in this environment |

No installed Android SDK/NDK toolchain found in this build environment.

False means the stage was not successfully completed; consult the corresponding command record and stderr to distinguish an unavailable toolchain from a failed test. Nothing is promoted from compiled to device-tested.

The full command/exit-code record is `build_commands.json`. Numerical claim evidence is under `claims/`. `CLAIMS.md` distinguishes numerical fixtures, counterexamples, hardware measurements and physical/formal evidence still to be supplied.
