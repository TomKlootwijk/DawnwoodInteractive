# Source-to-kernel map

24 September 2026. Companion to [Architecture study](ARCHITECTURE_STUDY.md). This map distinguishes **source intent**, **chosen numerical binding**, **code behavior** and **recorded observation**. Its correspondence table describes the **preserved DWI-N1-0.5 path**, originally shipped with runtime 0.5.1-rtx1 and retained in runtime 0.6.0-domain1. The latter adds the separately identified [DWI-D1-0.1 domain extension](DOMAIN_KERNEL.md); it does not silently redefine N1. Line references below were rechecked against the source containing both paths on this date.

Source page references use physical PDF pages: [original discussion](../double-slit-theory.pdf), 24 pages; [Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf), 18 pages; [early formalization](../Dawnwood_Interactive_Formalization.pdf), 20 pages. The last document's printed numbering trails the physical page by one after the cover.

## Executable correspondence

**Application integration is missing.** The restored
[original workbench](../source_workbench/README.md) consumes editable catalogue,
cycle and expression definitions. The native runtime consumes numeric options
and packed checkpoints; it does not load that application model. The table below
records individual numerical correspondences, not a working compiler for the
source application. See the [literal application contract](LITERAL_APPLICATION_CONTRACT.md).

| Architectural relationship | Source provenance | Current implementation and exact location |
|---|---|---|
| Whole state includes mutable definitions | Original pp. 14–16; Unified pp. 3, 9, 12–13 | [Snapshot][runtime] line 7 stores configuration, states and operators. [CPU epoch][cpu] lines 10–12 reads old states/operators, constructs changed operators, evolves states using the changed field, then advances the epoch. |
| Situated operator: body, field, location | Unified p. 9, Eqs. 21–25 | [Operator record][operators] lines 58–63 stores location, geometric parameters, program and controls. `dw_field` lines 157–168 evaluates a primitive relative to an N1 record; `dw_apply` lines 169–172 applies the body to its field-conditioned operand. |
| Mutation controller is also mutable | Unified p. 9, final paragraph | [CPU epoch][cpu] line 11 invokes mutation for every operator, including slot 30, using preceding slot 30 as controller and slot 5 as pinion. [Mutation][mutation] lines 173–191 applies that controller's current body and field. D1's appended protected laws return unchanged at line 177. |
| One-bit jitter and implicit routing | Original pp. 4–6, 8, 15, 22; Unified pp. 7, 10 | [Preparation][prepare] lines 78–79 computes jitter and the route; every level evaluates `2*selected+1+b`. Orientation and operator flags/program/seed bits affect `b`. |
| Non-orientable return | Original pp. 12–15; Unified pp. 9–10 | [Wrapping][wrap] lines 86–91 reverses `v` and orientation on odd `u` seam crossings. Lines 92–96 compute N1's four-coordinate inspection embedding. [Combination][combine] lines 111–112 applies return feedback and canonicalization. |
| Log-polar encoding and situated geometry | Original pp. 3–4, 11; Unified pp. 6, 8 | [Field evaluation][field] lines 165–166 uses `exp(rho)`, phase and transported orientation in local primitive coordinates. [Derivative][derivative] lines 53–54 computes the encoded polar pair with operator-controlled phase. |
| Primitive field and pinion colon | Original p. 8; Unified p. 8 | [Primitive dispatcher][shape] lines 118–125 implements six cases. [Geometry and derivative][evolve] lines 28–66 evaluates their aggregate, a chosen Frobenius-style colon binding, blend, selected action and motion; line 34 retains the N1 geometry expression. |
| Four stages with two Y-up events in slot four | Original p. 7; Unified p. 7 | [Preparation][prepare] line 87 evaluates Y-up. [Slope][slope] line 99 adds it twice to the fourth stage's `v` before derivative evaluation; [combination][combine] lines 107–110 uses four weighted slopes. |
| Dichromatic pair, history, inverse T | Original pp. 9–12; Unified p. 11 | [Finish][finish] lines 138–142 updates two complex amplitudes; lines 145–153 computes a 2×2 inverse and feedback/history. The complete [State][types] is 128 bytes, not one RGBA texel. |
| Resident texture operator field | Original pp. 18–19; Unified p. 14 | [Texture storage][texture] lines 5–25 preserves each 64-byte operator across four integer texels. Lines 28–44 stage two mutation controls or 31 evolution operators in workgroup shared memory. |

