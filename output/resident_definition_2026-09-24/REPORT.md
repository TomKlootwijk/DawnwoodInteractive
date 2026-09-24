# Resident executable definitions, 24 September 2026

**DWI-RESIDENT-0.1 now executes numerical definition changes on the RTX laptop.** The old situated mutator selects new executable bodies, including its own successor; the old situated pinion transports recurrent anchors; field rebinding consumes the new body and anchor; subsequent action resolves the complete new record table. This is a verified, finite **three-record component**, not the complete source application.

The [binding contract](../../docs/RESIDENT_DEFINITIONS.md) states the exact source relationships and authored numerical choices. The [ABI](../../docs/RESIDENT_ABI.md) defines the interpreter and checkpoint. Fifteen validated bank functions and explicit 92-step mutation / 57-step action plans implement the selected Hadamard, pinion and mutation records. Each lane has an independent LUT and component state. This differs from a wavefront population sharing one common field.

## What was observed

The [causal and transaction audit](causal_and_transaction_audit.json) consolidates the initial baseline and [29 further paired workloads](execution_summary.json): **30 CPU/GPU pairs, 737 returned instance observations, 69,278 mutable instance words and 34,800 committed instance epochs**. Every complete checkpoint is byte-identical between CPU and Vulkan, including programs, handles, numerical values and failure records. Counts include repeated checkpoints and intentionally failing instances; they do not represent 737 distinct substrates.

The successful population workload executes **257 independent instances for 128 epochs**, crossing the driver's 64-epoch submission boundary. It commits all 32,896 instance epochs with no failed lane. These are correctness runs, not full-device saturation measurements.

| Evidence | Observed result |
|---|---|
| Baseline delayed self-change | Bodies `(hinge,pinion,mutator)` change from `(4,8,6)` to `(4,8,7)` after epoch 1, then `(5,9,7)` after epoch 2. The new pinion first toggles placement handles at epoch 3. |
| Freeze only the mutator's self-change | Epoch-1 numerical state is identical; only the 17 mutator handles differ. Epoch 2 changes acting hinge bodies and state in all 17 instances, while anchor values still match. |
| Change the acted hinge expression | Negating returned `ai` changes epoch-1 waves with no record-table differences. Those returned values change the next hinge selection in 13/17 instances. |
| Equal energy, opposite imaginary amplitude | Both input sets have energy 0.75; all 17 positive/negative pairs select different hinge definitions. |
| Change old pinion, target field or target placement | Each intervention changes the subsequent numerical state in all 17 instances. |
| Reverse mutation target traversal | The eight-epoch checkpoint is byte-identical to normal traversal. |
| Continue a checkpoint | One epoch plus seven resumed epochs equals eight uninterrupted epochs, including the bank and live definitions. |

The [independent mathematical audit](independent_mathematical_audit.json) checks 51 one-epoch transitions from actual preceding FP32 checkpoints. Expected values use binary64 equations, a wider 7×7 Klein deck enumeration and a closed complex two-Hadamard matrix; the reference does not execute the bytecode or call plans. Maximum state error is **7.475227148390218e-8**; maximum record-value error is **5.952283854693263e-8**, below the declared `1e-6` comparison limit. Handle and generation mismatches are zero. These are sampled numerical results, not universal error bounds.

## Failure and boundary evidence

The 123 expected failed-instance observations include 17 already-failed instances replayed from a checkpoint. Executable failure cases cover fractional handles, out-of-range handles, signature mismatches, wrong generations, invalid jitter, nonpositive interval, epoch/generation limits, an action-stage field failure and a call-plan requirement failure. All failed epochs preserve the previous state and record words exactly; only their failure header changes. Other instances continue. An already-failed checkpoint remains frozen.

The action-stage radius failure is significant: provisional body changes and anchor transport occur first, then a zero-radius field fails. The resulting checkpoint restores even those preceding provisional changes. Failed XIR output rows are never committed as valid definitions.

[Additional boundary observations](boundary_semantics.json) verify orientation-relative vertical transport, both Klein seam directions, overlap-safe frame copying, epoch reads and the plan requirement opcode. The two opposite-orientation anchors move equally in `u` and oppositely in `v`; positive and negative seam crossings both flip orientation. These observations do not establish general smooth tangent covariance for every authored field.

Both loaders reject all [27 malformed binary cases](rejections/binary_rejections.json) before creating output. [Ten frontend cases](rejections/frontend_rejections.json) additionally reject changed source slots without matching bindings, missing assertions, incompatible overrides and malformed definitions. This is finite input-validation coverage, not an exhaustive proof.

## Device and artifact identity

Every paired GPU receipt identifies **NVIDIA GeForce RTX 5070 Ti Laptop GPU**, reports Khronos validation enabled, and records zero validation errors or warnings. All three allocated buffers are reported device-local on this laptop. Explicit per-epoch host reads/uploads are zero; the programs and instances upload once, then GPU dispatches exchange old/next buffers. This does not assert permanent cache residency or zero hardware bus traffic.

- Executable SHA-256: `dacc7de006822bcd37f11efe3afe473336038bf53f3f41d5525cd250d3ba4938`.
- SPIR-V SHA-256: `8f1d917f22b0d92f9544019366087df56aa2b089e68a87ce3f0fc8678dd5a2bb`.
- Baseline complete input SHA-256: `3b95b2b75cbbedbf3aa58bb8b24654665af5665ba0f1cdfa9a33c52f177bb47f`.

The native build record retains exact commands, source hashes and logs. Compilation and SPIR-V validation succeeded. The compiler reports one unused `phase` parameter warning in the shared plan interpreter; no warning is hidden or counted as a numerical failure. Existing numerical profiles and source workbench files remain separate.

GPU `execution_seconds` sums host submit-to-fence waits and excludes setup, command recording and readback. It is not a GPU timestamp or a speedup measurement. The [final binding audit](final_binding_audit.json) proves that final descriptive-metadata updates compile to the identical executed input. The [launcher audit](launcher_audit.json) exercises compile/run/inspect and reproduces the two-epoch checkpoint exactly.

## Run and continue

From the repository root, use a fresh output directory:

```powershell
.\Dawnwood-Resident.cmd compile --definition source_bindings/resident_v0.1.json --output output/my_resident
.\Dawnwood-Resident.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_resident/program.bin --output output/my_resident/after_8.bin --epochs 8
.\Dawnwood-Resident.cmd inspect output/my_resident/after_8.bin --manifest output/my_resident/manifest.json
.\Dawnwood-Resident.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_resident/after_8.bin --output output/my_resident/after_16.bin --epochs 8
```

Use `--backend cpu` without `--device` for CPU execution. Validation runs set `DAWNWOOD_VALIDATION=1` and `VK_LAYER_PATH` to the cached Vulkan SDK's `Bin` directory. Native execution replaces its named result file; keep distinct filenames for comparisons. No new test files were introduced; evidence comes from direct experiments and existing validation tools, following repository instructions.

## Completion boundary

This runtime selects among authored immutable expressions; it does not synthesize arbitrary instructions or grow the catalogue. Its component state carries a complex pair, chart context and one preceding-pair history, not the complete source RGBA/history/inverse state. The source `cycle.json` is not consumed. The full catalogue, PHI, split/parity, typed dynamic routing, dependent RK4 with double fourth-slot Y-up, primitives/divergence/coupling, inverse/history and complete surface return remain to be integrated and measured. No completed biochemical or futuristic AI application is inferred from these component results.
