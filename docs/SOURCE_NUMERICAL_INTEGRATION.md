# Numerical integration of the source application

**Profiles: DWI-XIR-0.1, DWI-APPLY-0.1 and DWI-RESIDENT-0.1. Status: numerical bodies, situated action and a bounded three-record resident-definition transition verified on CPU and the RTX 5070 Ti Laptop GPU for the recorded experiments; full source-application integration remains incomplete.**

The target remains the source application's complete situated-operator recurrence. DWI-XIR supplies a shared CPU/GPU expression evaluator with explicit numerical body bindings. DWI-APPLY composes one selected record's placement, field and body. DWI-RESIDENT adds in-run executable-definition selection for the Hadamard, pinion and mutation records: old controllers read a common preceding snapshot, produce new records including their own, and action executes the new definitions. The full catalogue and eight-stage cycle remain unfinished. These components must not be presented as the complete numerical Dawnwood application.

The [literal application contract](LITERAL_APPLICATION_CONTRACT.md) defines the broader acceptance conditions. This document preserves their implementation scope and records the types and dependencies that later lowering must respect.

## Source, binding, implementation and evidence

These are separate records:

| Layer | Authority and meaning |
|---|---|
| Source relationship | The [original discussion](../double-slit-theory.pdf), especially author statements on physical pp12 and 14, asks for the operators themselves to be SDF operations in the common Klein-bottle/LUT/BST recurrence. |
| Unified application | The [Unified v0.2 PDF](../Dawnwood_Interactive_Unified_v0.2.pdf), pp5-16, and [restored workbench](../source_workbench/Dawnwood_Interactive_v0.2/README.md) express connected bodies, fields, anchors, routing, history and return. Its numerical gaps remain explicit. |
| Chosen numerical binding | The [early formalization](../Dawnwood_Interactive_Formalization.pdf), physical p6 Eq7, proposes `H * diag(1,exp(i*phi)) * H`. DWI-XIR's first body chooses that formula in response to the requested double-Hadamard interpretation. It is a proposed source binding, not a numerical equation present in the original conversation. |
| Implementation | DWI-XIR-0.1 is the current CPU/GPU FP32 expression-VM work. A compiled expression body is one component needed by the source application. The status ledger below prevents that component from standing in for the whole architecture. |
| Evidence | Recorded CPU/GPU outputs, an independent binary64 mathematical audit, body-edit experiments and rejection checks support the body-component results below. Expression hashes identify definitions; they do not replace this numerical evidence. |

The source workbench's [binding inventory](../source_workbench/Dawnwood_Interactive_v0.2/model/bindings.json) contains null numerical bindings. It is an inventory, not a plug-in loader. The [kernel](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py) builds `Apply_SDF_operator`, mutation and surface-position graph nodes from live records. Supplying a JSON body changes that graph but does not automatically evaluate the body numerically.

## Status ledger

| Capability | Current status | Recorded evidence or remaining requirement |
|---|---|---|
| Original authoring model, symbolic records and cycle | Restored source reference | Source files and original workbench behavior; this is symbolic evidence. |
| Generic FP32 expression compilation | Verified for recorded fixtures | Source-record/binding resolution, all 18 opcodes, a constant-only program and 22 malformed-input rejections. |
| Shared CPU/GPU expression evaluation | Verified for 11 recorded final-build experiments | Bitwise-equal CPU/GPU outputs and statuses on the identified laptop, including intentional arithmetic failures. |
| Early Eq7 double-Hadamard body | Verified for 257 input rows | Independent closed-matrix reference, known-phase checks and maximum component error `3.6433394e-7`. |
| Sphere and matrix-contraction body bindings | Verified for supplied fixtures | Four sphere results and one contraction result match the reference exactly; a separate radius-guard failure was exercised. |
| Numerical body edits | External edit and recompilation verified | Negating output `ar` changes 256/257 rows numerically and matches the declared change exactly. No resident mutation runs in this experiment. |
| Source `body + field + anchor` application | One situated Hadamard call verified | DWI-APPLY composes all three actual source slots; independent slot edits affect numerical action. This is external recompilation, not resident mutation. |
| Source phase sequence and typed overloads | Not yet lowered | The authored cycle controls execution with validated dependencies and no hidden substitute schedule. |
| Resident mutation and metarule self-action | Verified finite three-record component | The preceding situated mutator selects new executable bodies, including its successor; old pinion transports anchors; field rebinding precedes publication. Arbitrary expression synthesis and the full catalogue remain open. |
| Component checkpoint continuation | Verified for recorded resident runs | Full bank, plans, live handles, anchors and component state survive continuation; this is not yet a full source-state checkpoint. |
| Full paired-stream/geometry/RGBA/return recurrence | Not yet lowered | Whole-state continuation with all declared dependencies numerically active. |
| Domain application expressed through that recurrence | Pending full integration | A complete resident application and independently checked domain result. Existing D1 feasibility results do not fill this row. |
| Full-profile performance and saturation | Pending full integration | Correctness-established source profile executed at the stated population and interval count. A body benchmark measures only the body workload. |