## Self-reference that is actually present

There are two connected levels. First, values such as phase, history, field and phase response affect operator updates. Second, the mutation update calls the mutation controller's executable scalar body. Because that controller is updated by the same loop, changes to its own body or situated field can affect how future operators change. The CPU and [GPU mutation pass][mutshader] lines 10–12 use equivalent preceding records.

The executable body is a packed eight-instruction scalar program: eight four-bit slots in `Operator.program`. [The interpreter][body], lines 147–156, supports identity, adding/subtracting gain, multiplying coupling, sine, cosine, absolute value, negation and squaring. Runtime mutation currently changes the first nibble between add/subtract or sine/cosine when its jitter bit is one. It also changes position, phase, gain, shear, seed and orientation flag. This changes executable behavior, not merely a label or visualization.

The boundary is equally concrete. Program length, opcode meanings and native update formulas remain fixed. Runtime mutation does not rewrite the interpreter, insert arbitrary new instructions, change its own native scheduling, or autonomously allocate a larger tree. Its controller is self-acting **within this declared language**. Radius, height, kind, coupling, `du`, `dv` and `mutationRate` are record parameters but are not rewritten by `dw_mutate` as currently implemented. Externally editing a checkpoint can change more record values than native mutation changes during an epoch.

Feedback also has a defined sampling structure. For operator `i`, the CPU uses state indices `(17*i+epoch) mod count` and `(31*i+epoch+1) mod count`, implemented without shader integer overflow by [feedback indexing][feedback] lines 80–85. These are deterministic population samples, not spatial nearest-neighbor selection or a reduction over every state. The field couples the population through shared evolving definitions, but “whole state” does not mean every state word is read by every operator each epoch.

## The two-Hadamard difference

The early formalization's physical p. 6, Eq. 7, proposes

\[
U_{early}(\phi)=H\begin{pmatrix}1&0\\0&e^{i\phi}\end{pmatrix}H,
\qquad H=\frac{1}{\sqrt2}\begin{pmatrix}1&1\\1&-1\end{pmatrix}.
\]

The current [finish code][finish], lines 138–142, first computes `H(a,b)` and then rotates its two outputs in opposite directions:

\[
U_{current}(\phi)=
\begin{pmatrix}e^{i\phi}&0\\0&e^{-i\phi}\end{pmatrix}H.
\]

These are different equations. At zero phase the early formula is identity and the current formula is H. Both ideal matrices preserve pair norm, but matching that invariant does not make their behavior equivalent. A H in each successive epoch also does not generally reconstruct the early same-epoch expression when phase and the operator field evolve between epochs.

Unified p. 5 leaves the hinge/pinion law as an editable named binding, and p. 16 lists it among open numerical meanings. Therefore the current implementation can be described as a chosen binding of that later expression vocabulary; it must not be described as an implementation of the earlier two-H formula without changing the equations and versioning the profile. The D1 extension retains this N1 hinge formula.

## Where the closure is narrower than the proposal

**Amplitude-dependent feedback.** Current amplitudes feed their next amplitudes and the stored norm `energy`. `dw_finish` line 128 supplies previous energy to operator 15 when forming phase. Its field, routing, motion and mutation paths do not directly consume `ar`, `ai`, `br`, `bi` or a cross-stream interference observable such as `Re(a*conj(b))`. The controller receives fields/history/phase response instead. Thus the code has a real recurrent operator/state loop, but its two complex streams have a much narrower influence on the changing architecture than the source's broader wave-resonance description suggests. D1 adds a domain-error return path, not this missing amplitude-sensitive path.

