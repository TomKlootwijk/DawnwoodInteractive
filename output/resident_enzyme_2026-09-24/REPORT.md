# Resident enzyme application — 24 September 2026

**DWI-ENZYME-0.1 now performs a useful numerical task through the authored source architecture:** reconcile candidate enzyme, substrate, complex and product concentrations with two supplied conserved pools. Proposal, chemical SDF, projection, acceptance and feedback are executable resident definitions. The complete eight-stage core supplies their current wave, history, inverse and situated carrier context. The next old-snapshot mutation consumes application feedback and chooses the next proposal definition.

The [source fidelity audit](SOURCE_FIDELITY_AUDIT.md) traces those connections to the original application and current code. The [binding contract](../../docs/RESIDENT_ENZYME_BINDING.md) identifies all authored numerical choices; the [scientific grounding](../../docs/ENZYME_POOL_DOMAIN_GROUNDING.md) gives primary biochemical sources and the metric derivation. This is a finite numerical specialization of the source relationships, not a claim that the PDFs uniquely supplied these biochemical equations.

## Useful output and reproduction

Use the command line from the repository directory:

```powershell
.\Dawnwood-Enzyme.cmd compile --inputs source_bindings/examples/enzyme_inputs.json --output output/my_enzyme
.\Dawnwood-Enzyme.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 128 --input output/my_enzyme/program.bin --output output/my_enzyme/gpu128.bin
.\Dawnwood-Enzyme.cmd results output/my_enzyme/gpu128.bin --manifest output/my_enzyme/manifest.json --output output/my_enzyme/results.json
```

The compile directory and result file must be fresh. Change the input JSON to supply observations and common pool totals, expressed in micromolar units. The actual launcher compile, both execution backends and result export were exercised; [the eight-input demo](demo/results.json) contains their returned results. The exporter reads the checkpoint and calculates diagnostics; it does not repair its outputs or substitute a reference solution. A checkpoint can be passed directly into another `run` invocation.

For example, observations `(E,S,ES,P)=(8,78,3,20)` with totals `(10,100)` return approximately `(7.600001,77.800003,2.399999,19.799997)` micromolar. The returned enzyme-pool residual is zero and substrate-pool residual is about `−9.54e-7` micromolar. These are synthetic demonstration inputs, not experimental evidence about a biological sample.

This is usable as a declared-model consistency check for candidate simulator states or model-generated concentration vectors. The output includes the actual resident strategy, returned composition, residuals, correction distance and remaining FP32 gap estimate. It does not establish a reaction rate, kinetic trajectory or exact nearest composition.

## What executes inside the architecture

The application retains **31 records, 35 compatible body families, 61 expression functions and 64 state words**. Each instance has an 814-word complete mutable image, including its live definitions. Mutation and action tapes contain 95 and 1,136 instructions. All original eight-stage action instructions survive in order; application calls extend the final `surface_return` transaction after the original 44 provisional state writes.

The current `blend` record supplies typed roles for proposal, the chemical SDF and boundary witness, projection/evaluation, acceptance, and final species/gap readout. Its two strategy families reference identical scientific-law functions and differ in proposal behavior. The original carrier field remains a Klein geodesic disk. The chemical SDF is a separate resident body role in the induced conservation-plane metric; concentrations are not reinterpreted as carrier coordinates.

All four species share one concentration scale. The scientific constraints are `E+ES=E_total`, `S+ES+P=S_total`, and nonnegativity for the closed, fixed-volume reaction scheme. The coordinate transform preserves four-species Euclidean distance in exact arithmetic. Nearest-boundary and nearest-feasible witnesses are distinguished. The numeric interpreter remains generic; application-specific arithmetic is in the inspectable expression bank.

## Complete-application evidence

The [aggregate](FINAL_SUMMARY.json) records **32 paired complete-application workloads**, 4,007 returned instance observations, **3,261,698 compared instance words**, and 619,708 committed instance-epochs per backend. Every complete CPU/GPU checkpoint matches exactly. Every run is healthy and enables Vulkan validation, with zero errors and warnings. These totals exclude the independent component experiments and additional large GPU population below.

- The 129-case population includes consistent observations, all feasible corners, negative inputs and independently generated inconsistent observations. Paired runs cover 1, 2, 8, 64, 128 and 2,048 epochs. Continuation `1+127` and reversed mutation-target traversal exactly reproduce uninterrupted 128-epoch checkpoints.
- Changing a representative current body in **each of the eight source stages** changes returned concentrations in 108 of 129 cases after one epoch. Independent carrier-field and placement changes have the same affected-instance count. Inputs already projected onto the same corner need not change their accepted composition; all 129 proposal diagnostics respond.
- Forcing the fast resident strategy changes 108 accepted compositions at epoch one; the baseline initially chooses the cautious strategy. Forcing the cautious strategy changes 85 compositions by epoch eight. Protected chemical-law functions remain identical in every intervention.
- Freezing only the mutator's own successor changes no first-epoch state words and exactly 129 body-handle words. At epoch two it changes every core wave and 81 accepted compositions. This demonstrates delayed execution of resident self-change, rather than an external recompilation alone.
- Removing the chemical contribution to mutator control changes the control records but does not change core waves at the tested 8, 64 or 128 epochs. At 2,048 epochs, it changes core waves and domain diagnostics in **45 of 129 instances**. The accepted concentrations are unchanged at that point. The feedback edge is conditional and delayed; it is not a claim of a wave change on every epoch.

