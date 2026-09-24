# Literal application contract

The target is an application whose acting definitions belong to the circulating SDF operator field. An external application algorithm that consumes distance values does not, by itself, implement that target. This document connects the primary sources, the original application and the conditions for a numerical implementation. It records an integration contract, not a claim that the numerical work is complete.

Page references below are physical PDF pages. The sources are the 24-page [original discussion](../double-slit-theory.pdf), the 18-page [Unified v0.2 definition](../Dawnwood_Interactive_Unified_v0.2.pdf), and the 20-page [early formalization](../Dawnwood_Interactive_Formalization.pdf). The original application is preserved in [the source archive](../Dawnwood_Interactive_Unified_v0.2.zip) and its restored [workbench directory](../source_workbench/Dawnwood_Interactive_v0.2/README.md).

## What the source actually requires

The [numerical integration ledger](SOURCE_NUMERICAL_INTEGRATION.md) tracks the
implementation against this contract. Its first verified component compiles
selected numerical bodies for CPU/GPU execution; complete situated application
and recurrent closure remain open requirements.

The author's corrections in the original discussion determine the architectural scope. On p12 the author places rasterization, raymarching, raytracing and square output fields outside the core. On p14 the author asks about self-referential computing with operators "defined and packed as SDF operations": the double pinion holds them on the Klein-bottle surface while one-bit jitter acts on the operators in the LUT/BST at interval PSI. Graphics is optional downstream observation.

Unified p3 expresses the system as:

```text
S[n] = (K[n], W[n], L[n], B[n], C[n])
S[n+1] = D_PSI(S[n], jitter[n])
```

Here geometry, wavefront, operator field, branching relation and texture state are coordinates of one returned definition. The operator field is both an input and an output. Unified p9 makes each operator a situated definition:

```text
O[i,n] = (body[i,n], field[i,n], anchor[i,n])
W' = Apply(O[i,n], W; S[n])
```

Body, field and position are accessible to the next operator-change expression. The previous LUT supplies the mutation operator while the new LUT is formed; that mutation operator is itself a field entry. Unified p13 requires the changed definition to be the definition referenced by the next application. A copy of a program stored beside an independently executing algorithm would not establish this dependency.

| Relationship | Source contract | Consequence for an application |
|---|---|---|
| Double pinion and hinge | Unified p5 keeps the hinge and paired pinion as entries whose phase, position and body can change in the same circulation. | The pair must participate in the computational path and return, with declared meanings for its values. |
| Geometric operators | Unified p8 puts the six primitives, phase differential, phyllotaxis, colon coupling and blend in the common cycle. | Their fields and current bodies cannot be decorative metadata. |
| Situated mutation | Unified p9 couples body change, pinion-held position and field change; the mutator is resident too. | Application strategies and their changes must be expressible through current operator records. |
| Routing | Unified p10 gives `child(i,b)=2*i+1+b`, route reversal and application of the selected current record. | A spatial route must select the operator definition that actually acts. |
| RGBA | Unified p11 assigns paired streams to R/G, history to B and inverse T to A. | Channel names need typed computational roles; inverse T needs an actual declared inverse relation. |
| Complete return | Unified p12 returns the changed LUT with the whole state; optional Bayer reads afterward. | Continuation must retain application definitions and their history as well as values. |
| Application vocabulary | Unified p13 maps conditionals, repetition and program change to routing, recurrence and LUT change. | These are requirements for expressing an application, not a supplied compiler for every domain. |

These requirements do **not** imply that all constants, every record or the host interpreter must mutate on every cycle. A stable evaluator can interpret resident definitions, including definitions that change other definitions. The relevant question is whether the current resident definition determines the action, and whether its changed definition is used subsequently.

Provenance matters. Original pp15-17 contain generated responses about automatic optimization, escape from deadlock and quantum behavior. Original p22 contains the author's question about universal expressibility; the affirmative answer and p23's Turing-completeness claim are generated responses. They are not mathematical demonstrations. Unified p18 also identifies its record layout, initial catalogue order and written cycle order as notation introduced by that edition. The structural design can be implemented seriously without presenting those larger claims as established results.

