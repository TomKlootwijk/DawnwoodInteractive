# Dawnwood Interactive

Dawnwood proposes a self-referential spatial computing substrate: executable
operator bodies, their fields and positions, paired streams, routing and returned
state participate in one evolving definition. The operator that changes
operators is itself represented in the field.

The repository contains the original documents, successive formalizations,
shared C++/Vulkan equations, hardware evidence and **headless native
specialization tools**. Source intent, chosen equations, executable behavior and
measured results remain distinct.

## The source application and its numerical edition

The [literal application contract](docs/LITERAL_APPLICATION_CONTRACT.md) is the
reference for implementing the requested architecture. The application must act
through its resident body/field/anchor definitions, including the definition
that changes other definitions, and return them with the state.

The original unified application is now available directly in
[source_workbench](source_workbench/README.md), restored byte for byte from the
supplied archive. Its headless authoring path is:

```powershell
.\Dawnwood-Source.cmd catalogue
.\Dawnwood-Source.cmd run --steps 8 --out output/my_source_08
```

Its 36 original checks pass. Saved continuation exactly reproduces uninterrupted
execution; live body and mutation-definition edits propagate through the
returned expression state. Read the
[source application reproduction](output/source_application_2026-09-24/REPORT.md).

**The authored numerical edition now executes all eight source stages through
resident body/field/placement definitions on CPU and Vulkan.** Its 31 records,
typed body families, old-snapshot mutation, dependent four-stage update, complex
streams, finite history, inverse matrix and Klein return are documented in the
[source-cycle binding](docs/SOURCE_CYCLE_BINDING.md) and
[source fidelity audit](output/source_cycle_2026-09-24/SOURCE_FIDELITY_AUDIT.md).
The source's open numerical laws are explicitly chosen bindings. This is a
bounded numerical edition with explicit source and arithmetic limits. A resident
enzyme-pool application now specializes this cycle, as described below. The
[source-authoring interface](docs/SOURCE_PROGRAM_AUTHORING.md) additionally
compiles explicit body/field/placement edits and one newly routed situated
operator into this same cycle.

```powershell
.\Dawnwood-Cycle.cmd compile --output output/my_cycle
.\Dawnwood-Cycle.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_cycle/program.bin --output output/my_cycle/after_64.bin --epochs 64
.\Dawnwood-Cycle.cmd inspect output/my_cycle/after_64.bin --manifest output/my_cycle/manifest.json
```

Use a fresh compilation directory. The [recorded cycle campaign](output/source_cycle_2026-09-24/REPORT.md)
separates complete-cycle comparisons, deliberate body interventions, independent
mathematical checks and hardware saturation. Selected-action adapters currently
cover six geometric records; optional Bayer layout and BC5 encoding are not
implemented by this edition. Its saturation and mathematical results belong to
the source-cycle campaign; application-specific evidence is recorded separately.

## Run the resident enzyme application

To author the acting definitions directly, see [source-program authoring](docs/SOURCE_PROGRAM_AUTHORING.md).
For example:

```powershell
.\Dawnwood-Author.cmd compile --model source_bindings/examples/amplitude_budget_model.json --output output/my_authored_program
```

The [authoring campaign](output/source_authoring_2026-09-24/REPORT.md) records
source-slot causality, added-record routing, independent distance/projection
checks and a GPU saturation run. The later [source graph compiler](docs/SOURCE_GRAPH_PROGRAM.md)
makes both mutation and all eight action stages authorable as named, typed graph
connections. Its [separate evidence](output/source_graph_2026-09-24/REPORT.md) covers
compatibility, graph-only interventions, heterogeneous matrix routing and laptop load.

```powershell
.\Dawnwood-Graph.cmd compile --graph source_bindings/graphs/enzyme_v0.1.json --enzyme-inputs source_bindings/examples/enzyme_inputs.json --output output/my_graph_enzyme
.\Dawnwood-Graph.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 128 --input output/my_graph_enzyme/program.bin --output output/my_graph_enzyme/gpu128.bin
.\Dawnwood-Graph.cmd results output/my_graph_enzyme/gpu128.bin --manifest output/my_graph_enzyme/manifest.json --output output/my_graph_enzyme/results.json
```

The graph names current records, typed inputs and returned state; the compiler
assigns registers. The numerical body laws and initial banks still come from
explicit bindings. The [requirements audit](docs/SOURCE_GRAPH_REQUIREMENTS.md)
separates this executable scope from optional codecs and unproved physical claims.

