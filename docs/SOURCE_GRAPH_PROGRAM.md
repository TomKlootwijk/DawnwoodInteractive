# Source-declared recurrent application graphs

`DWI-SOURCE-GRAPH-0.1` makes the complete numerical application wiring an editable source document. The graph declares the old-snapshot mutation of every operator, all eight action phases, and every next-record and next-state value. Its calls resolve the resident body, field and placement programs on the CPU or Vulkan GPU. The graph compiler allocates registers and builds the executable plans; authors use named values and nominal types.

The [default campaign summary](../output/source_graph_2026-09-24/summary.json) records 22 healthy paired workloads, 2,293,362 compared mutable-instance words and 629,649 instance-epochs per backend. All paired checkpoint bytes matched, validation reported zero errors and warnings, and the recorded default editions reproduced their earlier complete mutable instance images. These measurements establish the tested implementation compatibility; they do not validate every possible graph or scientific interpretation.

This document addresses the application-wiring gap identified at the end of the earlier [source-authoring requirements ledger](SOURCE_AUTHORING_REQUIREMENTS.md). That ledger describes its own completed milestone. The present graph interface adds composition of the full recurrence and typed computed calls with different argument/result shapes. The additional [intervention](../output/source_graph_2026-09-24/interventions.json), [delayed self-change](../output/source_graph_2026-09-24/self_change.json) and [routed-matrix](../output/source_graph_2026-09-24/matrix_audit/REPORT.md) campaigns now provide separate numerical evidence. The [current requirements audit](SOURCE_GRAPH_REQUIREMENTS.md) maps those results to the seven literal-application conditions and records their current completion evidence and finite limits.

## Relationship to the original architecture

Page numbers in this table are physical PDF pages. The [original discussion](../double-slit-theory.pdf), [early Formalization](../Dawnwood_Interactive_Formalization.pdf), [Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf), and preserved [symbolic application](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py) serve different purposes. A source relationship is distinguished from a numerical law chosen to execute it.

| Source obligation | Direct evidence | Graph implementation |
|---|---|---|
| The operator body, field and position are one situated, editable record. | Unified p9, equations 21–22; `kernel.py` lines 45–46, 64–79. The original user's p14, 08:23 statement connects SDF operators, the double pinion and jitter. | Named record calls retain the current selector across placement, nearest-lift query, field evaluation and body action. The record includes live handles and finite parameters. |
| Operator change uses the preceding field and state; the changing operator is itself resident. | Unified p9, equations 23–25 and the final paragraph; `kernel.py` lines 82–94. | `mutation.nodes` read the common old bank and old state, call the old mutator and old pinion, rebind the field, and return all 24 record fields. Runtime publication follows completion of all targets. |
| Selection uses implicit source identities and the current operator record. | Unified p10, equations 26–28; `kernel.py` lines 106–119. | A named `source_index` reference drives computed record reads/calls. Lookup preserves actual source indices; unsupported addresses or role signatures fail explicitly. |
| PHI, split/parity/hinge, four RK slots and the fourth-slot Y-up events remain connected. | Unified p7, equations 9–14; `kernel.py` lines 98–127 and `model/cycle.json`. | The graph states these dependencies and the configured nested Y-up count. The current numerical edition uses dependent derivative stages and the explicit RK laws documented separately. |
| Geometry, growth and coupling feed the returning stream; RGBA includes history and inverse T. | Unified p8, equations 15–19; p11, equations 29–30; `kernel.py` lines 129–149. | Six primitive values, phase differential, growth, coupling and blend lead to current crystal/RG channels, all four history components, T and its four-component inverse. |
| The next input is the whole returned state, including changed definitions. | Unified p12, equations 31–35; p13, equation 36; `kernel.py` lines 151–155 and 184–209. | Complete named returns lower into the existing epoch transaction. Checkpoints carry the bank, plans, current operator records, state and failure metadata. |
| Definitions and composition can be authored without inventing hidden meanings for unknown symbols. | Unified p12 calls its ordering editable; p16 lists open numerical bindings and shows `set_body`/`add_operator`. | Source slot bindings supply explicit program meanings; graph bindings supply explicit composition. Unknown names, unmatched declarations, incompatible contracts and missing mandatory dependencies reject. |