No row is completed by a changed symbolic-state hash, successful shader compilation alone or timing an unrelated profile. The [N1/D1 implementation mapping](SOURCE_TO_KERNEL.md) and [D1 results](DOMAIN_KERNEL.md) retain their own meanings.

## Recorded body-component evidence

The [resident-definition campaign](../output/resident_definition_2026-09-24/REPORT.md)
adds 30 paired CPU/GPU workloads with 69,278 returned instance words, all
bit-identical. It demonstrates delayed mutator/pinion self-change, body-to-wave
feedback changing later definitions, equal-energy phase-sensitive selection,
reverse target-order independence, checkpoint continuation and epoch rollback.
The independent 51-transition reference has maximum state error `7.475228e-8`
and no handle/generation disagreements. See [the component contract](RESIDENT_DEFINITIONS.md)
for its explicit finite bank, three-record scope and independent-instance
interpretation. The source `cycle.json` is still not consumed by this runtime.

The later [situated-Apply campaign](../output/situated_apply_2026-09-24/REPORT.md)
records 11 composed workloads, 6,177 lanes and 98,832 bitwise-equal CPU/GPU output
values, including four intended lane failures. All 771 equivalent dyadic Klein
representatives return bitwise-equal rows. Independent placement, field and body
edits each change action outputs on all 1,028 supplied rows; zero phase gain
suppresses the action response while the field still changes. Maximum observed
field and action errors against independent binary64 mathematics are
`6.879504e-8` and `8.989369e-8`. These are sampled component results. See
[the declared composition](SITUATED_APPLICATION.md) for the exact metric,
coupling choice and remaining full-application scope.

The [independent numerical audit](../output/source_ir_2026-09-24/independent_numeric_audit.json) reads the actual packed FP32 inputs from each program binary. Its reference calculations use the closed complex matrix for the hinge, Euclidean norm minus radius for the sphere and a matrix Frobenius contraction. The reference does not reuse the bytecode interpreter or compiler AST. All initial **262 lanes and 1,033 output values** have bitwise-identical CPU/GPU output files and zero lane statuses.

| Body | Supplied cases | Independent result |
|---|---|---|
| Two-Hadamard hinge | 257 rows, four complex-component outputs each | Maximum absolute component error `3.643339403502921e-7`; maximum relative squared-norm preservation error `2.784104912776674e-7`. |
| Sphere | Four local point/radius rows | Results `-1, 0, 4, 1` match the binary64 reference exactly for these inputs. |
| Double dot | One pair of real 2x2 matrices | Result `70` matches the Frobenius reference exactly. |

These are sampled numerical observations, not universal error bounds. Hinge phases in the fixture span approximately `[-pi,pi]`. The references use packed input values, while ideal matrix coefficients are evaluated in binary64; original decimal-to-FP32 input conversion remains a separate effect. The measured squared-norm drift confirms that exact mathematical unitarity is not exact FP32 conservation.

The [extended audit](../output/source_ir_2026-09-24/extended_numeric_audit.json) records 11 experiments on final executable SHA-256 `c7f0ab76c3956222f3abbf93b214d0ab3c2d8be6b682ec3f531d1c7c6df68e01`: the three original bindings rerun, an edited body, an all-18-opcode expression, a zero-input constant expression and five domain-failure cases. Every experiment's CPU/GPU output and status representation agrees bitwise. The failure cases cover negative square root, division by zero, overflow, an invalid eagerly evaluated selection operand and a failed sphere-radius precondition. Each reports its intended failing lane and zero output row rather than silently returning a valid result.

