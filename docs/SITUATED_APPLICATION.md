# Situated numerical application

**Binding profile: DWI-APPLY-0.1. Recorded CPU/GPU experiments verify the composed situated application; final compiler-provenance review is in progress. The complete source cycle remains unimplemented by this component.**

This step connects one source operator's placement, field and executable body in a single numerical expression program. Its selected action is the two-Hadamard hinge. The program evaluates placement, canonicalizes the Klein query, chooses the nearest anchor lift, evaluates the record's intrinsic disk field, constructs the phase and executes the record's hinge body. The existing DWI-XIR CPU/GPU evaluator supplies the arithmetic.

This is a situated `Apply` component. It does not implement the complete source cycle, resident operator mutation, metarule self-action or whole-state return. The [full integration ledger](SOURCE_NUMERICAL_INTEGRATION.md) and [literal application contract](LITERAL_APPLICATION_CONTRACT.md) retain those requirements.

## Source relationship and declared choices

The [Unified v0.2 definition](../Dawnwood_Interactive_Unified_v0.2.pdf), physical p9, represents a situated operator as `(body, field, anchor)` and its action as `Apply[operator, wavefront; whole_state]`. Pages8 and13 require changed bodies and positions to affect later application. Page16 leaves the numerical surface, field, phase and pinion functions open. The [original application](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py) preserves those dependencies as expressions; it does not prescribe a universal numerical `Apply` equation.

The [early formalization](../Dawnwood_Interactive_Formalization.pdf), physical pp7-8, proposes a flat Klein quotient, an intrinsic radial field and a field-threshold activation rule. That activation rule is explicitly a proposed profile. N1's `body(value + 0.01*field)` is another particular binding. Neither is silently adopted as a universal law here.

DWI-APPLY-0.1 instead declares a compositional call environment: the current placement determines an anchor, that anchor enters the field query, and the resulting field contributes to the phase operand of the current body. This continuous phase coupling does not suppress the action outside the disk. The numerical choices are inspectable bindings of the source relationship, not uniquely recovered equations from the original discussion.

```text
record placement expression --> anchor and transported frame
query + anchor -------------> canonical point and nearest lift
record field expression ----> signed intrinsic disk distance
state phase + field --------> declared hinge phase
record body + wave pair -----> two-Hadamard result
```

The [binding registry](../source_bindings/situated_v0.1.json) declares the composition as one executable SSA program. Separate definitions are linked into that program; computing placement or field on the host and passing only an already-computed phase would be a narrower claim. Its calls resolve the selected source record's `placement`, `field` and `body` slots, with explicit canonicalization and nearest-lift helpers between them. The application inputs are `u, v, orientation, ar, ai, br, bi, phase`.

The [application linker](../local_lab/source_apply.py) accepts ordered calls with declared argument names and references to preceding call outputs. A call chooses a source `record_slot` or an explicit helper symbol. Slot expressions can resolve through a numerical symbol binding or contain an inline expression. Numeric parameters come from the selected binding defaults with explicit source-record overrides. A call cannot silently ignore an extra argument or bind an unknown source symbol to an invented operation. The manifest preserves the actual selected source slots, resolved numerical definitions and still-unimplemented scope.

## Carrier, units and nearest-lift contract

The chosen carrier is the unit flat quotient

```text
(u,v) ~ (u,v+1)
(u,v) ~ (u+1,-v).
```

For a possibly noncanonical point with transported orientation bit `sigma`, let `m=floor(u)`. Canonicalization gives:

```text
u_c = u-m
v_c = frac((-1)^m * v)
sigma_c = sigma XOR parity(m).
```

The same representation rule applies to the anchor. Coordinates use normalized chart-length units. They are not image pixels, physical biochemical concentrations or coordinates of an ambient three-dimensional solid. If a later binding introduces a length scale, it must transform the field radius and phase-coupling units consistently.

The authored FP32 canonicalizer follows N1's explicit endpoint correction: if a horizontal remainder rounds to exactly one, it uses the greatest FP32 value below one. This finite-precision representation rule is additional to the ideal quotient equation, not an assertion of exact real-coordinate arithmetic.

For canonical query `q=(u,v)` and anchor `a=(a_u,a_v)`, candidate lift `m` gives:

```text
dx_m = u-a_u-m
t_m  = v-(-1)^m*a_v
n_m  = floor(t_m+1/2)
dy_m = t_m-n_m
d2_m = dx_m*dx_m + dy_m*dy_m.
```