The original workbench constructs expression DAGs; its `step` permits symbolic extensions and its bodies can be arbitrary authoring JSON. This finite numerical profile executes a checked subset with explicit meanings. The source does not uniquely determine the flat Klein metric, phase coding, derivative, Y-up shear, mutation policy, geometry coefficients or enzyme application. Their authored equations remain in [SOURCE_CYCLE_BINDING.md](SOURCE_CYCLE_BINDING.md), [SITUATED_APPLICATION.md](SITUATED_APPLICATION.md) and the domain documents.

The graph's eight-phase ordering is the supported source edition. The compiler permits additional calls and compatible rewiring within it while enforcing mandatory source dependencies. Arbitrary replacement or reordering of all source stages requires a separately declared profile. The early Formalization p11 section 10.3 and p15 section 14.2 distinguish finite self-reference from an unrestricted self-modifying or universal machine. This implementation makes no stronger universality claim.

The original user's p12, 08:16 statement places graphics output outside the core; Unified p12 likewise makes Bayer readout optional after return. This headless application requires neither a GUI nor image/sonification output. General BC5/device packing and claims about new physical computing devices remain separate work.

## What is source-owned

The [public wrapper](../local_lab/source_graph_program.py) first uses the existing [source authoring builder](../local_lab/source_program.py) to establish the numerical function bank, typed body families, records, initial state, source-slot resolutions and any domain constants. That builder still constructs its historical plans as part of producing the initial definition. [`source_graph.apply_graph`](../local_lab/source_graph.py) then replaces **both** final plans using the supplied graph. No historical tape positions or call layout contribute to those newly lowered plans.

This boundary is deliberate: the new source document owns every call edge, helper call, mutation return and state return, while the established source/binding machinery supplies initial records and the numerical laws named by those calls. The graph may also declare additional pure expression functions with explicit typed contracts. It cannot replace an existing function merely by reusing its name.

[`source_graph_export.py`](../local_lab/source_graph_export.py) provided a migration path for the default documents. It captures existing value flow, including return values before later scratch-register reuse, and gives it stable names. It is not called by normal graph compilation. The delivered files under [`source_bindings/graphs`](../source_bindings/graphs) are the subsequent application-wiring source and can be edited directly. Re-exporting a historical plan is not required after an authored change.

The remaining responsibilities are:

| Component | Responsibility |
|---|---|
| [`source_graph_types.py`](../local_lab/source_graph_types.py) | Versioned nominal contracts for state, record fields and current-record roles. |
| [`source_graph.py`](../local_lab/source_graph.py) | Strict schema/name/type checking, ordered graph evaluation, register allocation, plan generation and source-to-instruction provenance. |
| [`source_graph_fidelity.py`](../local_lab/source_graph_fidelity.py) | Mandatory source dependency and old/current-bank audit, including retained authoring policies. |
| [`source_resident_v2.py`](../local_lab/source_resident_v2.py) and native resident v2 | Validate/execute the complete function bank and generated plans with the existing FP32, typed-call, failure and checkpoint contracts. |

## Authoring contract

A graph contains `profile`, `type_profile`, `functions`, `mutation`, `phases` and `returns`. Optional `source`, `meaning` and `status` describe provenance; they are not executable evidence. `mutation` contains ordered `nodes` and all named record returns. `phases` contains the eight named stages with their ordered nodes. Final `returns` names every state component exactly once.

The three node operations are:

| Node | Operands and effect |
|---|---|
| `read_record` | Choose a named record, current mutation target or computed source index; choose `old`/`published`; read a list of named ABI fields. |
| `call_record` | Choose the same record forms and a body/field/placement slot, bank, role and exact ordered named arguments. Execute the slot's current program. A computed body call declares a reference `contract` with record key, slot and role. |
| `call_helper` | Invoke a fixed pure bank function or graph-declared helper with exact ordered arguments. Resident body methods must use a current-record call. |

Values are explicit references:

```json
{"state":"phase"}
{"node":"phase_adjustment","output":"phase"}
{"literal":0.03125,"type":"phase"}
{"target_index":true}
```

