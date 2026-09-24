# Literal application contract

The target is an application whose acting definitions belong to the circulating SDF operator field. An external application algorithm that consumes distance values does not, by itself, implement that target. This document connects the primary sources, the original application and the conditions for a numerical implementation. The bounded source cycle and a resident enzyme-pool application now implement the declared relationships; open numerical choices and broader source claims remain explicit.

Page references below are physical PDF pages. The sources are the 24-page [original discussion](../double-slit-theory.pdf), the 18-page [Unified v0.2 definition](../Dawnwood_Interactive_Unified_v0.2.pdf), and the 20-page [early formalization](../Dawnwood_Interactive_Formalization.pdf). The original application is preserved in [the source archive](../Dawnwood_Interactive_Unified_v0.2.zip) and its restored [workbench directory](../source_workbench/Dawnwood_Interactive_v0.2/README.md).

The bounded [cycle_v0.1 numerical edition](SOURCE_CYCLE_BINDING.md) now executes
these eight-stage core relationships through resident definitions. Its
[source audit](../output/source_cycle_2026-09-24/SOURCE_FIDELITY_AUDIT.md) and
[recorded campaign](../output/source_cycle_2026-09-24/REPORT.md) identify the
implemented relationships and explicit limits. The [resident enzyme specialization](RESIDENT_ENZYME_BINDING.md)
now adds an independently checked consistency task inside that cycle.
Unrestricted authoring, optional output packing and broader application claims
remain separate requirements.

## What the source actually requires

The [numerical integration ledger](SOURCE_NUMERICAL_INTEGRATION.md) tracks the
implementation against this contract. It separates earlier components, the
bounded complete-cycle edition, the enzyme application and remaining requirements.

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

Immutable scientific facts are not the defect. Conservation laws and source data can remain protected while computational strategies change. The connection missing from D1 is the application program itself: its acting procedures must be represented and executed through the common definition. The later resident enzyme application supplies that connection with explicit typed roles interpreted by the generic runtime; it does not retroactively change D1's scope.

## Acceptance conditions for numerical integration

These conditions make each numerical edition reviewable without requiring every interpreter detail to be mutable:

1. **One authoritative application model.** The catalogue, body expressions, field definitions, anchors and declared cycle produce the executed application. A CPU or GPU evaluator may provide stable primitives, but application behavior must not be duplicated in an independent solver keyed to the application's name.
2. **Explicit numerical bindings.** Every executed term has a typed meaning and versioned binding. Unsupported expressions fail visibly. Missing source laws remain identified choices rather than receiving silent substitutes. Finite record sizes and supported operations are declared implementation limits.
3. **Acting edits.** A deliberate body edit changes the corresponding numerical application. Field and anchor changes affect selection or action according to their bindings. Evidence must distinguish changed numerical behavior from merely changed graph hashes.
4. **Resident metarules.** The preceding mutation record participates in determining the next operator definitions, including its own subsequent definition. Changed definitions actually execute; mutation is not restricted to a parameter of an otherwise external application.
5. **Connected circulation.** Route/reversal, log-polar state, paired hinge/pinion, primitive/divergence/coupling operations, four slots with double fourth-slot Y-up, history, inverse and return retain their declared dependencies. Any externally supplied controls are identified. A claimed geometry-derived routing decision requires an implemented geometry binding.
6. **Whole-state continuation and device fidelity.** Checkpoints preserve live definitions, their numerical state, cycle and required history. Device packing preserves those semantics within declared error limits. CPU/GPU agreement and hardware measurements assess this executed profile, separately from expression-graph identity.
7. **Application-level evidence.** A source-native conditional/body-change example should show which resident definition acted before and after change. A useful domain application must additionally produce independently checkable domain outputs. Throughput alone satisfies neither condition.

## Current resident domain application

[DWI-ENZYME-0.1](RESIDENT_ENZYME_BINDING.md) is a bounded implementation of enzyme-pool consistency: it reconciles four supplied concentrations under the two conserved totals of a closed, fixed-volume `E + S ⇌ ES → E + P` model. The [grounding document](ENZYME_POOL_DOMAIN_GROUNDING.md) states the source assumptions, species order, units and induced concentration metric. The task produces a composition witness under those assumptions; it is not a reaction-rate, equilibrium or thermodynamic-direction calculation.

The current `blend` record has additional resident roles for proposing a candidate, evaluating the intrinsic conservation-plane SDF, projecting/evaluating a proposal, accepting or rejecting it and returning a four-species witness. Its two compatible body families share identical scientific-law function handles while changing the proposal role. The preceding resident mutator uses prior domain results to choose the next family and still changes its own subsequent definition. All original eight source stages remain active, and the complete current bank, records, history and 64-word state are checkpointed.

The operator's field slot remains its Klein carrier disk. The chemical SDF is a typed body role with concentration-space operands. This is an explicit situated distance-operator specialization; it does not claim that concentration coordinates are Klein chart coordinates, or that the original `Math_blend` symbol uniquely specified enzyme chemistry. Carrier placement and field affect the computational proposal while the scientific laws keep their meanings.

The [application campaign](../output/resident_enzyme_2026-09-24/REPORT.md) records 129 synthetic observations, healthy execution, feasibility within `1e-5` normalized tolerance, exact CPU/GPU checkpoint agreement, exact continuation and reverse mutation-order agreement. Interventions in each of the eight source stages and in carrier field/placement alter accepted concentrations in 108/129 cases. Freezing the mutator's self-change affects the accepted domain state in 81/129 cases by epoch 2. These are numerical acting-definition effects, not only changed graph identifiers.

The extra chemical-to-controller feedback path is both declared and observed with delay: ablating it leaves core waves unchanged through 128 epochs, but changes waves in 45/129 cases at epoch 2,048. Accepted concentrations remain unchanged in that long comparison because the sampled recurrence has already plateaued. The observation supports that conditional coupling, not a claim that every feedback perturbation changes every output.

Against an independent constrained optimum, maximum species error after 128 epochs is `4.337e-4` normalized units. FP32 boundary effects leave unresolved gaps and can reverse very small true objective differences. The implementation therefore reports approximate candidates and estimated gaps; it does not guarantee exact nearest solutions or monotonic real-arithmetic improvement. Synthetic consistency evidence also does not establish empirical biochemical validity, a speed advantage, unrestricted program synthesis, general intelligence or physical quantum computation. Optional device packing and wider source-language support remain open.
