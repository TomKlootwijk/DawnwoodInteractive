# Dawnwood v0.5 completion audit

23 September 2026. This audit checks the requested kernel validation, improvements, versioned formalization and evidence report. It does not certify that the executable implements every aspiration or physical assertion in the source discussion.

## Requirements and authoritative evidence

All project-relative paths below refer to `Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3`.

| User requirement | Evidence inspected | Assessment |
|---|---|---|
| Validate and improve the numerical kernel | Current shared arithmetic/evolution source; final raw GTX and POCO comparison traces; existing CPU fixtures and numerical operator coverage | Recorded trajectories pass at the original absolute/relative tolerances, with zero bitwise differences. Shared arithmetic corrects earlier divergence; staged ARM evolution resolves the observed phone pipeline failure. |
| Test both physical devices | Device identities and command records; all eight final comparison traces; final EXE/APK hashes | Actual GTX 1650 Ti and Mali-G720 MC7 runs completed. All requested comparison epochs are present; software Vulkan/build success was not substituted for physical execution. |
| Packed one-bit controls with full FP32 LUT parameters | `shaders/operator_texture.inc`, `include/numeric_types.inc`, runtime image creation and retained transfer observations | Actual RGBA32_UINT textures preserve the declared operator layout. Flags retain full words while individual controls use bits; distances are not reduced to one bit. |
| Measure performance and operational capacity | Raw final benchmark samples; all nine laptop and thirteen phone capacity candidates; memory policies and command records | Recomputed medians, rates, payloads and final counts match the report. Every capacity candidate completes the requested two epochs and healthy full readback. |
| Explain working, missing and unjustified claims | `docs/VALIDATION_v0.5.md`, `docs/CLAIMS.md`, formalization claim tables and retained counterexamples | Implemented mechanisms, measured trajectories, missing architecture and unsupported physical claims are distinguished. Failed and superseded candidates remain attributed to their artifacts. |
| Develop the latest supplied formalization in a new version | Unchanged original/source-copy hashes for both supplied PDFs; `docs/FORMALIZATION_v0.5.md`, `docs/CHANGES_v0.5.md`, rendered version 0.5 PDF | Versioned equations, numerical choices, LUT layout, scheduling, performance definitions and limitations are documented. The 20-page PDF was rendered and visually inspected. |
| Close phone apps before retrying | `results/v0.5/2026-09-23/phone_memory_cleanup/` before/after memory observations and stopped package list | YouTube, Facebook, Instagram and WhatsApp were stopped, followed by Android background-process cleanup. Available RAM increased by 396,964 KiB (387.66 MiB). Essential system services were retained. Compilation still failed until the staged kernel change. |
| Do not write new tests | Current repository test-source diff/status; retained existing-suite records | No new repository test sources were added for this campaign. Existing fixtures, verification commands, manual diagnostics and benchmark tools supplied evidence. |
| Deliver artifacts corresponding to measured code | Actual EXE/APK/native-library hashes; source fingerprint; all seven embedded shader payloads; complete archive manifest | Artifact identities match the measured records. Every packaged manifest entry was independently hashed; the source PDFs remain byte-identical. |

## Current measurements

| Metric | GTX 1650 Ti | POCO X7 Pro |
|---|---:|---:|
| Median device time, 4,096 states × 64 epochs | 0.157167648 s | 0.1693103924 s |
| Mean device time per whole-population epoch | 2.4557445 ms | 2.6454749 ms |
| Largest completed population, two epochs | 12,244,544 states | 14,569,792 states |

Device timings exclude setup and readback. Capacities are achieved populations under current memory policies, not absolute hardware maxima or long-duration endurance results. Full-capacity output was health-checked, not compared against a CPU reference for every record.

## Limits remain part of the result

- Numerical comparisons cover recorded inputs and horizons; they are not an all-input proof.
- The phone's Vulkan validation layer was disabled. Desktop core/synchronization validation was enabled for comparisons and reported no errors or warnings.
- Independently initialized Windows and Android runs can start with different bits because host initialization still uses native math. Cross-device replay from identical seed/configuration is not claimed.
- Correctness and phone compatibility improved at a measured performance cost. No general speed improvement is claimed.
- Mutable scalar bodies, parameters, controls and positions do not make the fixed native integrator, primitive formulas, Hadamard matrix, topology, schedule or configured tree fully self-defining.
- Physical quantum behavior, universality, permanent cache residence and automatic noise removal remain unproved or contradicted in their stated generic forms. The request to assess those claims is answered by these findings; the report does not silently promote them to implemented features.

## Audit corrections

Two stale statements in README and CLAIMS described the root status file as historical. They now identify `results/STATUS.md` as the current packaged campaign index and point to the preserved historical copy. REFERENCES now points to the current v0.5 formalization while retaining the historical lineage hash record. No numerical source, shader or executable changed during this final audit.

The package receipt is `Dawnwood_GPU_Kernels_v0.5_release.json`; the independent artifact audit is `v0.5_artifact_audit.json`. Raw evidence is retained in the release under `results/v0.5/`.