Each object above is a separate reference form. `state` always means the preceding state. A current intermediate result must name its producer. `target_index` is available only during mutation. Node IDs and output names have separate identities, including when names contain dots. Forward references and cycles are rejected. Source operands contain no raw registers, tape opcodes or byte offsets.

Nominal types distinguish such values as `amplitude`, `phase`, `log_radius`, `interval`, `carrier_distance`, `matrix_scalar`, `history_scalar`, `domain_coordinate` and program handles even though each occupies an FP32 word. Exact matching rejects accidental wiring between them. A graph helper declares ordered input/output type maps plus a pure XIR binding with matching names. Arithmetic and optional `requires` are validated and compiled. These declarations do not prove physical units, distance exactness or the scientific meaning of user arithmetic.

All nodes execute in source order, including nodes whose outputs are unused. A guard in such a call can still fail the lane. The initial PSI call is one such retained guard evaluation in the default graph: the later selected-stage PSI result is the value used by RK4, phase differential, growth and return. Eliminating the first call as apparently dead code would change failure behavior.

## Mutation, action and return

The mutation graph runs once per record against a common old instance. It evaluates the old target placement, old mutator placement/field, old target field, and old pinion placement/field. The old mutator computes the body/control proposal. The old pinion transports the target anchor and proposes a placement handle. Rebinding consumes the old field, proposed body and anchor, old radius and old surface coordinates. All 24 fields are then returned as one record candidate.

Source-slot `preserve_program` helpers and the added-record `preserve_family`/program-retention helper remain executable graph nodes. The audit requires their actual target-index argument, old target handles, ordinary proposed handles and appropriate returned outputs. An authored model with these policies cannot silently use a graph that omits them. The policy may retain a handle while the record's coordinates, control, radius or generation evolve.

After all targets are processed, the action uses published records. It starts with the new Klein/PSI applications and follows PHI, split/parity/double Hadamard, BST/selected action, four derivative stages, configured fourth-slope Y-up events, RK combination, six geometry values, growth/coupling/blend, crystal/RG/history/T/inverse, and pinion/return. The complete state return carries old configuration/history where specified and new wave, chart, phase history, B, T, A and diagnostics where computed. Later graph helpers may transform values while keeping the required source dependencies.

Every current body application has an executed same-record placement, nearest-lift and field chain. For core bodies, the resulting field enters `field_distance`. The enzyme's protected mathematical roles have no carrier-distance argument; their situated chain is executed and checked for order/record identity, but is reported as execution-only context. It is not claimed to alter their domain equations numerically.

The enzyme graph also owns the whole application path: source-controlled proposal role100, domain SDF/witness role101, projection/evaluation role102, incumbent objective role104, acceptance role103 and final witness/gap role104. It returns all domain coordinates, observations, concentrations and diagnostics. The next old-snapshot mutation receives the previous chemical SDF/improvement/acceptance feedback. The exact domain law and finite-precision limitations remain those of the [enzyme grounding](ENZYME_POOL_DOMAIN_GROUNDING.md) and its measured application; a graph change does not itself certify a kinetic model or convergence.

Failure in mutation or action rolls back the entire epoch under [RESIDENT_V2_ABI.md](RESIDENT_V2_ABI.md). A newly selected self-mutator acts on the following epoch: every target in the current mutation pass still uses the same old controller. Graph helpers and the graph topology remain fixed during execution; resident mutation changes validated family/function handles and finite record parameters within the declared bank.

## Source-only composition examples

These examples edit JSON composition without changing the native evaluator or the Python phase builder:

| Graph | Declared change |
|---|---|
| [`phase_bias_v0.1.json`](../source_bindings/graphs/phase_bias_v0.1.json) | Adds `0.03125` radians to the computed hinge phase through a typed helper before the current double-Hadamard call. |
| [`growth_rewire_v0.1.json`](../source_bindings/graphs/growth_rewire_v0.1.json) | Exchanges the first two growth-channel references entering double-dot coupling while retaining all required growth ancestry. |
| [`mutation_bias_v0.1.json`](../source_bindings/graphs/mutation_bias_v0.1.json) | Adds `0.03125` to the evaluated old mutator carrier-distance input before body selection. This is a controller-input bias; its name does not certify a new global SDF. |
| [`conservative_enzyme_v0.1.json`](../source_bindings/graphs/conservative_enzyme_v0.1.json) | Halves the resident proposal displacement and step diagnostic before protected domain SDF/projection/acceptance/witness processing. |
| [`routed_matrix_conditioning_v0.1.json`](../source_bindings/graphs/routed_matrix_conditioning_v0.1.json) | Uses current BST calls to obtain source indices 19 and 18, dynamically applies current T and inverse-T role0, then applies the resulting real 2×2 inverse to both real and imaginary R/G components before pinion/return. |

