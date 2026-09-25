# Native queries against a retained constructed SDF

The public headless workflow evaluated all **900 held-out resource requests** against the three-leaf SDF retained in parent lane 0 at epoch 8. The CPU and Vulkan results are identical across the entire checkpoint. All 900 requests were admitted and passed the independent results reader. The maximum observed query-distance error was **0** against the separate rational-edge oracle, below the previously declared absolute threshold `1e-5`. These queries lie inside the admitted boxes; this observation is not a global FP32 error bound.

The [summary](summary.json) records the measurements. The [commands](commands.json), [executable/shader snapshots](runtime/), [source snapshots](sources/) and [direct experiment text](experiment.txt) retain the execution provenance. The [full independent readout](results.json.xz) is losslessly archived; [archive receipts](archive_receipts.json) retain its original byte hash and size.

## Public workflow and reproducibility

`Dawnwood-Develop.cmd compile --instances 3` produced the expected default input SHA256 `c3af6851c99c3d1fb4285fedf14d6f45bfb18c096822d8ea92b09981c4daab90` in a fresh temporary directory. Public `inspect` validated that small compiled image with its manifest.

Public `prepare` then cloned the complete retained parent instance for the 900 pairs in the previously frozen holdout dataset. It changed only the population count, each lane's query coordinates, and `resource_enabled=0`. Every parent record, program word, header/epoch and other state word was copied exactly. Static bytes after the count word were unchanged. This is an explicitly forked population, not ordinary checkpoint resume.

Public `run` executed one complete source epoch on CPU and one on **NVIDIA GeForce RTX 5070 Ti Laptop GPU**. Public `results` read the Vulkan output using distance tolerance `1e-5` and score tolerance `2e-5`. Both native calls and all public CLI commands returned 0. Vulkan validation was enabled with **0 errors and 0 warnings**. There was one dispatch/submission and no per-epoch host read or upload. This small correctness pair is not a saturation or throughput benchmark.

| Check | Actual result |
|---|---:|
| Query population |900 lanes |
| Complete checkpoint bytes compared |3,317,804 |
| Mutable instance words compared |786,600 |
| CPU/Vulkan byte differences |0 |
| Prepared fresh answers |0 |
| Executed fresh answers |900 |
| Final epoch |9 for every lane |
| Independently valid/admitted queries |900/900 |
| Ambiguous admission classifications at requested tolerance |0 |
| New construction acceptances |0 |
| Retained AST |5 nodes, 3 leaves, revision 2 |
| Retained program-word differences per lane |0 of 40 |

The query-population manifest explicitly requires epoch 9 before new diagnostics are fresh. Host readout of the prepared epoch 8 image reported 0 fresh answers. After the native epoch it reported 900. Old distances were never relabeled as answers to new queries.

## What stayed fixed and what evolved

The generated SDF's **complete 40-word representation**—header controls, node opcodes, child references and box constants—stayed byte-identical to the parent in every lane. The immutable bank/configuration stayed unchanged during native execution. `resource_enabled` remained 0, so no new program was accepted.

The source recurrence still ran. All 32 records advanced their generation once; their anchors, control, radius and recorded mutation/pinion field values changed, and 31 placement handles changed. Body and carrier-field handles remained unchanged. These are ordinary resident record updates, not changes to the constructed resource-SDF AST. The complete record tables were identical across query lanes because all lanes inherited the same parent context. [Per-record before/after words](normal_record_evolution.json) make these changes inspectable. The [preparation changes](preparation_changes.json) separately identify the only input-state edits.

## Scope

The input checkpoint and program identities were frozen before the holdout dataset was generated; copied [freeze](holdout_freeze_receipt.json) and [dataset receipts](holdout_dataset_receipt.json) retain that ordering. This native run uses parent lane 0 only. The earlier host assessment compared all three retained lane programs and a hand-authored reference; this report does not turn those other host evaluations into GPU measurements.

The useful output is the retained definition's signed distance and admission decision for a new normalized persistent/scratch-memory request. These are authored resource-preference regions under a protected quota model. They do not guarantee real device allocation success. The earlier fixed three-box reference also covers 900/900 and uses less area; this run supplies native execution evidence, not a superiority claim.

The prepared manifest and every file in its artifact index are present uncompressed with their original hashes, so the retained 900-query output can be read immediately from the repository root:

```powershell
.\Dawnwood-Develop.cmd results output/source_development_2026-09-25/native_queries/vulkan.bin --manifest output/source_development_2026-09-25/native_queries/prepared/manifest.json --distance-tolerance 0.00001 --score-tolerance 0.00002 --output output/source_development_2026-09-25/native_queries/replayed-results.json
```

`replayed-results.json` must be a new file. Full readout and inspection JSON were losslessly archived; compression receipts retain original hashes. The parent checkpoint, prepared input, CPU output and Vulkan output remain raw binaries.
