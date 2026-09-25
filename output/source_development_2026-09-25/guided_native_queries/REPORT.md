# Applying both guided definitions to fresh requests

Both frozen, resident-generated four-leaf SDFs answer **1,200/1,200 fresh requests** in native CPU and Vulkan execution. The two policies use the same held-out requests and the same parent lane, selected before this application run. Every result passes the independent distance/geometry/readout assessment. Each policy's complete CPU/Vulkan checkpoint is byte-identical.

The [machine report](REPORT.json) records checkpoint hashes and query errors. The [protocol](protocol.json) freezes inputs, lane selection, tolerances, source hashes and executable/shader hashes. The [execution receipts](execution_receipts.json) retain all four commands and their native output. The [direct experiment](experiment.txt) contains preparation, execution and independent checks; no host constructs a candidate or chooses an accepted SDF during these runs.

The initial two checkpoints were frozen in the [guidance comparison](../guidance_comparison/FROZEN_CHECKPOINTS.json) before the [new holdout dataset](../guided_holdouts/REPORT.md) was generated. Query preparation clones lane 0 of each checkpoint, changes only query coordinates and construction enablement, and requires epoch 11 before answers are fresh. The epoch-10 parent program, all other state, and every record survive preparation.

After one full native epoch, every lane has seven nodes, four leaves and revision three. All 40 program words remain identical to their corresponding parent program; there are zero new construction acceptances. The surrounding source recurrence still executes. Both Vulkan calls report the physical RTX 5070 Ti Laptop GPU, enabled validation, zero errors and zero warnings.

## Reuse the retained result

The guided checkpoint and manifest are directly usable:

```powershell
.\Dawnwood-Develop.cmd results output/source_development_2026-09-25/guided_native_queries/guided_034/vulkan.bin --manifest output/source_development_2026-09-25/guided_native_queries/guided_034/manifest.json --output output/my_guided_answers.json
```

Use `prepare` with a new JSON array of normalized request pairs to apply that definition to further requests, followed by `run --epochs 1` and `results`, as described in the [application guide](../../../docs/RESIDENT_SDF_DEVELOPMENT.md). Existing output files are preserved; choose a fresh path.

Full readouts are losslessly archived as `results.json.xz` in each policy directory, with original-byte and archive hashes in the machine report. Manifests and native checkpoints remain directly readable by the command line.

## Scope

These are 1,200 native queries for **one frozen program per policy**. The separate host holdout campaign assesses three selected programs per policy. The fixed four-box reference also covers the full dataset; this run establishes native reuse and preserves the measured policy improvement without claiming overall superiority, an allocator speedup or guaranteed physical allocation. The 42.9% improvement concerns the newly added leaf's region area, not memory consumption.