The matrix graph exercises heterogeneous calls: T consumes a wave/crystal context and returns a matrix; inverse-T consumes and returns matrix entries. Their selectors also drive their own current record reads, placement and field calls. The raw four-bit paths are `[0,1,0,0]` for index 19 and `[0,0,1,1]` for index 18, each XOR-adjusted for the current neck bit before the resident BST applies its reversal. The dynamic contract supplies the expected role/signature, not a hardcoded replacement for lookup. Native execution checks the selected current record against that signature; an incompatible address must fail and roll back. The ordinary selected-wave role99 remains a separate declared interface.

These are authored computational laws with the following measured consequences. The [source-only intervention campaign](../output/source_graph_2026-09-24/interventions.json) records 17 healthy CPU/Vulkan pairs, 1,754,142 compared mutable-instance words and 84,108 instance-epochs per backend. Phase bias and growth rewiring each change all four wave components in 129/129 instances at epochs 1, 2 and 64. Mutation bias changes complete operator-containing images in 129/129 instances while all state components remain unchanged through epoch 64. The conservative enzyme graph changes decoded physical composition and domain diagnostics while leaving core waves unchanged through epoch 128. All four corresponding identity controls reproduce complete mutable images at epoch 64. These observations do not support claiming every graph edit changes every output.

The [self-change campaign](../output/source_graph_2026-09-24/self_change.json) changes only the graph composition returning the mutator's successor body. Its four healthy pairs compare 420,024 mutable-instance words over 16,899 instance-epochs per backend. Freezing that successor leaves epoch 1 state exact; at epoch 2 it changes 129/129 waves, 81 accepted intrinsic coordinate pairs and 80 decoded physical compositions. The intrinsic/physical counts differ because distinct FP32 coordinates can round to the same decoded concentrations. The identity control remains exact at epoch 64.

The [matrix campaign](../output/source_graph_2026-09-24/matrix_audit/REPORT.md) completes seven CPU/Vulkan pairs of 257 instances, including two intentional signature-failure pairs. Full matrix applications run for 1, 8 and 64 epochs. Actual indices 19/18 are correct for both neck values, and the inverse uses both numerical branches (30 adjugate, 227 Schur). Independent binary64 comparisons satisfy the predeclared 1e-6 bounds: the maximum entry of `T A − I` is 1.0736e-7, the added graph matrix application has scaled error 5.7430e-8, and the final pair through pinion/return has scaled error 1.1329e-7. Both incompatible route cases return status 11 and roll back every state/record word in 257/257 instances.

The extra matrix application is additional to the inverse application already present in the pinion body. After one epoch it changes amplitudes in 257/257 instances while T and A themselves remain identical to the unconditioned graph. This is a measured composition change, not a new physical device or an optimization claim.

## Headless commands and artifacts

Use a new output directory for compilation:

```powershell
.\Dawnwood-Graph.cmd compile --graph source_bindings/graphs/cycle_v0.1.json --instances 129 --output output/my_graph
.\Dawnwood-Graph.cmd run --input output/my_graph/program.bin --output output/my_graph/vulkan.bin --backend vulkan --epochs 64
.\Dawnwood-Graph.cmd inspect output/my_graph/vulkan.bin --manifest output/my_graph/manifest.json
```

The launcher uses the bundled Python runtime when present. The explicit equivalent is `python -X utf8 -B local_lab/source_graph_program.py compile ...`; the native executable remains the resident-v2 binary. Use `--backend cpu` for the matched portable scalar backend.

For the domain application:

```powershell
.\Dawnwood-Graph.cmd compile --graph source_bindings/graphs/conservative_enzyme_v0.1.json --enzyme-inputs source_bindings/examples/enzyme_inputs.json --output output/my_enzyme_graph
```

`--model`, `--cycle`, `--registry` and `--routes` select the actual corresponding source inputs. The amplitude graph additionally needs `--model source_bindings/examples/amplitude_budget_model.json`. With `--enzyme-inputs`, observation rows determine the instance count; a separate `--instances` is rejected.

Compilation retains exact input documents, `definition.json`, `program.bin`, `manifest.json` and compiler snapshots. The manifest records source hashes, graph hashes, both generated-plan hashes, nominal contracts, structural evidence, node-to-instruction spans, named returns and register-allocation metadata. Device checkpoints preserve the complete executable configuration and mutable instances. Identical mutable images across editions do not require identical program/checkpoint configuration bytes: graph lowering changes the tapes and allocation.

## Evidence and finite limits

The [22-pair result list](../output/source_graph_2026-09-24/paired_summary.json) reports complete CPU/Vulkan checkpoint identity and successful statuses. The [summary](../output/source_graph_2026-09-24/summary.json) additionally compares earlier and graph-generated mutable images for core epochs 1/2/64, enzyme epochs 1/2/8/64/128/2048, amplitude epochs 1/2/64/2048, and authored-Hadamard epochs 1/2/64. It records exact continuation and reverse-target equivalence. These finite observations support default compatibility without equating differently configured files.

The [graph-profile stress run](../output/source_graph_2026-09-24/saturation/summary.json) advances 33,024 independent instances for 2,048 epochs. These are 129 distinct templates repeated 256 times; all 26,881,536 mutable words match their corresponding completed CPU templates. GPU utilization reaches 100% in 101 of 117 telemetry samples, with maximum 71°C, zero validation errors/warnings and no thermal stop. The 54.0001555-second timing sums host submit-to-fence waits, excluding setup, command recording and readback. This measures compute saturation, not maximum VRAM capacity. No host state read/upload occurs between epochs.

The [public CLI receipt](../output/source_graph_2026-09-24/cli/summary.json) verifies compilation, CPU/Vulkan execution, inspection and result decoding through `Dawnwood-Graph.cmd` for 8 instances over 128 epochs. Complete checkpoints match and 19 manifest file hashes verify. All reported candidates are feasible within the declared tolerance, while some gap estimates remain above threshold; optimality is not claimed and readout does not repair the state.

The [direct compiler audit](../output/source_graph_2026-09-24/compiler_rejections.json) records schema, type, atomicity, guard-retention and allocation checks separately from native execution. The independent [fidelity audit](../output/source_graph_2026-09-24/fidelity_audit/results.json) retains 18 targeted broken-edge cases and four positive controls, all matching expectations. Its [script](../output/source_graph_2026-09-24/fidelity_audit/experiment.txt), captured checker, input graphs/definitions, hashes and logs reproduce the direct structural API experiment. It executes no native workload.

Structural fidelity follows named argument ancestry and execution order. A helper may multiply an input by zero or a callee may ignore it; passing the checker does not prove nonzero sensitivity. Guard-only and execution-only effects also differ from arithmetic causality. Numerical interventions, null controls, independent mathematical references, failure/rollback probes and runtime receipts remain necessary for claims about behavior. Neither structural checks nor CPU/GPU agreement prove a scientific law is the intended law.

This edition retains at most 32 records, 64 state values, 256 functions, 256 body families, 32 methods per family, 256 expression instructions per function, 64 function inputs and 32 outputs. Each source plan is bounded to 2,048 graph nodes and 4,096 generated tape instructions. Register allocation uses at most 192 simultaneously live value registers and a separate 64-value argument window in the 256-register frame. A graph can exceed liveness capacity before exhausting the node limit and must then reject.

The core edition uses 44 state values; the added-route edition uses 45; the enzyme edition uses 64. Every GPU lane remains an independent instance with its own resident records. Runtime allocation of new records, unrestricted synthesis of new expression programs, unbounded symbolic DAG evaluation, global shared-field semantics, general optimization, quantum computation and an asymptotic performance advantage are not established by this graph milestone.