Evaluate horizontal lifts in order `m=-1,0,1`; replace the selected candidate only for a strictly smaller squared distance. The first minimum therefore wins. Vertical reduction maps a `+1/2` tie to `-1/2`. With canonical representatives, these three horizontal candidates cover the nearest even and odd lifts, as described in early Eq19. The distance is `d_K=sqrt(min(d2_m))`.

The distance and the local displacement have different transformation rules. The selected `(dx,dy)` is expressed in the query's covering-plane coordinates. To provide an **anchor-local** displacement, transport the transverse component through the selected lift and the anchor's frame:

```text
anchor_frame_x = dx
anchor_frame_y = (-1)^(lift_parity XOR anchor_orientation) * dy.
```

If transporting a tangent vector whose components are already expressed in the query's transported frame, the transverse sign additionally includes `query_orientation`. Point displacement and query-frame tangent components must not be confused. The scalar radial distance is invariant under these signs; asymmetric body operands can reveal an omitted frame transformation.

These are mathematical representation rules. FP32 approximation, branch decisions near equal distances and extreme-coordinate range behavior still require implementation evidence. A chosen nearest-lift vector can be discontinuous where several shortest geodesics meet; this does not make the scalar distance incorrect or establish globally smooth dynamics.

## The field and its exact-distance interpretation

The chosen field is

```text
f(q,a,r) = d_K(q,a)-r,       0 < r < 1/2.
```

The guard is part of this numerical binding. It is not a bound imposed by the original symbolic architecture. The field is negative inside the intrinsic geodesic disk, zero on its boundary and positive outside. No ambient sphere, radial-height offset or three-dimensional Klein-bottle signed solid is claimed.

For this specified quotient and radius range, `f` is mathematically an exact signed distance to the disk boundary. The justification is independent of the evaluator:

1. A nonidentity deck transformation has either a nonzero integer horizontal displacement, or a nonzero integer vertical displacement. Its displacement length is at least one. Vertical translation by one realizes that length at every point. The flat quotient therefore has uniform injectivity radius `1/2`.
2. For an outside point at distance `d>=r` from the anchor, every boundary point is at least `d-r` away by the triangle inequality. A minimizing anchor-to-query geodesic, cut at radius `r`, supplies a boundary point exactly `d-r` away.
3. For an inside point with `d<r`, every boundary point is at least `r-d` away. Extend the radial geodesic through the point to length `r`. Because `r<1/2`, this segment remains in the anchor's injectivity neighborhood and its endpoint is on the boundary, attaining `r-d`.

The implemented FP32 evaluation approximates this mathematical distance. A general edit of the field is not automatically another exact SDF: scaling, arbitrary blending and nonlinear transformations need their own metric interpretation. Field edits that change the radius while preserving the declared guard retain this particular disk interpretation.

## Placement and phase coupling

The placement binding uses the selected source-record index `i`, operator count `N` and the following authored rule:

```text
gamma = 2.39996322972865332
t = i*gamma
s = sqrt((i+1/2)/N)
raw_u = 1/2 + placement_scale*s*cos(t) + shift_u
raw_v = 1/2 + placement_scale*s*sin(t) + shift_v.
```

Canonicalize this raw point with initial orientation zero. The selected Hadamard parameters default to `placement_scale=0.4`, zero shifts, `radius=0.18` and `phase_gain=1`. Placement scale must be nonnegative; index and count must be integral, below `2^24`, with `N>0` and `0<=i<N`. These are declared FP32 binding guards. A scale of zero deliberately permits a constant offset anchor for analytic witnesses.

Early physical p7 supplies a proposed planar phyllotaxis seed; normalization by operator count and mapping into this chart are additional authored choices, following the N1 initialization formula. Portable XIR arithmetic need not reproduce N1's host-native initialization bits. This placement is not a claim of uniform Klein surface-area sampling or optimal cache locality.

The phase composition is explicitly:

```text
hinge_phase = external_phase + phase_gain * field_value.
```

`external_phase` is in radians, `field_value` is in chart-length units and `phase_gain` is in radians per chart-length unit. The supplied phase is not yet produced by the complete pinion/history cycle. If chart lengths are rescaled by a factor `s`, the radius and field scale by `s` and the gain must scale by `1/s` to preserve the same action.

The resulting phase and wave pair enter the record's current two-Hadamard body:

```text
U(phi) = H * diag(1,exp(i*phi)) * H
H = (1/sqrt(2)) * [[1,1],[1,-1]].
```

This is the chosen early-formalization Eq7 binding. No additional H is introduced by an implicit split. The existing historical N1 phase convention remains a different profile.

The application exposes the canonical anchor and query, their orientations, local displacement, selected horizontal lift, anchor-frame transverse coordinate, field distance, effective phase and four action components. Query orientation and the anchor-frame coordinate are diagnostics here: the radial field is symmetric under transverse sign reversal. Their presence does not claim that all tangent dynamics or asymmetric operator fields have been implemented.

## Causality and representation witnesses

The following are independent mathematical fixtures proposed for validating this component. They are not execution results. All fractional coordinates and radii below are dyadic and exactly representable in FP32; constants involving pi still require the usual packed-input and approximation accounting.

For hinge causality, use wave pair `(a,b)=(1,0)`, query `(1/8,1/4)`, anchor `(3/8,1/4)`, radius `1/8`, external phase `pi/4` and gain `2*pi`. The distance is `1/4`, field `1/8` and resulting phase `pi/2`.

This anchor is expressible through the placement binding with scale zero and shifts `(-1/8,-1/4)`. Moving it to the query changes only the horizontal shift to `-3/8`.

| Independent change from that baseline | Mathematical result |
|---|---|
| None | `a'=(1+i)/2`, `b'=(1-i)/2`. |
| Move only the anchor to the query | Field becomes `-1/8`, phase becomes zero and output is `(1,0)`. |
| Change only the field radius to `3/8` | Field becomes `-1/8`, phase becomes zero and output is `(1,0)`. |
| Change only the body to use the conjugate intervening phase | At the unchanged supplied `pi/2` phase, output becomes `a'=(1-i)/2`, `b'=(1+i)/2`. |

The last edit deliberately changes the body law for a causality experiment; it is not another assertion that the unchanged Eq7 produces a different answer. Actual validation must change the corresponding authored slot and recompile, rather than feed a precomputed alternative phase directly.

For a seam-distance counterexample, choose query `(1/8,1/4)` and anchor `(7/8,3/4)`. The correct reflected lift is `m=-1,n=1`, giving displacement `(1/4,0)` and distance `1/4`. A torus-style implementation that omits reflection instead gives `sqrt(5)/4`. This distinguishes the intended carrier from ordinary periodic wrapping.

For a frame witness, change the query to `(1/8,3/8)` with the same anchor and orientation zero. The selected covering displacement is `(1/4,1/8)`, its squared length is `5/64`, and its anchor-local transverse component is **`-1/8`**. A radial distance alone cannot detect the sign error. If an anchor-frame component is exposed, inspect it directly; a future asymmetric local body must consume the correctly transported component.

The equivalent representations `query=(9/8,-3/8,orientation=1)` and `anchor=(15/8,-3/4,orientation=1)` canonicalize to their corresponding original points with orientation zero. Changing either representation must preserve the canonical environment, intrinsic field and resulting action. Do not hold an orientation bit fixed while changing a transported-frame representation and then claim that the same frame was supplied.

The [additional boundary experiment](../output/situated_apply_2026-09-24/boundary_comparison.json) checks the strict first-minimum and vertical tie rules, plus the FP32 greatest-below-one correction. Its three CPU/GPU rows agree bitwise. Agreement at a tie establishes deterministic selection; it does not establish continuity of the selected vector across the cut locus.

The linker requires placement, field and body slots to be structural ancestors of the declared action outputs. This rejects disconnected decorative definitions, but it is not by itself a proof of numerical causality. A zero wave pair produces zero output for every phase; zero phase gain makes field changes ineffectual; algebraic cancellation can erase a dependency. Valid nondegenerate edit experiments must therefore complement the structural check. Norm-only comparison is also insufficient because ideal `H D H` preserves the norm while its complex outputs change.

## Recorded evidence

The [execution summary](../output/situated_apply_2026-09-24/execution_summary.json) contains **11 workloads, 6,177 rows and 98,832 returned FP32 words**, including action components and diagnostic outputs. CPU and Vulkan results are bitwise identical for every workload, including the statuses and zeroed output rows of four intentional failing lanes. This is execution of the composed placement/field/body program, rather than the earlier body-only probes.