## What the original application executes

The restored [application documentation](../source_workbench/Dawnwood_Interactive_v0.2/docs/WORKBENCH.md) explicitly describes a symbolic expression workbench. Its [kernel](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py) implements the following connected operations:

- `add_operator` creates a body, a surface-position expression, an SDF expression and a record joining them. The [catalogue](../source_workbench/Dawnwood_Interactive_v0.2/model/substrate.json) supplies the initial definitions and indices.
- `set_body` replaces a live body, rebinds its field and refreshes the LUT. `apply` references the current complete record, rather than a detached immutable copy of its initial body.
- `_operator_mutation` captures the preceding LUT, mutation record and pinion record. It constructs new body, anchor and field expressions for every record, including the mutation record. The resulting records participate in that cycle's subsequent applications.
- The [cycle file](../source_workbench/Dawnwood_Interactive_v0.2/model/cycle.json) supplies the phase sequence and fourth-slot Y-up count. The runtime reads both. Its named handlers require the dependencies produced by earlier phases; arbitrary reordering is not automatically meaningful. An unfamiliar phase name creates a symbolic call, not a new numerical implementation.
- `_surface_return` returns the surface, carried result, current LUT and history as the next whole state. Snapshot and continuation preserve the graph, live records, cycle, epoch and state references.

The [expression graph](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/terms.py) is an acyclic history of references. Its self-reference is the recurrence consuming a preceding whole state containing its acting definitions. It does not require a Python object-reference cycle. Content hashes identify expressions and dependencies; they do not prove a numerical result.

There are important execution boundaries. Operator bodies are JSON literals, and `Apply_SDF_operator`, `Mutate_operator_body` and related actions are constructed graph nodes. Their numeric effects are not evaluated. The [binding inventory](../source_workbench/Dawnwood_Interactive_v0.2/model/bindings.json) records open meanings; adding a number or formula there does not automatically install an evaluator.

The [integer helpers](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/native.py) really evaluate parity and implicit routes. However, the [example session](../source_workbench/Dawnwood_Interactive_v0.2/examples/session.json) supplies route, jitter and neck/reversal bits. The current `bst` record participates in the routing expression; it does not numerically derive those supplied decisions from a solved Klein field. Similarly, catalogue `placement` descriptions are not a general placement-expression evaluator: `add_operator` constructs the named phyllotaxis anchor.

The original application's concrete deliverable is consequently an inspectable, editable, resumable expression of the architecture. Its [body-edit example](../source_workbench/Dawnwood_Interactive_v0.2/examples/body_edit.json) changes `double_dot` using operands named `left_pinion`, `right_pinion` and `local_SDF`. This is a real change to the acting expression graph. It is not yet a numerical coupling calculation or a biochemical solver. These boundaries agree with Unified pp16-17.

## Numerical bindings must preserve the relationships

Unified p16 leaves the Klein surface/chart/distance, log-polar coding, phase-dependent hinge/pinion, colon coupling, phase differential/blend, RK derivative/Y-up, PSI/jitter, inverse T and device packing open. Binding those terms is necessary numerical work, not permission to replace the connected application with an unrelated algorithm. Each binding needs declared inputs, outputs, units, metric, precision and behavior at its domain boundaries. A residual or arbitrary transformed field must not silently inherit an exact-distance claim.

The early formalization supplies one explicitly proposed two-Hadamard convention on physical p6, Eq7:

```text
U(phi) = H * diag(1, exp(i*phi)) * H
H      = (1/sqrt(2)) * [[1, 1], [1, -1]]
```

The native N1/D1 [amplitude update](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L138) instead evaluates `diag(exp(i*phase), exp(-i*phase)) * H`. At zero phase these are identity and H respectively. Two channels or two epochs do not make these the same operator. Unified p5 keeps its hinge binding open; a numerical integration must identify which definition it implements and how it remains connected to the pinion, field and application.

