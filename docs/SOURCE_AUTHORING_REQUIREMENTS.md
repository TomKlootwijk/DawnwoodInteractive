# Source application authoring requirements

The source-authoring interface connects explicit edits to situated operator declarations to the complete numerical source cycle. The resident evaluator executes the resulting expressions, resolves live body/field/placement handles, mutates records from an old snapshot, and checkpoints the resulting state. One explicitly registered additional operator can be reached by the extended implicit route.

This document records the source obligations and the accepted bounded interface. The [authoring campaign](../output/source_authoring_2026-09-24/REPORT.md) now provides separate source-edit, CPU/GPU, continuation, rejection, mathematical and saturation evidence. Its [final recompilation audit](../output/source_authoring_2026-09-24/final_recompilation_audit.json) connects current compiler sources to the exact executed program bytes. Earlier source-cycle and enzyme measurements do not automatically validate this authoring path or arbitrary new user expressions.

## Original requirements and their scope

Page numbers below are physical PDF pages. The original discussion, the first technical formalization and Unified v0.2 have different roles; proposed numerical choices are not retrospectively attributed to the user.

| Requirement | Direct source evidence | Original executable evidence |
|---|---|---|
| The computing core carries and changes operators, rather than only displaying their geometry. | [Original discussion](../double-slit-theory.pdf), p14, user's 08:23 statement: operators are defined as SDF operations, carried on the Klein surface by the double pinion, and acted on by jitter. | [`kernel.py`](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py), `Operator`, `apply`, and `_operator_mutation`. |
| Body, field and surface position belong to the same situated record and remain visible to operator change. | [Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf), p9, sections 7.1–7.2, equations 21–25. | `kernel.py`, lines 45–46 and 82–94: record construction, old mutation/pinion records, changed body, anchor and field. |
| An author can replace a definition and register a further situated operator. | Unified v0.2, p10 section 8.2; p16 section 14.1 names `set_body` and `add_operator`, with the next circulation using the resulting record. | `kernel.py`, lines 54–77: unoccupied nonnegative indices, body replacement and field rebinding. |
| A registered operator can be selected through the same implicit route. | Unified v0.2, p10 equations 26–28 and p13 section 11.2. The implicit child relation is `2*i+1+b`; reversal XORs the route bits. | `kernel.py`, lines 106–119: look up the actual source index and apply its current record; an absent address remains a named unresolved read, never a modulo alias. |
| Changed definitions remain part of the returning state and continuation. | Unified v0.2, p12, complete circulation; p13 section 11.1, equation 36. | `kernel.py`, `_surface_return`, `snapshot` and `from_snapshot`, including live records and expression graph. |
| Missing numerical meanings must be bound explicitly. | Unified v0.2, p16 section 14: the source leaves several laws open; authoring expressions require supplied numerical meaning. | [`model/bindings.json`](../source_workbench/Dawnwood_Interactive_v0.2/model/bindings.json) retains open bindings; [`WORKBENCH.md`](../source_workbench/Dawnwood_Interactive_v0.2/docs/WORKBENCH.md) describes the evaluator attachment points. |

The original workbench is symbolic. It can accept arbitrary JSON as authoring material without claiming to numerically execute an unknown expression. The numerical implementation must therefore reject an unresolved declaration rather than silently giving it the old symbol's law.

The source user's p12, 08:16 statement explicitly puts rasterization, raymarching, raytracing and square output fields outside the core and calls Bayer output optional. No GUI, image output or sonification is needed to satisfy this milestone. BC5 packing and cache placement are separate device-representation work; neither substitutes for executing an edited definition.

The original discussion's claims of universal or quantum computation on pp 13–16 and 22–23 occur in the generated responses. The user's question on p22 is not a constructive universality proof. The [early Formalization](../Dawnwood_Interactive_Formalization.pdf), physical p11 section 10.3 and p15 section 14.2, explicitly separates its finite self-referential interpreter from arbitrary self-modifying code and universality. Selecting among authored executable variants is a valid declared finite mechanism; it is not unrestricted synthesis of new instructions.

## Existing boundary being addressed

The original numerical edition in [`source_cycle.py`](../local_lab/source_cycle.py), `validate_sources`, accepts exactly the original 31 identities and original body/field/placement declarations. It rejects unfamiliar declarations and record parameters. Its selected-action role 99 initially covers only the six geometric primitives. These checks protect against silently miscompiling source edits, but they also prevent the original workbench's authoring operations from reaching the full numerical cycle through that interface.

The generic [`source_resident_v2.py`](../local_lab/source_resident_v2.py) already compiles explicit expression banks and typed families. Editing a resident definition directly is possible; that is distinct from binding an edit to its actual source declaration. The new modules divide the source-facing work as follows:

| Module | Authoring responsibility | Validation status in this document |
|---|---|---|
| [`source_slot_bindings.py`](../local_lab/source_slot_bindings.py) | Resolve explicit edits to existing source body, field and placement slots against the final generated typed bank. | Recorded direct rejection checks and separate full-cycle body/field/placement interventions. |
| [`source_catalogue_extension.py`](../local_lab/source_catalogue_extension.py) | Add one explicitly bound selected operator and extend its implicit route to five supplied bits. | Recorded five-bit routes, source-index identity, mutation retention and runtime rollback. |
| [`source_program.py`](../local_lab/source_program.py) | Feed the actual authored declarations through the appropriate source-cycle/application builder, resolution and resident compilation stages; retain their provenance. | Final CLI compilation, execution, inspection and program-equivalence audit; [commands](SOURCE_PROGRAM_AUTHORING.md). |

Temporary construction of the canonical baseline may be an implementation detail. The delivered record assertions, hashes and compilation inputs must describe the actual authored model, not a substituted model that hides the edits. An unchanged source/binding invocation should retain the previous executable bytes; that is a required compatibility measurement, not an assumption.

## Existing-record slot bindings

The accepted external registry has this shape:

```text
{
  "profile": "DWI-SOURCE-SLOTS-0.1",
  "entries": [
    {"key": operator_key, "slot": "body" | "field" | "placement",
     "declaration": exact_source_JSON, "binding": slot_binding}
  ]
}
```

This is structural notation, not a runnable JSON example. `declaration` must match the actual source slot structurally, including its complete semantic content. An inline declaration is exactly `{"resident_binding": slot_binding}`. Inline and registry definitions for the same slot are ambiguous and must be rejected. Duplicate, unused, unknown or mismatched registry entries must not be ignored.

A body binding contains:

```text
{
  "kind": "body",
  "mutation_policy": "declared_variants",
  "variants": {
    family_name: {"inherit": true, "roles": {role_number_string: pure_XIR_binding}}
  }
}
```

Every compatible family sharing the record's body interface must be explicitly listed. Mutation must not escape an authored edit by switching to an unaccounted-for alternative. `inherit: true` explicitly retains roles not replaced in that family; without it, every role needs a binding. Role keys are canonical unsigned-integer strings. A replacement retains the required ordered input names, output names, widths and interface. Original preconditions must remain an unchanged prefix of the replacement's `requires`; additional guards may follow. An incompatible edit fails rather than changing an unrelated caller's interpretation of its arguments.

Field and placement bindings contain `kind`, `function` and `mutation_policy`:

```text
{"kind": "field" | "placement", "function": pure_XIR_binding,
 "mutation_policy": "preserve_program"}
```

`preserve_program` retains that slot's authored program handle during mutation. It does not freeze the complete record: the authored mutation can still change anchors, radii, controls and generation. The action must resolve the current retained program with its current arguments. This is an explicit mutation policy, not a claim that every authored field program synthesizes its own successor.

A pure XIR binding uses ordered `inputs`, named `outputs`, optional `requires`, and optional `source`, `meaning`, `status` metadata. Its expressions are finite numeric constants, named inputs or the supported arithmetic-expression objects. Metadata documents the intended law; it does not itself establish distance exactness, units or scientific validity. Preconditions execute, and failed preconditions retain the resident failure/rollback behavior.

The enzyme application's protected roles 0 and 101–104 must retain their fixed scientific law identities across compatible families. Authoring its role 100 proposal is a separate operation. A body edit is not permission to silently alter conserved totals, the domain metric, objective or acceptance law while retaining the old scientific label.

## One additional situated operator

The accepted extension design preserves the original 31 source identities and adds one unique record at an unused source index in 31..62. Those indices are the fifth level reached from root 0 using five bits. An index is an identity, not an ordinal; it must not be reduced modulo 32.

The added body has an explicit common selected-action interface:

```text
{"resident_binding": {
  "kind": "selected_body",
  "function": pure_XIR_binding,
  "mutation_policy": "preserve_family"
}}

role: 99
inputs:  ar, ai, br, bi, routing_phase, field_distance
outputs: ar, ai, br, bi
```

The field and placement use the inline `preserve_program` schema above. Their ordered contracts are `dx,dy,radius -> distance` and `u,v,orientation -> u,v,orientation`, respectively. Their metric and canonicalization obligations remain part of the authored binding; giving an arbitrary scalar the output name `distance` does not prove it is an SDF.

The record supplies all 20 finite named parameter values from the inherited record ABI:

```text
anchor_u, anchor_v, anchor_orientation, radius, phase_gain,
shift_u, shift_v, placement_scale, control, du, dv, feedback_gain,
last_mutator_field, previous_body_handle, last_pinion_field,
reserved_0, reserved_1, reserved_2, reserved_3, reserved_4
```