The body-edit experiment changes the selected source record to an inline expression that negates only the hinge's `ar` output, then recompiles and executes it. It changes 256 of 257 rows numerically and agrees exactly with the declared transformation. This demonstrates **external authored-body recompilation**. It does not demonstrate the field changing its own resident definitions during execution.

The [rejection record](../output/source_ir_2026-09-24/rejections/summary.json) contains 11 native and 11 frontend malformed-input cases, all rejected before an output file was created. They cover invalid instructions/references/payloads, nonfinite values, unbound symbols, unsupported semantic keys, undeclared inputs, wrong arity, duplicate JSON keys and exceeded instruction limits. This is finite validation coverage, not a proof that every malformed input is handled.

All 11 final GPU receipts identify the **NVIDIA GeForce RTX 5070 Ti Laptop GPU**, with `DAWNWOOD_VALIDATION=1`, validation enabled and zero validation errors or warnings. Representative raw receipts are the [final hinge run](../output/source_ir_2026-09-24/hadamard_final_vulkan.stdout.txt), [edited-body run](../output/source_ir_2026-09-24/body_edit_vulkan.stdout.txt) and [guard-failure run](../output/source_ir_2026-09-24/guard_vulkan.stdout.txt). Their `execution_seconds` measures host submission-to-fence waiting, excluding setup and readback; it is not a GPU timestamp. These small correctness experiments are not saturation measurements. The [run report](../output/source_ir_2026-09-24/REPORT.md) provides the consolidated reproduction record.

## Expression-VM foundation

The shared evaluator is in [source_ir.inc](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/source_ir.inc), with a [compute shader](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/shaders/source_ir.comp). The [source-expression compiler](../local_lab/source_ir.py) resolves a selected original body through an explicit numerical registry or an inline expression. A separate [native harness](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/src/source_ir_cli.cpp) executes the program on CPU or Vulkan. This is independent body evaluation, not a call into a completed source-cycle runtime.

Its declared bounded representation uses FP32 scalar static single assignment: instruction `i` produces register `i`, and operand registers refer only to preceding instructions. The host-validated limits are 256 instructions, at most 64 input columns and at most 32 output columns; a constant-only program can have zero input columns. These are limits of this implementation, not limits supplied by the source architecture.

The initial instruction family contains constants, input loads, arithmetic, sine/cosine/exponential/square root, absolute value, minimum/maximum, negation, floor, less-than, selection and the opcode17 `require` guard. It reuses the native profile's portable elementary arithmetic. This inventory does not yet supply every source operation: for example, full log-polar encoding and operator-record writes still require further lowering or bindings.

Selection is eager SSA evaluation: both operand expressions have already executed. It therefore cannot hide a division by zero or an invalid square root in an unselected branch. The harness contract rejects malformed programs and nonfinite input/constants before dispatch, and reports lane-local arithmetic failure separately from output values. Failure status is `((instruction_index+1)<<16) | reason`, with reason 1 for division by zero, 2 for a negative square-root operand, 3 for a nonfinite result and 4 for a failed `require`. A zero guard operand fails; a finite nonzero value satisfies it. A failed lane's output row is zeroed, so its separate status must be checked. The recorded failure experiments exercise all four reasons and eager selection; the sphere guard produces status `262148` (`0x00040004`) on its invalid-radius lane.

The [binding registry](../source_bindings/xir_v0.1.json) and [binding notes](../source_bindings/README.md) contain three explicit overloads. `Hadamard_mitosis` takes named `ar, ai, br, bi, phase` inputs and returns four amplitude components. `SDF_sphere` takes supplied local `x,y,z,radius` values and computes `sqrt(x*x+y*y+z*z)-radius`; its `radius>0` precondition is emitted as executable guard instructions. `Pinion_double_dot` takes two real 2x2 matrices as named scalar entries and returns their Frobenius contraction. The sphere's carrier-local coordinates and the contraction's pinion tensors are supplied operands at this stage, not values constructed by a lowered source cycle.

An expression is a finite numeric literal, an input reference `{"input":"name"}`, or an operation `{"op":"name","args":[...]}`. A binding declares ordered input names, named output expressions and optional `requires` expressions compiled before outputs. An original `body:{"symbol":"..."}` resolves only through an explicit binding; alternatively, `body:{"expression":{...}}` carries the binding inline. Unknown names, undeclared inputs, wrong arities and unsupported syntax are rejected. The compiler's manifest retains the source record and hashes, selected expression, FP32 input rows, instructions and unimplemented scope. Original historical source files remain unchanged.

