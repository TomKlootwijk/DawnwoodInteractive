# Typed resident runtime and PHI arithmetic — 24 September 2026

Profile **DWI-RESIDENT-0.2**, checkpoint **DWRD0002**, physical NVIDIA GeForce RTX 5070 Ti Laptop GPU. This campaign verifies execution mechanisms required by the source cycle. It does not itself verify a complete eight-stage application or a domain specialization.

The source applies different typed roles through the same current record: pinion transports anchors during old-snapshot mutation and carries the returned payload later; RK4 has stage and gather roles. V2 represents these as one mutable body-family handle with an immutable interface. Computed routes resolve actual source indices, never modulo aliases. See the [ABI](../../docs/RESIDENT_V2_ABI.md) and [arithmetic contract](../../docs/SOURCE_MATH_V2.md).

## Recorded results

- Four paired compatibility workloads, 17 independent instances each: one epoch, eight epochs, reversed eight-epoch target traversal, and checkpoint continuation 1+7. CPU/GPU checkpoint bytes agree in every run. Reverse traversal and continuation match uninterrupted execution exactly. The eight-epoch mutable images also equal the previously verified v1 images, including state, body handles, anchors, generations and headers.
- Four paired dispatch workloads, seven instances each. A resident family replacement changes role7 from multiplication to addition and back; both old and new table reads report the appropriate body. An intentionally failing unused role is not executed. Missing typed role, absent source index and invalid computed index produce statuses11,10,9. Explicitly invoking the failing role produces XIR failure in both old-snapshot mutation and new-table action. Every failure rolls back all state/record words; already failed images remain frozen on continuation.
- One paired arithmetic workload, 27,240 instances: 27,220 valid log/atan2 evaluations and 20 intended domain failures. Complete CPU/GPU checkpoints are byte-identical, including 394 representable subnormal angle outputs and eight signed-axis cases. All 20 failures preserve the preceding state and record. Independent binary64 comparisons report maximum absolute errors `3.8369313273e-6` for log and `2.5758752908e-7` for atan2, with maximum distances of one and two FP32 ULP respectively in this device sample.
- A separate direct CPU sweep covered 12,485,252 logarithms and 18,001,604 angle pairs, with maximum observed two-ULP differences from the binary64 references rounded to FP32. This is sampled accuracy, not an exhaustive correct-rounding proof.
- 18 malformed frontend definitions were rejected. 59 malformed binaries were rejected by both the Python checkpoint decoder and native CPU loader; a valid control was accepted. The cases cover family contracts, role tables, source identities, handles, instruction bounds, initialized reads, reserved words and failure-header consistency.

All recorded Vulkan runs enable validation and report **zero errors and zero warnings**. GPU buffers report device-local allocation, with no per-epoch host reads or uploads. This establishes the explicit runtime transfer pattern, not permanent cache residence or zero physical bus traffic. These are correctness workloads, not a saturation or throughput result.

The dispatch fixtures intentionally isolate generic machine behavior. They are not source-faithful applications merely because their record identities use the source catalogue. Application fidelity additionally requires the authored cycle, situated calls and causal evidence.

## Evidence and reproduction

The [runtime summary](runtime_summary.json), [failure audit](dispatch_failure_audit.json), [frontend rejections](rejections/frontend.json), [binary rejections](rejections/binary/summary.json) and `math/` retain definitions, inputs, complete outputs, commands, exit codes, raw logs and comparison receipts. Exit3 means the recorded intentional instance failures; exit2 means rejected malformed input. Neither is relabeled a healthy computation.

The final [build receipt](../../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/bin/windows-resident-v2/build.json) records all source hashes and three successful commands: GLSL compilation, SPIR-V validation and C++ compilation. All three final build stderr files are empty.

```text
Executable SHA256 d6e08b44edf484571ad5d49954a8b3797c71e5bfc80ec4ce8cde795e8d865d29
Shader     SHA256 9e90c89135a93a115db1ceaea5475338a389f8ab41ab7e64165751d4410f6098
```

For example, run `Dawnwood-Resident2.cmd run --input output/source_cycle_2026-09-24/compatibility/program.bin --output output/my_v2.bin --backend vulkan --device "RTX 5070 Ti" --epochs 8`, then inspect using its retained manifest. Use a distinct output path. Frozen v1 artifacts and original source-workbench files remain unchanged.
