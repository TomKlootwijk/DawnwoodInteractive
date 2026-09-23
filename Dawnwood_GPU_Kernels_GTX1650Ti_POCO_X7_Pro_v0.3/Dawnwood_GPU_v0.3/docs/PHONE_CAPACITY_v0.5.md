# Android capacity procedure — v0.5

The September 23 campaign completed **14,569,792 full states for two epochs** on the connected POCO X7 Pro (2412DPC0AG, Mali-G720 MC7), with successful full readback, health and digest checks. Growth stopped at the current Android memory policy boundary, without an allocation failure or serious runtime error. This is the highest completed population under the observed policy, not the phone's absolute hardware maximum.

Separately, all 30 existing CPU fixtures passed, and CPU/GPU comparisons passed for 128 states × 16 epochs, 257 × 1,024, 4,096 × 256, and 65,537 × 4 with zero bitwise state/operator mismatches. The last case crosses the dispatch-chunk boundary. Numerical comparison evidence is under `results/v0.5/2026-09-23/phone_split` and `phone_extended`; the large capacity run itself did not perform CPU/GPU equivalence checking.

The measured APK SHA256 is `8c86dbcd791a824b1402a5561c3ef3926a8f539900d0dcdf95b1563d89726430`. Android validation layers were not enabled. Agreement is between CPU and GPU given the same initialized snapshot on the phone; native host-library initialization does not guarantee independently generated Windows/Android snapshots match.

| Final completed capacity candidate | Actual result |
|---|---:|
| Population / completed epochs | 14,569,792 / 2 |
| One full-state population payload | 1,864,933,376 bytes |
| Two GPU state-buffer payloads | 3,729,866,752 bytes |
| Total allocated Vulkan buffers and images | 3,753,000,960 bytes |
| Bounded evolution scratch / staging payload | 6,291,456 / 16,777,216 bytes |
| Summed Vulkan device timestamps, two epochs | 11.91558916 seconds |
| State updates per GPU-timed second | 2,445,500.899 |
| Android app measured work interval | 76.886 seconds |
| External launch-to-report interval | 77.546 seconds |
| Largest compute submission | 0.0411456 seconds |

GPU timing includes the two epochs' compute submissions; initialization, upload, readback and CPU health/digest processing are outside that interval. The Android work interval and external launch-to-report interval are distinct end-to-end measurements, not additional GPU timings. The recorded Vulkan allocations include scratch, staging and padded images, but do not represent all Android application, driver or system memory.

Evidence is `results/v0.5/2026-09-23/phone_capacity/summary.json`, `run_012_14569792.command.json`, and `run_012_14569792.android.json`. The full state/operator digest is `9ae99cb7c910cae5`; health reported zero nonfinite values or out-of-chart states. Before and after this candidate, Android reported `system_low_memory=false`, `android_thermal_status=0`, and battery temperature 36.6°C. These endpoint observations do not establish sustained thermal performance.

The limiting policy factor was physical shared-memory headroom, using 85% of freshly reported available RAM, a 226,492,416-byte effective reserve, staging and scratch allowances. Available RAM varied between probes; the final probe produced a smaller target than the already completed best population, ending growth. The phone exposed no Vulkan memory-budget extension. Its reported heap size was treated as a ceiling rather than free memory, and its 12 GB marketed system RAM was never treated as dedicated VRAM.

From the project directory, with Python and Android platform-tools on PATH:

```powershell
python tools/test_phone.py --serial PHONE_SERIAL --apk bin/android/Dawnwood_GPU_v0.5_debug.apk --out results/v0.5/phone_validation_NEW_RUN
python tools/measure_phone_capacity.py --serial PHONE_SERIAL --apk bin/android/Dawnwood_GPU_v0.5_debug.apk --steps 2 --budget-fraction 0.95 --reserve-mib 128 --out results/v0.5/phone_capacity_NEW_RUN
```

Replace `PHONE_SERIAL` with the authorized device identifier and `NEW_RUN` with a unique campaign label. The capacity output directory must be empty; preserve the existing evidence. Omit `--apk` to use the installed app, in which case the wrapper records package information but cannot claim the hash of an APK it did not install. The first command checks CPU/GPU agreement. The second measures how many complete states can execute under the current memory policy; it does not replace that comparison.

The app also accepts explicit ADB controls:

```powershell
adb -s PHONE_SERIAL shell am start -n nl.dawnwood.kernel/.MainActivity --ez autorun true --es command run --es run_id capacity_manual --ei count 65536 --ei steps 2 --ei batch 1 --ef budget_fraction 0.95
```

UI buttons retain batch 8 and budget fraction 0.8. ADB extras override those values only for that launch. The completed report records the forwarded native arguments, model, available and total Android RAM, low-memory flag and threshold, thermal status, and battery temperature.

The capacity wrapper:

- Starts at a bounded population and increases it only after a completed run and full-state health/readback report.
- Queries actual Android `ActivityManager.MemoryInfo` after each fresh probe. It never uses the PC's RAM to size the phone run.
- Accounts for two GPU state copies and one transient CPU snapshot on unified memory: 384 bytes per complete state at peak, plus up to 16 MiB staging, bounded evolution scratch and reserves. The effective reserve is at least Android's low-memory threshold; sizing also retains 15% of the reported available host RAM before those deductions.
- When `split_evolution=true`, requires the actual reported scratch record size and dispatch limit. The accepted build reports 96 bytes × 65,536 records, a 6 MiB maximum payload. This full bound is conservatively deducted from shared host headroom and each relevant state heap, even for smaller candidates. `evolution_scratch_policy` records these charges, the current probe allocation and the fact that allocation padding is not part of this payload allowance. Actual runtime allocations retain their reported padded sizes.
- Uses Vulkan budget information where available. A Vulkan heap size remains a capacity ceiling, not a report of free phone RAM.
- Stops growth on an app crash, timeout, failed health, or a fresh probe reporting critical thermal status or Android low memory. Thermal and low-memory checks occur between candidates, not continuously during a candidate. Ordinary allocation rejection can refine a smaller boundary.
- Retains every ADB command and its actual exit code in `adb_commands.jsonl`, atomic app reports, device identity, and logs restricted to observed app PIDs. JNI completion is explicitly labeled as a synthetic completion code rather than a native process exit status.
- Force-stops only `nl.dawnwood.kernel` between attempts and at completion.

The resulting `CAPACITY.md` and `summary.json` describe a completed population under the observed policy, not an absolute hardware maximum. Kernel timestamps exclude initialization and readback. Population capacity alone establishes neither cache residence, bandwidth saturation, occupancy, nor CPU/GPU equivalence.

Earlier monolithic builds failed during phone pipeline creation, including a Scudo native out-of-memory abort. A retry still failed with 5.59 GB of available system RAM before the probe. These failures are preserved in the September 23 campaign directories and are setup failures, not completed capacity measurements. The accepted split build resolved the observed setup failure; see `docs/PORTABLE_MATH_v0.5.md` for the source changes and the limits of that diagnosis.