## First body: two Hadamards with an intervening phase

The chosen input contract is two complex amplitudes `a=ar+i*ai`, `b=br+i*bi` and a real phase `phi`. Its mathematical action is:

```text
u = (a+b)/sqrt(2)
v = (a-b)/sqrt(2)
v = exp(i*phi) * v
a_next = (u+v)/sqrt(2)
b_next = (u-v)/sqrt(2)
```

This is early Eq7, `U(phi)=H D(phi) H`, with `D(phi)=diag(1,exp(i*phi))`. In exact arithmetic, `U(0)=I`, `U(pi)` exchanges the two inputs, and the complex squared norm is preserved. An independent analytic reference may evaluate the equivalent matrix:

```text
U(phi) = 1/2 * [[1+exp(i*phi), 1-exp(i*phi)],
               [1-exp(i*phi), 1+exp(i*phi)]]
```

The FP32 implementation has rounding and elementary-function approximation error. Its zero-phase result need not be bitwise identical to the input after the two scaled additions, and exact norm conservation is not an implementation guarantee. Report actual component errors and norm errors against the reference. Analytic agreement and CPU/GPU agreement answer different questions; the latter can pass when both implementations share a mistake.

The source seed `[0,2,0,1]` can be interpreted as `(a,b)=(0+2i,0+i)` under the existing N1 seed convention. That is an explicit encoding choice, not a timestamp encoder supplied by the source. It also does not require normalization to unit norm.

The source's split stage must not introduce another Hadamard when the hinge body already implements `H D H`. The split's eventual typed binding must state whether it forms, tags or routes the paired input. Otherwise a seemingly literal implementation could inadvertently execute three Hadamards.

N1's existing amplitude update instead computes `diag(exp(i*p),exp(-i*p)) H`. At zero phase that is H, not identity. Reuse of its arithmetic helpers does not justify reuse of that complete mixer under the new binding's name. The separate XIR body does not change or retroactively correct the historical N1 profile; its documented convention remains distinct.

## Model and type contract for full integration

The source [catalogue](../source_workbench/Dawnwood_Interactive_v0.2/model/substrate.json) provides `index`, `key`, `head`, body JSON, field JSON, placement JSON and provenance for each operator. The numeric compiler must identify which of those fields it consumes. The original runtime does not numerically dispatch on `head` or evaluate arbitrary placement JSON; it constructs a named phyllotaxis anchor. Such gaps need implemented bindings, not assumptions about what the source loader already does.

A future compiled situated record needs a stable identity/index, versioned executable body, field program, anchor program or state, parameters and provenance. An application call needs typed operands and access to the current record. A mutation call additionally needs the immutable preceding whole state and preceding LUT. None of these requirements implies that host interpreter instructions or scientific constants must rewrite themselves.

The full application needs semantic types beyond a scalar-expression VM: bits and indices, complex pairs, chart coordinates with orientation, tangents, matrices, field values with metric/quality, operator references, RK slots, history and whole-state references. These are **requirements for the enclosing application compiler**, not a claim that DWI-XIR-0.1 already implements each type. Vector and matrix arithmetic may lower to scalar registers while retaining compile-time shape and unit checks.

`Apply` in the symbolic application is intentionally permissive. A numeric compiler cannot interpret every selected operator as `scalar -> scalar`. For example, inverse T consumes a transform, whereas a primitive consumes a point. A routed record needs a signature-compatible invocation or an explicit authored adapter from the current frame. Unknown expressions and incompatible calls must be reported rather than converted to identity operations.

## Complete catalogue: numerical dispatch requirements

The table specifies intended call contracts and decisions still needed. The hinge, sphere and contraction bodies have the limited numerical evidence above; one situated hinge call additionally has the DWI-APPLY evidence. The remaining call forms are not yet lowered. Existing N1 helpers can support explicit bindings; their presence does not make the source call compiled.

