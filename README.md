# Dawnwood Interactive

Dawnwood proposes a self-referential spatial computing substrate: executable
operator bodies, their fields and positions, paired streams, routing and returned
state participate in one evolving definition. The operator that changes
operators is itself represented in the field.

The repository contains the original documents, successive formalizations,
shared C++/Vulkan equations, hardware evidence and **headless native
specialization tools**. Source intent, chosen equations, executable behavior and
measured results remain distinct.

## The source application and the numerical gap

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

**This application constructs symbolic expressions. The native GPU runtime does
not import its model, cycle or expression graph.** Nine numerical meanings are
unbound in the source application; the later native profiles make their own
explicit choices. The numerical integration is unfinished. D1's fixed projection
algorithm with a mutable controller is an experiment, not fulfillment of the
literal resident application language.

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