The sources also describe several packing relationships: log-polar encoding, dichromatic state, an implicit tree and resident GPU memory. They do not supply a complete independent codec called double packing. Unified p15 explicitly leaves the per-state width of the hypothetical 24-48-billion-state scenario unspecified. A device layout needs an actual record and round-trip contract, including operator definitions and metadata.

## Why D1 is not this completed application

The [D1 profile](DOMAIN_KERNEL.md) adds a fixed cyclic relaxed projection of four domain coordinates over protected affine law records. Its [projection implementation](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L8) determines law order, constraint-kind handling and coordinate update in native code. The current mutation operator supplies a response that modulates relaxation, and violation returns to the recurrent state. That feedback is real.

However, the application procedure is still the native projector. [Protected law evaluation](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L157) bypasses ordinary body/anchor evaluation and returns domain distance directly; those law records are outside the core route. A field-controlled scalar does not encode the application's selection, composition and action as situated executable definitions. Verified constraints and GPU saturation establish results for D1, not completion of the source application contract.

Immutable scientific facts are not the defect. Conservation laws and source data can remain protected while computational strategies change. The missing connection is the application program itself: its acting procedures must be represented and executed through the common definition, rather than hidden in a fixed application-specific loop.

## Acceptance conditions for numerical integration

These conditions make the next implementation reviewable without claiming that every interpreter detail must be mutable:

1. **One authoritative application model.** The catalogue, body expressions, field definitions, anchors and declared cycle produce the executed application. A CPU or GPU evaluator may provide stable primitives, but application behavior must not be duplicated in an independent solver keyed to the application's name.
2. **Explicit numerical bindings.** Every executed term has a typed meaning and versioned binding. Unsupported expressions fail visibly. Missing source laws remain identified choices rather than receiving silent substitutes. Finite record sizes and supported operations are declared implementation limits.
3. **Acting edits.** A deliberate body edit changes the corresponding numerical application. Field and anchor changes affect selection or action according to their bindings. Evidence must distinguish changed numerical behavior from merely changed graph hashes.
4. **Resident metarules.** The preceding mutation record participates in determining the next operator definitions, including its own subsequent definition. Changed definitions actually execute; mutation is not restricted to a parameter of an otherwise external application.
5. **Connected circulation.** Route/reversal, log-polar state, paired hinge/pinion, primitive/divergence/coupling operations, four slots with double fourth-slot Y-up, history, inverse and return retain their declared dependencies. Any externally supplied controls are identified. A claimed geometry-derived routing decision requires an implemented geometry binding.
6. **Whole-state continuation and device fidelity.** Checkpoints preserve live definitions, their numerical state, cycle and required history. Device packing preserves those semantics within declared error limits. CPU/GPU agreement and hardware measurements assess this executed profile, separately from expression-graph identity.
7. **Application-level evidence.** A source-native conditional/body-change example should show which resident definition acted before and after change. A useful domain application must additionally produce independently checkable domain outputs. Throughput alone satisfies neither condition.

For a biochemical specialization, a concrete first target could be enzyme-pool consistency and a reaction-feasibility witness. This remains a proposed application. It would require sourced species and reaction definitions, concentration units and scales, initial observations, conservation constraints, and a clear distinction between feasibility, kinetics and thermodynamic direction. The [existing domain field documentation](DOMAIN_FIELDS.md) supplies authored field examples, not the complete resident application.

The application would need situated definitions for proposing a candidate, evaluating relevant laws, selecting the next action, accepting or rejecting a proposal, returning history and producing a witness. A resident metarule could change proposal composition or search behavior while preserving authoritative scientific laws. The carrier coordinates locate an operator; concentration coordinates describe its domain operands. Their relation must be explicitly encoded through the same acting record and cycle rather than treating them as interchangeable units. Distance to a conservation surface alone does not establish reaction kinetics, equilibrium or biological usefulness.

Success would mean a trace from sourced inputs through those current resident definitions to an independently checked result, including observable effects of legitimate operator and metarule edits. The original symbolic application preserves the relationships needed to express that work. D1 demonstrates a narrower numerical task. Neither currently establishes the complete biochemical application described here.