| Index / key | Typed numerical operands and action | Binding or reuse boundary |
|---|---|---|
| 0 `klein` | Previous surface, current LUT and feedback produce a carrier context; point/anchor queries produce field values. | Reuse quotient canonicalization and nearest-lift distance. N1's scalar geometry average is not the whole surface action. |
| 1 `hadamard` | Complex pair and phase/context produce a complex pair. | First chosen binding is early `H D H`; do not reuse N1's different mixer. |
| 2 `phi` | A declared positive-radius frame and reference radius produce log radius and angle/phase coordinates. | `rho=ln(r/r0)` needs a domain and inverse. N1's extra phase correction is a separate choice. |
| 3 `rk4` | Slot form consumes base frame, preceding slopes, interval and derivative definition; gather form consumes four slots and the base frame. | Typed overloads and stage dependence are required. A scalar angular modifier is not this whole action. |
| 4 `phyllotaxis` | Phase difference, primitive results, LUT and interval produce divergence/placement information. | Early p7 supplies a planar golden-angle seed policy; its chart mapping and evolving action still need bindings. |
| 5 `pinion` | Anchor transport consumes chart point, local-frame increments and controls; return form carries surface/RGBA/LUT state. | Early p8 gives paired transport with seam handling. Both declared roles refer to the current pinion record. |
| 6 `double_dot` | Explicit same-shaped operands and surface context produce a coupled result. | Early p9 proposes Frobenius contraction. N1's `Q:P` is reusable with declared operand extraction, not as an unspecified cross product. |
| 7 `T_shape` | Local point and stem/bar dimensions produce a field value. | Two-box union is an available binding; distinguish its implicit-field quality in overlaps. |
| 8 `pyramid` | Local point and dimensions produce a field value. | Early square-base residual and N1 triangular extrusion are different choices. |
| 9 `circle` | Local 2D point and positive radius produce signed distance. | Existing Euclidean radial expression is reusable. |
| 10 `cone` | Local 3D point and dimensions produce a field value. | Early cone residual and N1 capped-cone distance must not be conflated. |
| 11 `sphere` | Local 3D point and positive radius produce signed distance. | Existing Euclidean sphere expression is reusable. |
| 12 `apex` | Local point and apex position produce unsigned distance. | Do not invent an interior sign. |
| 13 `delta_phi` | Current and preceding unwrapped phases produce a second difference. | State whether divided by time; N1 uses an unscaled difference. |
| 14 `blend` | Typed coupling, growth and primitive values plus weights produce the declared result/frame. | Early scalar interpolation is an available primitive, not a complete operand mapping. |
| 15 `wavefront` | Literal source vector and an encoding definition produce the initial wave/frame. | N1's two-complex-amplitude encoding is an explicit choice. |
| 16 `y_up` | Fourth-slot position or slope plus declared displacement/frame produce a changed slot. | Declare slot meaning; execute two applications. N1 uses two position shifts before evaluating k4. |
| 17 `crystal` | Computed frame and LUT form the channel-bearing state. | Typed formation is an explicit computational action; no physical crystallization claim follows. |
| 18 `inverse_T` | A chosen transform type produces its inverse. | N1 rotation/shear inversion is reusable if that T binding is retained. Invalid/singular cases need policy. |
| 19 `T_transform` | Working frame, crystal context and current parameters produce a transform. | N1's rotation-times-shear is a proposed binding, not the source's only possible T. |
| 20 `jitter` | Generator state or recorded controls plus feedback/mode produce a bit and next generator state. | Xorshift is available; disabled behavior and replay must be explicit. |
| 21 `bst` | LUT, route controls, surface and jitter produce a path and selected index. | Reuse `2*i+1+b` and XOR reversal. Supplied versus field-derived controls are distinct modes. |
| 22 `return` | Carried frame, current LUT, neck/parity and interval produce the next whole state. | N1's additional horizontal increment is not the whole return action. |
| 23 `phase_history` | Previous history, jitter and all four slots produce the next history. | A finite recurrence must declare retained information and approximations. |
| 24 `dichromatic` | Crystal state and parity produce the paired channel values. | Two arbitrary complex values require four real components; labels are not compression. |
| 25 `bayer` | Completed state and output coordinates produce optional readout. | Downstream only, with declared intensity mapping and threshold convention. |
| 26 `bc5` | Suitable two-channel samples and block/layout policy produce optional compressed storage/output. | Not a lossless executable-record format and not a mandatory active recurrence stage. |
| 27 `split` | Encoded frame and control bit form/tag/route paired input. | Must not silently add a third H to the selected hinge convention. |
| 28 `parity` | Declared integer payload or split bits and neck context produce parity. | Population parity and even/odd are different functions despite agreeing for 7/54. |
| 29 `psi` | Epoch, base interval, feedback and current definition produce the logical interval. | Validate the resulting interval; positive base dt alone is insufficient after modulation. |
| 30 `mutation` | Old operator, its field/anchor, old LUT/state and controls produce a next operator definition. | The old mutator body must determine the update, including its own next definition. A fixed rule with one adjustable scalar is narrower. |

