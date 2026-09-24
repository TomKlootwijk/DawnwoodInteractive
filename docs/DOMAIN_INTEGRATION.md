# Integrating domain knowledge as situated computational fields

24 September 2026. This contract connects sourced domain relationships to Dawnwood's operator-bearing recurrence. It distinguishes the **standalone CPU field bindings**, the unchanged **DWI-N1-0.5 profile**, and the optional **DWI-D1-0.1 native domain profile**. The [native kernel definition](DOMAIN_KERNEL.md) now implements affine-law evaluation, controller-modulated task projection and feedback in the shared C++/Vulkan equations. Wider domain models and fuller architectural closure still require explicit bindings and evidence.

## Two spaces, one explicit connection

The [Unified definition](../Dawnwood_Interactive_Unified_v0.2.pdf), pp. 9 and 12–13, represents an operator by its body, field and situated position, and returns changed operators with the state. A domain specialization must bind each component:

| Component | Required application meaning |
|---|---|
| Domain state `x` | Named variables, units, valid ranges and declared environmental conditions. |
| Field `f(x)` | A sourced relationship with an explicit sign/zero meaning and metric, or a clearly labelled residual. |
| Body | The executable action: evaluate, compose, propose, select, record or transform another permitted operator. |
| Carrier anchor `(u,v,orientation)` | Placement and transport in the Klein operator field, with a declared effect on selection or action. |
| Return | Candidate state, evidence and changed computational definitions used by the next circulation. |

The **carrier space** is the Klein chart and its transported frame. The **domain state space** might contain concentrations, temperature or resource allocations. A micromolar concentration is not a surface coordinate. Specify encoding and decoding, and how a carrier encounter selects or applies a domain field. Retaining both spaces prevents decorative placement from being mistaken for an executable geometric relationship.

For mixed units, declare coordinates such as `z_i=(x_i-reference_i)/scale_i`. Euclidean distance in `z` is dimensionless and depends on those scales. A distance is meaningful only with its metric and units; changing scales changes that distance even when the same physical equation remains satisfied.

## What can be an exact field

A normalized affine boundary `(a·z-b)/||a||` is an exact signed distance to its hyperplane in Euclidean `z` coordinates. Sphere and box distances have similarly explicit contracts. An equality uses zero distance or a stated tolerance; a signed negative value alone does not satisfy an equality. Inequality acceptance needs its own sign convention.

An arbitrary biological law is not automatically a signed-distance function. For example, the Michaelis–Menten rate relation `v=Vmax*S/(Km+S)` describes saturation kinetics under its applicable conditions. Subtracting predicted from observed rate gives a **rate residual**, not generally distance to the curve. The supplied parameters must identify their experiment, conditions and uncertainty; illustrative defaults identify no particular enzyme. [IUPAC Michaelis–Menten kinetics](https://goldbook.iupac.org/terms/view/M03892/pdf)

Composing valid constraints with minimum or maximum can express admissibility without producing an exact distance everywhere. Keep `exact_sdf`, `residual` and compound feasibility scores distinct. This permits literal geometric computation where justified without claiming that all domain knowledge has a universal SDF encoding.

## First application: enzyme-pool consistency witness

Use the declared, fixed-volume mechanism `E+S <=> ES -> E+P`, with no enzyme synthesis, degradation or omitted substrate reservoirs. Let `x=(E,ES,S,P)` in micromolar, and supply conserved totals. The authored moiety constraints are

\[
E+ES=E_{total},\qquad S+ES+P=S_{total},\qquad x_i\ge0.
\]

With one common concentration unit, the two normalized signed hyperplane distances are `(E+ES-E_total)/sqrt(2)` and `(S+ES+P-S_total)/sqrt(3)`. Their perpendicular projections give individual boundary witnesses. A witness for one constraint does not automatically satisfy the other or nonnegativity. Report every original constraint after any proposed correction.

For illustrative totals `E_total=10` and `S_total=100`, `(8,2,78,20)` satisfies both pools. Changing only `ES` to `3` violates both, with raw concentration-space distances approximately `0.7071` and `0.5774` micromolar. With a common scale of one micromolar, the normalized CPU/D1 distances have those same numbers but are dimensionless. These are computational witnesses under declared assumptions, not measured enzyme data. A proposed correction must be checked against both pools together.

This answers a concrete question: **is this candidate composition consistent with the stated pools, and which relation excludes it?** It does not determine reaction speed, equilibrium or biological viability. A broader reaction-feasibility witness needs a declared species representation, stoichiometry, conditions and appropriate thermodynamic data. Chemical equations for explicit ionic species and biochemical equations using transformed totals at specified pH require different bookkeeping. [NIST biochemical thermodynamics recommendations](https://www.nist.gov/publications/recommendations-terminology-and-databases-biochemical-thermodynamics)

The optional D1 profile now projects actual four-coordinate task states against these affine law types, with relaxation controlled by the mutable situated operator 30. Constraint violation participates in geometry and returns through `state.field` to later mutation. Its laws remain protected. This is a native task binding; it does not implement arbitrary proposal/rejection/rollback programs, enzyme dynamics or thermodynamic reaction feasibility. Those additions would require further explicit task operands, actions and return paths.

## Protect laws while allowing self-reference

Keep versioned source metadata, adopted conservation relations, physical constants and application invariants immutable within an experiment. Store assumptions and uncertain measured parameters explicitly; changing an assumption creates a new identified model. A solver must not improve its score by quietly weakening conservation or changing a constant.

Mutable records can instead represent candidate assignments, permitted parameters, proposal scales, operator ordering and search strategies. A controller record can change these and itself be acted upon by other field records. That remains self-referential: the executable strategy producing later candidates belongs to the returned state. Protecting domain truth does not require fixing every computational strategy.

## Compiler and extension contract

Every compiled operator should carry:

- Identity, source URL/version, equation or derivation, assumptions and immutable content hash.
- Domain variable order, units, scales, valid domain, metric, field classification and acceptance tolerance.
- Body language/version, typed operands, carrier anchor/frame and declared dependencies.
- Mutation permissions, immutable references, checkpoint representation and returned witness schema.

Compilation should reject missing units, incompatible operands, unsupported field types and undeclared mutable targets. Execution should distinguish invalid input, constraint violation and bounded-run unresolved status. A finite unsuccessful search is not proof of infeasibility. Evidence should preserve input, source/model identity, executed operator changes and residuals evaluated against the original constraints.

The CPU [domain binding library](../local_lab/domain_fields.py) exposes `catalogue()` and `evaluate(spec)`. Its `DW-Domain-0.1` examples cover enzyme pools, buffer windows, enzyme kinetics, GPU resource budgets and spatial clearance. These authored bindings report their field class, metric, acceptance and boundary information. Their local validation concerns those equations, not integrated GPU execution.

D1 adds three versioned affine domain-field types and uses four existing state slots under a distinct checkpoint magic; it does not silently reinterpret N1 checkpoints. Its native projection/evaluation actions and protected law records are documented separately. Future nonlinear fields, richer task storage, explicit rollback and broader interpreter actions require another declared profile extension. Require matched CPU/GPU evaluation and a trace showing that changed situated definitions cause a meaningful domain result.

The same contract supports computational memory and local planning: typed relations or resource/clearance constraints become acting definitions, while authorized metarules change retrieval or proposal behavior. The [specialization roadmap](SPECIALIZATION_ROADMAP.md) describes these targets. They need concrete task semantics and execution evidence, not an external solver with a Klein picture attached.