See [baseline runs](baseline_summary.json), [interventions](interventions_summary.json) and [the long feedback comparison](long_feedback_audit.json). Deliberate stage-body perturbations establish causal connections; they are not offered as mathematically valid replacements for the original stage equations. Ordinary declined proposals continue the epoch and controller history rather than triggering fatal rollback.

## Accuracy and limits that remain visible

Against an independent exact rational four-species projection oracle, the full 129-case run has the following sampled errors. These compare returned physical concentrations, divided by the declared scale, with the exact solution for the packed normalized observations.

| Measurement | 128 epochs | 2,048 epochs |
|---|---:|---:|
| Maximum species error, normalized | 4.337e-4 | 1.998e-4 |
| Same error at scale 10 micromolar | 0.004337 micromolar | 0.001998 micromolar |
| Maximum pool residual, normalized | 9.537e-7 | 9.537e-7 |
| Lowest returned species, normalized | −2.981e-8 | −9.537e-7 |
| Gap estimates exceeding requested 1e-5 | 51/129 | 51/129 |

All returned cases satisfy the explicitly reported feasibility tolerance of `1e-5` normalized concentration. Tiny negative values and pool residuals are retained, not clipped. The [128-epoch readout](results_128.json), [2,048-epoch readout](results_2048.json) and exact rational reference files preserve the details. More iterations do not guarantee an arbitrarily small error in this FP32 edition.

The separate [mathematical audit](math/REPORT.md) executes **3,486 direct component cases** with identical CPU/GPU checkpoints. Maximum sampled SDF error is `1.446e-6` normalized; maximum projected-species error is `9.694e-7` in its principal geometry group. Common unit scaling by powers of two reproduces normalized results exactly in the recorded cases.

The audit also exposes finite-precision limits. Hard boundary probes record 19 tiny accepted increases in the exact objective, the largest `1.4581e-8` normalized squared units. Rounded gap estimates can understate true objective excess. Therefore neither monotonic improvement nor a rigorously certified optimum is claimed. Some direct arithmetic stress fixtures exceed the application CLI's input bounds and are identified separately.

The historical [first candidate](pre_stable_acceptance/STATUS.json) used comparison of large full FP32 objectives and stalled earlier. Its complete definition and outputs are preserved separately. The final acceptance law computes the quadratic change directly, substantially reducing that cancellation while retaining the remaining boundary-rounding limits. No tolerance was loosened to conceal the result.

## Complete-application laptop saturation

The [sustained run](saturation/summary.json) executes **33,024 instances × 2,048 epochs**, or **67,633,152 complete instance-cycles**. Its population repeats 129 independently CPU-executed template cases 256 times. Every returned instance image is compared with its corresponding CPU template: **26,881,536 mutable words, zero differences**. The full static checkpoint prefix is unchanged too.

| Recorded measurement | Value |
|---|---:|
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop GPU |
| Native submit-to-fence execution timer | 55.798894 seconds |
| Telemetry samples / samples at 100% GPU | 127 / 105 |
| Highest recorded temperature | 71°C |
| Highest recorded power | 120.56 W |
| Highest recorded device memory used | 401 MiB |
| Two mutable instance buffers | 215,052,288 bytes |
| Vulkan validation errors / warnings | 0 / 0 |
| Explicit per-epoch host reads / uploads | 0 / 0 |

The timer excludes setup, command recording and readback. This measures compute saturation for the stated application, not maximum VRAM capacity, FLOPS, exclusive physical bus behavior, or an application speed advantage. CPU template timing is for 129 cases, not the repeated GPU population, so those wall times must not be compared as an acceleration ratio. No power or clock setting was changed; the monitored 90°C stop threshold was not reached.

Large input and output checkpoints are preserved losslessly as `.bin.xz` archives, with archive and uncompressed hashes. Decompression was verified. Replication is explicit; the run does not represent 33,024 distinct biochemical observations.

## Provenance and completion boundary

The final CLI [baseline bundle](baseline/manifest.json) preserves the original source model and cycle, input data, both generators, dependency snapshot, expression bank, call plans and program. Its program SHA256 is `d81a6c2fbdf0e43015664d291c23470c59e3b0277f9218773625aa74b6ea41b4`. The [source audit](SOURCE_FIDELITY_AUDIT.md) records exact code hashes. Fifty-eight malformed authoring cases were rejected with a valid control in the [rejection campaign](rejections/REPORT.md).

Early temporary experiment scripts read some model titles with the Windows default encoding. Explicit UTF-8 recompilation produces identical executed program bytes; the differing non-executable provenance metadata and original experimental copies remain disclosed in [compilation equivalence](compilation_equivalence.json) and the component audit. No result is silently assigned to different numerical instructions.

This milestone supplies a headless, resident domain application with source-linked documentation and independently checked outputs. It remains a finite program bank and a numerical approximation. Unrestricted expression synthesis, optional texture packing, other biochemical mechanisms and wider scientific validation are separate work; this result establishes no new physical law or general AI capability.
