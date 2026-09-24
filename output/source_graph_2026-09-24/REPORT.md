# Complete source-graph execution — 24 September 2026

**Both mutation and the full eight-stage application now execute from a named, typed source graph.** The graph owns the current-record calls, arguments, helpers, old-state reads and all returned record/state values. Numerical body laws and initial banks retain their explicit source bindings. The unchanged resident CPU/Vulkan interpreter executes the generated program.

The [aggregate](FINAL_SUMMARY.json) records 51 paired workloads: 49 healthy pairs and two deliberate failure pairs, with 5,902,446 compared mutable words and identical complete CPU/GPU checkpoints. The additional saturation population is counted separately.

The [source contract and commands](../../docs/SOURCE_GRAPH_PROGRAM.md) explain the representation. The [requirements audit](../../docs/SOURCE_GRAPH_REQUIREMENTS.md) maps it to the original documents and executable application. This is a bounded numerical implementation of those relationships; open source laws are identified as authored choices.

## Use it locally

From the repository directory, with a fresh output directory:

```powershell
.\Dawnwood-Graph.cmd compile --graph source_bindings/graphs/enzyme_v0.1.json --enzyme-inputs source_bindings/examples/enzyme_inputs.json --output output/my_graph_enzyme
.\Dawnwood-Graph.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 128 --input output/my_graph_enzyme/program.bin --output output/my_graph_enzyme/gpu128.bin
.\Dawnwood-Graph.cmd results output/my_graph_enzyme/gpu128.bin --manifest output/my_graph_enzyme/manifest.json --output output/my_graph_enzyme/results.json
```

The [actual launcher campaign](cli/summary.json) exercised compilation, CPU and Vulkan execution, inspection and result export. Its eight-input [readout](cli/enzyme/results.json) reports actual concentrations, conservation residuals, strategy and gap estimates. All eight cases are feasible within the declared `1e-5` normalized tolerance; some gap estimates remain above the requested threshold. The exporter does not repair returned states. A checkpoint is a valid input for continued execution.

The useful biochemical task is reconciling candidate concentrations with the two conserved pools of the supplied closed enzyme model. The [scientific derivation](../../docs/ENZYME_POOL_DOMAIN_GROUNDING.md) defines assumptions, units and the intrinsic SDF metric. It is not a kinetic or biological prediction. The existing [amplitude-budget source model](../../source_bindings/examples/amplitude_budget_model.json), compiled with the amplitude graph, supplies a separate Euclidean amplitude constraint. Other [domain field definitions](../../docs/DOMAIN_FIELDS.md) retain their documented CPU/D1 scopes; this report does not imply that every catalogue item has become a resident graph application.

## Source ownership and migration equivalence

The compiler reads the supplied graph after the source authoring builder has initialized numerical banks and state. It replaces both final tapes. Authors name values and current records; register numbers are allocated by the compiler. The exporter is an offline migration utility and is not invoked by graph compilation.

The [default campaign](summary.json) contains **22 healthy CPU/GPU pairs**, **2,293,362 compared mutable words** and **629,649 committed instance-epochs per backend**. Entire paired checkpoints match exactly, with Vulkan validation enabled and zero errors or warnings.

Four editions were compared with their earlier execution evidence: core, enzyme, amplitude extension and authored Hadamard. All 16 epoch-specific comparisons reproduce complete mutable instance images, including current operator records. Their static tapes differ because graph lowering uses a new register layout. Core, enzyme and amplitude also pass exact resumed and reversed-target-order comparisons.

The [compiler audit](compiler_rejections.json) passes **48 cases**, comprising 41 atomic rejections and seven valid compilations. It exercises malformed references, wrong nominal types/arguments/banks, missing returns, unsupported expressions, guarded unused results, function/plan limits and register pressure. A valid graph reaches 172 of 192 value registers; overflow rejects without changing the caller's definition. Four profiles still compile identically after the original tapes and call-site metadata are replaced with invalid objects. This directly checks independence from the previous tape construction.

The independent [structural audit](fidelity_audit/results.json) rejects all 18 deliberately broken source dependencies and accepts four positive controls. It checks common-old mutation, old/current K use, stage order, PHI/RK/Y-up/history paths, authoring retention and enzyme feedback. Structural ancestry cannot establish that a callee is numerically sensitive to every argument; the following experiments supply separate behavioral evidence.

## Graph edits and delayed self-change

The [intervention campaign](interventions.json) adds **17 healthy pairs**, **1,754,142 compared words** and **84,108 instance-epochs per backend**. Existing numerical functions, body families, initial records and initial states remain identical to their corresponding baselines. Only graph wiring and explicitly added graph helpers change.