All 11 GPU receipts identify the **NVIDIA GeForce RTX 5070 Ti Laptop GPU**, report validation enabled, and record zero validation errors or warnings. The [baseline receipt](../output/situated_apply_2026-09-24/baseline/vulkan.stdout.log) and [invalid-radius receipt](../output/situated_apply_2026-09-24/radius_half/vulkan.stdout.log) show the respective successful and expected-failure paths. Timing is host submission-to-fence waiting, excluding setup and readback; these workloads do not establish saturation performance.

The [independent mathematical comparison](../output/situated_apply_2026-09-24/mathematical_comparison.json) uses packed FP32 inputs/parameters, a binary64 closed complex matrix for `H D H` and a wider 7x7 enumeration of deck transformations for the metric. Its placement reference uses the packed golden-angle constant with binary64 library arithmetic. It does not obtain expected results by replaying the compiled SSA instructions.

| Quantity | Maximum observed error |
|---|---|
| Anchor components | `1.9972320686179046e-8` |
| Intrinsic field value | `6.879503089418648e-8` |
| Complex action components, complete composed reference | `8.989368327494418e-8` |
| Action components using the returned phase as reference input | `8.575936993882038e-8` |
| Relative squared-norm preservation error | `2.2246852641553494e-7` |

The squared-norm metric is `abs(sum(output_amplitudes^2)-sum(input_amplitudes^2))/sum(input_amplitudes^2)` over the four real amplitude components. The reported errors are within the recorded `1e-6` comparison limit. They are finite-sample results, not universal bounds over every valid FP32 input or edited program.

All **771 tested equivalent query representations** produce bitwise-identical returned values to their corresponding base representations. The explicit Klein witness selects `m=-1`, displacement `(1/4,0)` for query `(1/8,1/4)` and anchor `(7/8,3/4)`. Its field is `1/8` at radius `1/8`. The frame witness returns covering `dy=1/8` and anchor-frame `y=-1/8` for query `(1/8,3/8)`; its equivalent query representation produces the same outputs. These results distinguish the reflected Klein identification and transported frame from ordinary torus wrapping.

The recorded intervention experiments change the actual selected source-record slot and recompile. Each uses 1,028 input rows:

| Authored intervention | Anchor changes | Field changes | Effective-phase changes | Action changes |
|---|---:|---:|---:|---:|
| Placement expression adds `1/16` to the horizontal shift | 1,028 | 1,028 | 1,028 | 1,028 |
| Field expression subtracts an additional `1/32` | 0 | 1,028 | 1,028 | 1,028 |
| Body expression negates only output `ar` | 0 | 0 | 0 | 1,028 |
| Zero phase gain, then shifted placement | 1,028 | 1,028 | 0 | 0 |

The field intervention changes its effective disk radius by `1/32`; the recorded radius remains below `1/2`. The body intervention deliberately changes the hinge law for the experiment. Retained source descriptions in copied records are provenance, not a claim that edited mathematics remains the unchanged base formula. The zero-gain control demonstrates the intended causal path: changes to placement and field affect the action through the declared phase coupling, rather than an unrelated hidden modification.

Four expected failing lanes exercise radius zero, radius `1/2`, negative placement scale and invalid query orientation. The corresponding workloads return native exit code3 and matching CPU/GPU failure results. The other lanes, including two valid-orientation rows in the orientation workload, succeed. A failed lane is not counted as a successful application merely because its output row contains finite zeros.

The [final compiler-provenance audit](../output/situated_apply_2026-09-24/compiler_provenance_audit.json) records the compiler hash and exact recompilation of all 13 saved programs, including the additional boundary and launcher examples. Numerical program bytes are unchanged by the provenance correction. The linker records all eager instruction failure sites separately from action ancestry, rejects unused calls, and uses unambiguous call/output identities. [Twenty-two frontend rejection cases](../output/situated_apply_2026-09-24/frontend_rejections.json) include disconnected slots, invalid arguments, unused failing calls and the dotted-name collision counterexample. This finite coverage is not an exhaustive proof of the linker.

## Remaining scope

The verified single-record composition leaves the source's editable cycle, numerical routing, resident operator mutation, mutation of the mutator, coupled history/inverse return and complete application to be integrated. The analytical examples above remain mathematical fixtures; the measured interventions are specifically those listed in the evidence table. External edits and recompilation demonstrate that definitions affect this component; they do not demonstrate the field autonomously rewriting its acting definitions during a PSI circulation.
