# DWI-RESIDENT-0.3 execution contract

This isolated version raises the maximum per-instance state width from 64 to **128 FP32 words**. It preserves the numerical equations, typed function/family dispatch, plan instruction set, old-snapshot record mutation, and whole-epoch transaction of [DWI-RESIDENT-0.2](RESIDENT_V2_ABI.md). The v2 files and binaries remain unchanged.

The magic is `DWRD0003`. A v2 loader must reject this version, and a v3 loader must reject a v2 file. Recompilation or an explicit, separately validated conversion is required; changing a file's version is not ordinary checkpoint continuation.

## Layout and independent limits

The eight header words remain:

`count, recordCount, stateWidth, functionCount, heapWords, mutationSteps, actionSteps, familyCount`.

Static configuration order is unchanged: record metadata, six-word XIR function descriptors, four-word family descriptors, immutable heap, mutation tape, action tape. Each mutable instance image contains `6 + stateWidth + 24*recordCount` words, with the same failure header, state words, and resident records. `stateWidth` is now 1..128. All computed offsets and storage sizes remain checked.

| Resource | Limit |
|---|---:|
| Per-instance state | 128 FP32 words |
| Per-call XIR inputs | 64 FP32 values |
| Per-call XIR outputs | 32 FP32 values |
| XIR instructions per function | 256 |
| Plan frame | 256 FP32 registers |
| Resident records | 32 |
| Functions / body families | 256 each |
| Methods per family | 32 |
| Instructions per mutation/action tape | 4096 each |

`MAX_STATES=128` is independent of XIR's `MAX_INPUTS=64`. The native exactly-once output-coverage checker has 128 entries; its frame-initialization checker remains 256 entries. The function operand limits and shared FP32 arithmetic are unchanged.

## Execution and program data

All v2 plan and XIR opcodes retain their meanings. Configuration is read-only during execution. Only instance record/state images can change. A source binding may place a bounded expression representation in named state words and have a resident operator interpret it. This capacity extension alone does not supply a grammar, constructor, SDF proof, task objective, or newly synthesized expression; those require a separate explicit application binding and evidence.

Such program data is checkpointed and rolled back as ordinary state. State reads still access the old instance; current action results use frame references. Every action writes every state field exactly once. Record mutation remains a common-old-snapshot operation before action. The runtime does not silently permit mutation instructions to write action state or configuration.

The entire old image is restored if any mutation or action call fails. Failure statuses, typed lookup validation, generation limits, failed-image freezing, and resume semantics are identical to v2. Vulkan continues to use one immutable configuration buffer and two alternating complete instance buffers, with dependencies between epochs and no per-epoch host upload or readback.

## Implementation and evidence

The Python API remains `compile_definition(model, definition)`, `decode_checkpoint(raw)`, `read_checkpoint(path)`, `inspect_checkpoint(path, manifest_path=None)`, and `write_compilation(...)`, now in [source_resident_v3.py](../local_lab/source_resident_v3.py). `PROFILE` is `DWI-RESIDENT-0.3`; `MAGIC` is `DWRD0003`.

The separate [build tool](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/tools/build_resident_v3.py) creates `bin/windows-resident-v3/dawnwood-resident-v3.exe` and `resident_v3.spv`. It uses the same cached toolchain, Vulkan validation workflow, disabled contraction/fast-math policy, build receipts and source-hash checks as v2. The CLI is `run --input file --output file --backend cpu|vulkan --epochs N [--device substring] [--reverse-targets]`.

Direct compatibility, 128-state continuation/rollback, version rejection and hardware results are recorded separately under `output/source_development_2026-09-25/runtime_v3`. Compilation alone is not runtime validation or evidence of a self-constructing SDF application.