[DWI-ENZYME-0.1](docs/RESIDENT_ENZYME_BINDING.md) reconciles supplied enzyme,
substrate, complex and product concentrations against two conserved pools. Its
proposal, chemical SDF, projection, evaluation and acceptance are executable
resident definitions inside the full eight-stage cycle. A resident mutator
changes the proposal strategy from preceding results. The chemical SDF uses an
explicit concentration metric; the operator's Klein field and placement retain
their carrier meanings.

```powershell
.\Dawnwood-Enzyme.cmd compile --inputs source_bindings/examples/enzyme_inputs.json --output output/my_enzyme
.\Dawnwood-Enzyme.cmd run --backend vulkan --epochs 128 --input output/my_enzyme/program.bin --output output/my_enzyme/gpu128.bin
.\Dawnwood-Enzyme.cmd results output/my_enzyme/gpu128.bin --manifest output/my_enzyme/manifest.json --output output/my_enzyme/results.json
```

The [resident application campaign](output/resident_enzyme_2026-09-24/REPORT.md)
checked 129 synthetic cases: all were runtime-healthy and feasible within the
declared `1e-5` normalized tolerance. CPU/GPU checkpoints, resumed execution and
reversed mutation order agreed exactly. After 128 epochs, the maximum species
error against an independent constrained optimum was `4.337e-4` normalized
concentration units (`0.004337 uM` with that campaign's scale).

This is a bounded consistency tool for the supplied model. It reports residuals
and an estimated optimality gap; FP32 rounding prevents an exact-nearest or
strict-monotonicity guarantee. Computational epochs are not biochemical time.
See the [domain derivation](docs/ENZYME_POOL_DOMAIN_GROUNDING.md) for the scientific
assumptions and metric. No speed advantage over a direct small solver is claimed.

## Earlier numerical components

The earlier numerical components remain available:
[DWI-XIR expression bindings](source_bindings/README.md). It compiles a selected
source operator's declared numerical body into the same instructions for CPU
and Vulkan. The early formalization's two-Hadamard formula is one implemented
binding. [Measured component results](output/source_ir_2026-09-24/REPORT.md)
include independent analytic comparisons and executable body edits. The
[integration ledger](docs/SOURCE_NUMERICAL_INTEGRATION.md) retains all remaining
operator, stage and whole-state requirements; this isolated body evaluator has a narrower scope than the authored cycle above.

The next component, [situated Apply](docs/SITUATED_APPLICATION.md), executes a
selected source record's **placement → Klein-local SDF → two-Hadamard body**
as one numerical program. Each definition can be replaced by an executable
expression. Independent placement, field and body edits change the measured
action on both CPU and GPU. The complete authored recurrence is supplied by `Dawnwood-Cycle.cmd` above.

```powershell
.\Dawnwood-Apply.cmd compile --bindings source_bindings/situated_v0.1.json --operator hadamard --inputs source_bindings/examples/situated_inputs.json --output output/my_situated
.\Dawnwood-Apply.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_situated/program.bin --output output/my_situated/gpu.bin
.\Dawnwood-Apply.cmd inspect output/my_situated/gpu.bin --manifest output/my_situated/manifest.json
```

[Resident definition execution](docs/RESIDENT_DEFINITIONS.md) now adds actual
in-run program selection: the old situated mutator and pinion produce new
body/field/anchor records, including their own, and subsequent action executes
those records. The three-record component preserves all programs and live state
in a resumable checkpoint. Its self-mutation, feedback, old-snapshot ordering and
rollback have [CPU/GPU evidence](output/resident_definition_2026-09-24/REPORT.md).
This three-record fixture remains a regression reference for the larger finite
source-cycle bank above.

```powershell
.\Dawnwood-Resident.cmd compile --definition source_bindings/resident_v0.1.json --output output/my_resident
.\Dawnwood-Resident.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_resident/program.bin --output output/my_resident/after_8.bin --epochs 8
.\Dawnwood-Resident.cmd inspect output/my_resident/after_8.bin --manifest output/my_resident/manifest.json
```

The [typed resident v2 runtime](docs/RESIDENT_V2_ABI.md) adds complete body-family
replacement, computed source-index routing and portable log/phase arithmetic.
Its [CPU/GPU campaign](output/source_cycle_2026-09-24/RUNTIME_REPORT.md) verifies
typed execution, strict route failures, rollback and exact continuation. Use
`Dawnwood-Resident2.cmd` for its separate `DWRD0002` checkpoints. Full-cycle
fidelity requires the authored application binding in addition to this machine.

## Run the D1 constraint-repair experiment

From the repository root, using Python 3.10 or newer:

```powershell
python local_lab/specialize.py --example enzyme_repair --count 257 --epochs 64 --stride 16 --output output/enzyme_repair_live_01
```

The laptop launcher finds the installed Python automatically:

```powershell
.\Dawnwood-Specialize.cmd --example metabolic_flux --output output/my_flux_01
```

On this laptop the bundled Python can be used directly:

```powershell
$dwPython = 'C:\Users\ietsm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $dwPython local_lab/specialize.py --example buffer_design --count 257 --epochs 64 --stride 16 --output output/buffer_design_live_01
```

Each output directory must be new. The tool uses
`Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/bin/windows-domain/dawnwood.exe`.
It compiles the definition into native operator/state records, compares CPU and
GPU for the requested verification interval, then advances the actual selected
backend. Returned proposals are written to `solutions.csv`; `result.json`
contains complete-population constraint audits. Checkpoints, executable hashes,
commands, stdout, stderr and exit codes are retained beside them.

Available definitions under [domain_knowledge/native](domain_knowledge/native):

| Example | Concrete use | Scope |
|---|---|---|
| `enzyme_repair` | Repair enzyme-pool proposals against declared conservation and bounds | Constraint-consistent candidates, not a biochemical time simulation |
| `buffer_design` | Find assignments satisfying authored log-activity buffer constraints | The supplied affine model and assumptions, not an experimental formulation guarantee |
| `metabolic_flux` | Produce candidates for synthetic steady-state flux constraints | A finite synthetic network, not a validated organism model or optimal flux |
| `resource_allocation` | Propose resource quantities within quotas and capacities | Feasibility proposals, not a scheduler acting on the machine |

These definitions use **DWI-D1-0.1** in executable **0.6.0-domain1**. All four
returned feasible assignments for 257 proposals on the RTX laptop. A further
1,048,576-state enzyme run completed 1,024 epochs and passed the full-population
constraint audit. Read the [measured results and limits](output/domain_kernel_2026-09-24/REPORT.md).

## What the native binding does

Four state slots carry normalized domain coordinates. Additional protected LUT
records carry affine equality, halfspace or slab laws. Their individual distance
fields are evaluated directly; mutation cannot change their coefficients.

Constraint violation enters the existing geometry/body computation. The current
mutation controller determines the relaxation used by an ordered projection
sweep. Returned domain error enters `state.field`, influencing the next operator
mutation. Klein transport, paired amplitudes, history, inverse-T response and the
mutation-before-evolution schedule remain active. This is a versioned addition
to the existing numerical recurrence.

The binding supplies finite constraint repair. It does not establish optimality,
automatic scientific discovery, general intelligence or physical quantum
computation. An unresolved bounded run remains an unresolved result.

## Read and reproduce

1. [Architecture study](docs/ARCHITECTURE_STUDY.md): the source's operator,
   geometry, state and self-reference relationships.
2. [Source-to-kernel map](docs/SOURCE_TO_KERNEL.md): executable bindings and
   remaining fidelity questions.
3. [Headless tools](local_lab/README.md): commands, authoring schema, controllers
   and saved evidence.
4. [Local experiments](docs/LOCAL_EXPERIMENTS.md): controlled comparisons and
   acceptance criteria.
5. [Specialization roadmap](docs/SPECIALIZATION_ROADMAP.md): finite tasks and
   additional work required for broader specialization.
6. [Domain fields](docs/DOMAIN_FIELDS.md) and
   [domain integration](docs/DOMAIN_INTEGRATION.md): knowledge definitions,
   coordinate metrics and native mapping.
7. [Native domain equations and ABI](docs/DOMAIN_KERNEL.md): the exact feedback,
   projection, immutable-law and checkpoint bindings.
8. [Resident enzyme application](docs/RESIDENT_ENZYME_BINDING.md): complete-cycle
   candidate reconciliation, executable domain roles and measured numerical limits.

## Original architecture and preserved numerical profile

- [Original 24-page source](double-slit-theory.pdf).
- [Unified definition v0.2](Dawnwood_Interactive_Unified_v0.2.pdf).
- [Earlier formalization](Dawnwood_Interactive_Formalization.pdf).
- [Native runtime documentation](Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/README.md).

**DWI-N1-0.5** remains the existing numerical profile. Its separate
**0.5.1-rtx1** laptop release and evidence are retained:
[download](output/Dawnwood_RTX5070Ti_v0.5.1.zip),
[RTX validation report](output/rtx5070ti_laptop_2026-09-24/REPORT.md).
That campaign completed 43,609,664 states under its stated memory policy and 177
full epochs during the sustained run. Those timings and capacity results belong
to N1; they are not D1 specialization measurements.