The original recurrence does not directly apply resident entries15, 20 and29: its raw seed, session controls and PSI symbol supply those roles. Making their current definitions numerically operative is an explicit integration refinement. Entry26 remains optional. Catalogue coverage must describe actual call paths instead of counting stored names.

## Eight-stage dependency and ordering gates

The [authored cycle](../source_workbench/Dawnwood_Interactive_v0.2/model/cycle.json) controls the original phase sequence. The application compiler must validate that each phase's inputs have producers. Arbitrary phase permutations are not automatically meaningful, and an unknown stage requires a registered numerical meaning.

| Phase | Required inputs | Outputs/dependencies carried forward |
|---|---|---|
| `operator_mutation` | Old whole state/LUT, old mutation and pinion records, controls | New LUT, surface context and working frame. All mutations read the same old snapshot. |
| `log_polar` | Working frame, new PHI record and LUT | Encoded frame. |
| `split_and_hinge` | Encoded frame, jitter/neck, current split/parity/hinge | Paired working frame and parity context. |
| `selected_operator` | Route inputs, neck, surface, current BST/LUT | Path/index and the result of applying the selected current record. |
| `rk4_four_slots` | Selected frame, interval, derivative and Y-up definitions | Updated frame and four retained slots, with double Y-up on slot4. |
| `geometry_divergence` | Working/encoded frames, surface and current primitive/phase/phyllotaxis/coupling/blend records | Geometry and coupled result. |
| `rgba_crystal` | Coupled result, parity, previous B, four slots and channel/T/inverse definitions | Paired channels, new history and inverse-T state. |
| `surface_return` | Surface, RGBA, current LUT, neck/parity/interval and pinion/return definitions | Next whole state, including the definitions that will act next. |

Optional readout consumes the completed state after return. It must not silently become the next feedback input.

RK4 needs special lowering. The symbolic workbench makes four calls with a slot index and the same base expression, then gathers them. It does not explicitly put `k1` into the slot2 call or `k2` into slot3. A numerical binding must generate the chosen dependent stage computation. Four independent copies of the same derivative evaluation do not implement classical RK4.

The two Y-up applications also require a declared interpretation. Early formalization physical p10 proposes a post-weighted impulse and explicitly distinguishes that choice from changing k4. Unified p12 places the repeated action in the fourth slot. N1 shifts the fourth-stage position twice before evaluating its derivative. These are different bindings; reusing N1's arithmetic requires recording its interpretation.

N1 evaluates geometry inside its derivative and applies its amplitude hinge after kinematic integration. The source cycle puts the hinge before selection/integration and its geometric phase afterward. Calling the existing N1 evolution routine from a source-model loader would preserve N1's schedule; it would not compile the authored source order. Individual field, matrix, integer and topology helpers are reusable. The complete schedule is not interchangeable without a declared profile revision.

## Remaining full-application work

After the numerical bodies, situated call and three-record resident transition, integration still needs the remaining typed `Apply` forms, valid source-cycle lowering, full-catalogue mutation, full paired-state participation and whole-source-state checkpoint continuation. A stable interpreter may execute all of these; self-reference concerns the acting definitions and their updates, not overwriting native GPU instructions.

A later biochemical application must encode its candidate operations, law evaluation, selection, acceptance/rejection, history and strategy changes through those situated definitions. Authoritative scientific laws may remain immutable while the resident computational strategy changes. A correct standalone distance calculator or fixed projection solver is useful evidence for its own task, but does not supply the missing application program.

The verified results are the expression foundation, situated call and bounded resident-definition transition. Actual body, field and placement definitions affect numerical action, and a resident mutator's successor changes later mutation behavior. The remaining catalogue calls, full cycle and complete application remain to be integrated and measured.