| Graph edit | Recorded effect |
|---|---|
| Add a phase bias before current double Hadamard | Changes returned waves in all 129 instances at 1, 2 and 64 epochs. |
| Exchange two growth-channel arguments entering double-dot coupling | Changes returned waves in all 129 instances at 1, 2 and 64 epochs. |
| Bias the old mutator's evaluated carrier-distance input | Changes resident record images; all state values remain unchanged through the measured 64 epochs. This null state result is retained. |
| Halve the current resident chemical proposal displacement | Changes chemical proposals and returned compositions while core wave values remain unchanged through 128 epochs in this comparison. |
| Identity controls for all four edits | Reproduce every mutable instance word of the original graph after 64 epochs. |

The conservative chemical proposal retains the protected scientific laws. All 129 cases remain feasible within `1e-5` normalized concentration tolerance. Against an independent exact rational active-set projection of packed observations, its [maximum species error after 128 epochs](conservative_enzyme_accuracy.json) is **9.0303e-4 normalized**, versus approximately `4.337e-4` for the default proposal. This graph edit demonstrates source-owned composition; it is not an optimization improvement.

The separate [self-change experiment](self_change.json) adds four healthy pairs and 420,024 compared words. A source helper retains only the mutator's own old body handle while leaving every other proposed record value and every existing numerical function intact. The first epoch's state is unchanged. At epoch two, **129/129 wave states**, **81/129 accepted intrinsic coordinates**, and **80/129 decoded physical compositions** differ. FP32 decoding makes the last two counts distinct. The identity helper reproduces the full baseline mutable images at epoch 64. This demonstrates delayed execution of a changed resident definition through the new graph path.

## Heterogeneous routed application

The [matrix audit](matrix_audit/REPORT.md) executes actual current BST routes to source **19, T**, and **18, inverse T**. Each route supplies its selected record's anchor, placement, field and typed body. The source graph then applies the returned inverse to the complex R/G channels before the existing pinion/return.

Seven CPU/GPU pairs over 257 varied instances produce identical checkpoints. Five pairs are healthy, including full applications at 1, 8 and 64 epochs and a diagnostic capture; two deliberately wrong-interface pairs fail with status 11 and restore every old state/record word. The diagnostic is a one-epoch instrumented observation, not a valid application continuation.

Independent binary64 calculations meet the predeclared `1e-6` bounds. Maximum entry error in `T A − I` is `1.0735e-7`; the added complex-pair map has maximum scaled error `5.7429e-8`. Both inverse branches execute. All 257 returned pairs change relative to the unconditioned graph.

The existing pinion already applies A. This example deliberately applies A one extra time; no conditioning improvement or new physical capability is inferred from its name. Its demonstrated capability is typed source composition of heterogeneous routed procedures, without converting their interfaces into a generic wave-only adapter.

## Laptop compute saturation

The [new graph-specific saturation run](saturation/summary.json) executes **33,024 instances × 2,048 epochs = 67,633,152 complete instance-cycles**. The population repeats 129 independently CPU-executed templates 256 times. All **26,881,536 mutable words** match their CPU references, and the static configuration remains unchanged. These are independent replicas for hardware load, not 33,024 distinct scientific initial cases.

| Measurement | Result |
|---|---:|
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop GPU |
| Submit-to-fence execution time | 54.0001555 seconds |
| Telemetry samples at 100% GPU / total | 101 / 117 |
| Peak temperature | 71°C |
| Peak recorded power | 120.76 W |
| Peak recorded device memory used | 401 MiB |
| Two mutable state buffers | 215,052,288 bytes |
| Per-epoch host reads / uploads | 0 / 0 |
| Validation errors / warnings | 0 / 0 |
| CPU-reference word differences | 0 |

The timer excludes setup, command recording and readback. This is compute saturation, not a maximum VRAM-capacity measurement or a demonstrated application speed advantage. Compressed complete input/output checkpoints retain their uncompressed hashes.

## Provenance and reproducibility

The [final recompilation audit](final_recompilation_audit.json) connects current compiler sources to the exact executed binary programs. Earlier archived definitions preserve their construction-time hashes. A final metadata correction replaces inherited builder step positions with graph node/call mappings, and the public manifest now explicitly declares the lowered complete application. These changes leave executable bytes unchanged; the current CLI output contains the corrected metadata.

Each case retains its actual model, graph and program. Large definition/manifest JSON files use lossless `.xz` archives with byte counts and SHA256 values in `compilation.json`. Scripts and their dependencies are retained under [experiments](experiments); compiler/schema and matrix audits also retain their own scripts and receipts. No persistent test suite was added.

Two harness issues are retained rather than counted as successful runs: the matrix audit's first Vulkan launch lacked its layer search path, and the CLI harness initially supplied a Vulkan-only device argument to CPU mode. Both were corrected before successful paired execution. The self-change harness also corrected an expected physical-composition count that had been taken from the distinct intrinsic-coordinate count; the actual checkpoints were already correct.

The native executable and shader are unchanged from the earlier resident edition. Source relationships, numerical binding choices, structural checks, observed numerical effects and hardware measurements remain separately inspectable. The results establish this finite headless implementation; unrestricted runtime program synthesis, empirical biochemical validity, general intelligence and physical quantum computation are not established.