**Geometry and routing.** The current route is determined by bits and transported orientation at [preparation][prepare] line 79. Operator fields affect evaluation after selection; selection is not a direct distance comparison against each operator's SDF. Positions move on the wrapped chart while tree indices and configured depth remain stable. Geometric relocation therefore changes field action but does not reorder the implicit tree. D1 visits its protected laws in declared order while retaining this core route. A profile in which geometry determines instruction choice would need to specify that additional rule.

**Field semantics.** The native geometry evaluates primitive scalar fields, then passes them through mutable bodies. Arbitrary sine, square, gain and composition operations do not automatically preserve a signed-distance metric. The code provides an intrinsic chart rule, local fields and a four-coordinate embedding, rather than a demonstrated global inside/outside Euclidean SDF for an embedded Klein bottle in three dimensions. The source intent remains a common geometric operator field; the numerical metric and executable consequences need their declared binding.

**Native scaffolding.** The primitive dispatcher, chart transition, instruction meanings, derivative equations, RK weighting, matrix construction, mutation sampling and epoch schedule are native rules. LUT entries influence many of them, but their complete algorithms are not encoded as freely replaceable SDF programs. Likewise, phyllotaxis appears explicitly in [initialization][initial] lines 6 and 9; a proven ongoing golden-angle surface arrangement or guaranteed warp locality does not follow from those seeds.

## Packing, counts and evidence

The active ABI asserts [128 bytes per State, 64 per Operator and 64 per Config][abi], lines 5–7. Old/new buffers preserve epoch dependencies. Integer texture storage preserves operator words exactly; shared storage holds the core records for a dispatch. This realizes important residency and mutable-LUT parts of the architecture without implementing BC5 as an exact instruction/state codec or establishing permanent hardware-cache residency.

Consequently, the [measured 43,609,664-state RTX population](../output/rtx5070ti_laptop_2026-09-24/REPORT.md) counts these complete records under the stated memory policy. It cannot be compared as the same kind of element to the hypothetical single-byte texels or undefined “operational states” in original pp. 20–22. Page partitioning and double buffering do not multiply compression or semantic capacity.

The campaign's per-epoch CPU/GPU comparisons establish agreement for the exercised numerical binding. Its active-operator sensitivity checks establish that the inspected bodies can affect outputs in those cases. Capacity, full readback and sustained load establish practical execution limits and health observations. None alone establishes a useful domain specialization, autonomous optimization, universality or every property of the source's complete proposed closure.

## The explicit D1 extension

[DWI-D1-0.1](DOMAIN_KERNEL.md) now gives four state slots an identified task meaning and appends protected affine laws to the same LUT. The [domain helpers][domain] at `numeric_types.inc` lines 131–146 evaluate exact analytic affine fields in normalized coordinates. The [projection and coupling functions][domain_evolve] at `numeric_evolve.inc` lines 3–34 use the current mutable operator 30 to regulate correction; lines 159–167 return residual error to `state.field` instead of overwriting task coordinates with the N1 inspection embedding. Its `DWKD0001` checkpoint identity separates that binding from N1.

This adds a practical native constraint specialization and a domain-to-controller feedback path. The application algorithm remains native rather than composed from the source application's acting records. The source permits a stable evaluator; the missing part is executable representation of the application definitions, not self-rewriting host instructions. D1 also does not introduce the earlier two-H mixer. [Measured domain results and their numerical limits](DOMAIN_KERNEL.md#recorded-domain-validation) belong to D1's own evidence; the previous N1 saturation figures remain attributed to N1.

[runtime]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/runtime.hpp#L7
[cpu]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/src/cpu.cpp#L10
[initial]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/src/cpu.cpp#L6
[types]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L48
[operators]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L58
[mutation]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L173
[feedback]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L80
[wrap]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L86
[field]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L157
[shape]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L118
[body]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L147
[domain]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc#L131
[domain_evolve]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L3
[evolve]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L28
[derivative]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L36
[prepare]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L76
[slope]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L94
[combine]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L102
[finish]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc#L117
[texture]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/shaders/operator_texture.inc#L5
[mutshader]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/shaders/mutate.comp#L10
[abi]: ../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric.hpp#L5