`preserve_family` retains the added program family while the common old-snapshot mutation still advances its record values and generation. This initial extension does not claim arbitrary family growth or new instruction generation during execution. Existing custom BST-body overrides are incompatible with the extension's changed five-bit routing contract and must fail explicitly unless a future version supplies a declared compatible replacement.

The proposed demonstration is a source-authored amplitude-budget projection on a ball in `C²`, identified with four-dimensional Euclidean real space by `w=(ar,ai,br,bi)`. For declared radius `R>0`, its signed distance is `||w||₂−R`, and its nearest feasible amplitude is `w*R/max(R,||w||₂)`. The zero vector is included and needs no division by zero. This formula states the intended exact-arithmetic task; the final authored expression, its units, any explicit dependence of `R` on carrier context, guards and FP32 error still need to be recorded and measured.

This amplitude-space ball is separate from the Klein carrier field used to situate the operator. It is a computational constraint/projection, not a rendered sphere, a biochemical conservation law, or a quantum claim. The five-bit route must invoke the added record's actual current field, placement and body inside the same selected-operator stage and return its consequences through the remaining source cycle.

The projection's bound applies to its immediate output. RK4, geometry, RGBA and surface return subsequently transform that output; the selected-stage projection alone does not establish a bound on the final returned amplitudes. The evidence must identify the inspected stage and cannot silently promote a local operator invariant into a whole-cycle constraint.

## Explicit finite limits

The symbolic workbench permits additional nonnegative integer indices without a fixed catalogue cap. This numerical edition does not inherit unlimited symbolic resources. The [resident contracts](RESIDENT_V2_ABI.md) bound the executable representation:

| Resource | Bound relevant to this milestone |
|---|---|
| Records |32 total; original 31 plus one extension. |
| Route |Up to five explicitly supplied bits for the extension; at depth 5, source indices 31..62. |
| State |64 FP32 values per independent instance. The base cycle has 44; the extra route bit makes 45. |
| Enzyme plus extension |The current enzyme state already has 64 values. A naive extra route value would exceed the bound and must be rejected, not silently dropped or packed without a declared contract. |
| Function bank |256 functions maximum. |
| Body families |256 families maximum; at most 32 methods per family. |
| Pure expression function |256 instructions, 64 inputs, 32 outputs maximum. |
| Call plans |4,096 instructions per mutation/action plan and 256 frame registers. |

Every lane remains an independent substrate instance with its own records. These limits and instance semantics do not prove unrestricted expressibility, a shared global operator field, or a scaling advantage.

## Required validation before declaring the milestone complete

The following acceptance obligations are mapped to results and limits in the [campaign report](../output/source_authoring_2026-09-24/REPORT.md). They remain necessary for any further edition; passing finite fixtures does not verify arbitrary authored programs:

1. **Source fidelity:** retain exact UTF-8 source bytes, declarations, registry entries, binding hashes and source-to-program mapping. Reject changed-but-unbound slots, mismatches, duplicate/unused entries, unknown expressions and incompatible role contracts.
2. **Default compatibility:** compile the unchanged cycle/application through the wrapper and compare complete program bytes with the established edition. Record any metadata-only difference explicitly.
3. **Acting definition changes:** separately edit a body, a field and a placement. Show their actual numerical consequences through the full cycle. Structural ancestry alone does not prove a nonzero effect; preserve null controls and declared ablations.
4. **Mutation coverage:** demonstrate an edited body remains covered after switching to every reachable compatible family. Show custom field/placement handles survive their declared policy while anchors/record values can still evolve. Preserve old-snapshot and delayed self-change semantics.
5. **Additional record routing:** reach the actual new source index with five bits, exercise neck reversal, and check missing indices or incompatible interfaces fail instead of aliasing. Verify its current body/field/placement all enter the action.
6. **Application mathematics:** compare the authored amplitude-ball distance/projection with an independent Euclidean four-dimensional reference, including zero, inside, boundary and outside cases, and declared input limits. Check the complete cycle intervention separately from the isolated mathematical function.
7. **Execution and continuation:** retain paired CPU/GPU checkpoints, status/validation receipts, resume equivalence, reverse-target equivalence where applicable, and failure rollback. A successful compile alone is not execution evidence.
8. **Resource accounting:** reject the 65-state enzyme/extension combination and out-of-range catalogues/plans explicitly. Do not make throughput, saturation or memory-capacity claims from older workloads.

No persistent test suite was added. Existing checks and retained direct experiments provide this edition's evidence. That milestone supplied its application wiring through versioned builders. The subsequent [source graph interface](SOURCE_GRAPH_PROGRAM.md) now supplies complete named mutation/action wiring and declared heterogeneous computed calls; its [separate requirements audit](SOURCE_GRAPH_REQUIREMENTS.md) and [campaign](../output/source_graph_2026-09-24/REPORT.md) establish that later scope. Optional codecs and broader physical/universality claims remain separate obligations, not silently completed by this milestone.
