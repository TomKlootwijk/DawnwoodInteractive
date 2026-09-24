# Authored numerical source cycle

The `cycle_v0.1` edition connects all eight phases of the original source cycle through `DWI-RESIDENT-0.2` typed resident calls. It instantiates the original 31 operator identities, carries their live definitions between epochs, evaluates current body/field/placement slots, and returns complex streams, finite history, an actual inverse matrix and Klein-chart state. This is an explicitly authored numerical binding of the source relationships. It is not a biochemical application or a claim that the source PDFs uniquely prescribe these numerical formulas.

The [cycle compiler](../local_lab/source_cycle.py) reads the original [catalogue](../source_workbench/Dawnwood_Interactive_v0.2/model/substrate.json) and [cycle](../source_workbench/Dawnwood_Interactive_v0.2/model/cycle.json). It emits the inspectable [expression bank and call plans](../source_bindings/cycle_v0.1.json), then uses the [v2 resident frontend](../local_lab/source_resident_v2.py) to validate and compile them. Application arithmetic lives in these explicit expressions; the native evaluator supplies generic memory operations, typed dispatch and numerical primitives.

## Source relationships and edition boundaries

Physical page 9 of [Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf) joins body, field and anchor and gives mutation/rebinding dependencies. Pages 10–13 connect implicit routing, channel/history roles, the cycle and whole-state return. Its p16 leaves numerical meanings open. The preserved [symbolic implementation](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py#L82) supplies an executable record of those dependencies, while constructing symbolic calls rather than computing their numerical effects.

This compiler consumes the actual phase array and the actual fourth-slot Y-up count. It rejects unknown, duplicate, missing or improperly ordered phases. It also checks every source index/key and original body/field/placement declaration against the explicitly supported edition. An unfamiliar source-body edit fails rather than silently inheriting its old numerical law. The actual `seed.wavefront` initializes the two complex amplitudes: the original `[0,2,0,1]` means `a=0+2i`, `b=0+1i`. Each must be nonzero for PHI. Carrier query coordinates vary between independently executed instances; their amplitudes are not replaced by a benchmark seed.

The bank has 55 scalar-expression functions and 34 body families: the 31 source identities plus alternative Hadamard, pinion and mutation definitions. A body handle selects a family of typed roles. The pinion family has separate anchor-transport and return roles; RK4 has derivative and combination roles; the hinge has complex and log-polar overloads. Mutable alternatives must implement the complete same interface. Runtime role/signature checks distinguish a valid current definition from an unsupported call.

Selected routing initially supports the six geometric source indices 7–12 through a common selected-action role. Other addresses and incompatible roles fail visibly; addresses are never reduced modulo the record count. The full catalogue being present does not imply that every body runs unconditionally. Source Bayer observation is optional and outside the core; this edition supplies only an optional threshold overload, not a Bayer texture layout. BC5 texture encoding remains unsupported and fails if invoked. Neither optional mechanism is counted as completed packing work.

## Connected phase contract

Each semantic call resolves a current placement expression, computes the nearest-lift distance from the current K chart to that placement, invokes the current field expression, and supplies its result to the current typed body. The initial Klein call sees old K; its newly evaluated K then directly changes the later field queries, including BST and geometry. The carrier field is the declared intrinsic Klein-disk family from [situated application](SITUATED_APPLICATION.md), with guarded effective radius below `0.5`. It is separate from the geometric primitive value calculated by a primitive's body.

| Source phase | Numerical binding and dependency |
|---|---|
| `operator_mutation` | Every target reads the same old instance. The old mutator selects new compatible bodies, including its own successor, with explicit old PSI/dt input. The old pinion transports old evaluated anchors. Rebinding uses the old field and new body/anchor before publication. The new Klein record consumes old returned-chart feedback; the current PSI record derives the positive effective interval. |
| `log_polar` | The current PHI record produces two natural-log radii and two radian angles from the preceding complex pair. Its field contributes explicit opposite phase offsets. |
| `split_and_hinge` | A supplied bit exchanges typed log-polar channels. Parity reads the actual split angles, jitter and neck bit. The current hinge decodes the channels and executes the chosen two-Hadamard expression. |
| `selected_operator` | The current BST body computes `child=2*i+1+bit` from supplied depth/bits with neck reversal; supplied jitter contributes to its routing phase. Dynamic source-index dispatch invokes the selected compatible geometric record, including its live field and placement. |
| `rk4_four_slots` | Derivative evaluations use dependent intermediate states. The configured Y-up calls modify only the fourth slope. The current RK4 combination role receives all four slopes. |
| `geometry_divergence` | All six current primitive values and explicit PSI/dt feed phase-driven phyllotaxis. Delta reads the actual PHI-encoded phase and its encoded history. A Frobenius coupling and convex blend produce the next complex pair. |
| `rgba_crystal` | Current crystal and dichromatic records produce R/G complex streams. The history record consumes all four slopes. T is an explicit positive-definite 2×2 matrix; the inverse record computes its actual inverse. |
| `surface_return` | The new pinion's return overload consumes R/G, all history components and all inverse entries. The current return record applies neck/parity and phase effects. The next image includes the updated records and this complete numerical cycle state. |

Compilation records each phase's half-open instruction range and every typed call in the manifest. Those ranges make it possible to inspect or intervene on a phase without relying on a workload name. The original symbolic RK4 calls all receive the same working expression; its derivative and intermediate-state law are unspecified. The explicitly dependent construction here is the chosen numerical overload, not an assertion that the original Python code already performs numerical RK4.

## Exact numerical choices

### Resident mutation and carrier

The mutation and transport policy extends [the verified three-record binding](RESIDENT_DEFINITIONS.md) to all 31 targets, with handles remapped to typed body families. It additionally couples the old positive PSI/dt directly into mutation: the selection signal adds `0.0005*dt`, and the field-dependent control increment becomes `0.001*dt*(M+0.5*T)`. The first mutator selects its successor. That successor can change hinge and pinion families in the following mutation pass. All targets in a pass continue to use the old controller definitions, independent of traversal order. Other body families retain their previous handle under this initial authored mutation policy.

The carrier remains the unit flat quotient `(u+1,v)~(u,-v)`, `(u,v+1)~(u,v)`, with an orientation bit. Mutation applies the old placement expression to each old anchor before transport. Forward/reverse pinion motion uses the orientation-relative vertical convention. Rebinding can select an expanded disk and changes the radius using the new stored anchor. For surface feedback, the preceding returned chart is canonicalized and located by a nearest lift relative to old K. The current Klein body consumes that local horizontal displacement, its vertical component in the old K frame, and the returned orientation bit, as well as the prior wave and its current field. Its updated K drives subsequent field queries in the same cycle. Surface evolution changes chart coordinates and orientation; it does not replace the underlying metric with an unspecified three-dimensional immersion or establish general smooth tangent covariance.

The effective fields, old body choice, old controller values, wave components and supplied jitter contribute to mutation. Jitter and neck controls are guarded bits. The profile does not invent an automatic physical or random source for them. `dt` is a declared computational interval, not a measured biochemical time.

### PHI, splitting and the double Hadamard

For a complex amplitude `(x,y)`, PHI computes its log radius with the scaled expression

```text
m = max(abs(x),abs(y)); n = min(abs(x),abs(y))
log_radius = log(m) + 0.5*log(1+(n/m)^2), with m>0
angle = atan2(y,x)
```

This avoids squaring a very large or tiny amplitude merely to take its logarithm. Actual scalar evaluation remains FP32. An exact zero complex amplitude fails the declared domain guard. The field contributes `+0.01*d` to the first angle and `-0.01*d` to the second.

The split overload exchanges the two log-polar pairs when jitter is one, then adds small opposite field phase terms. This is a typed channel-splitting choice, not a claim that floating values undergo integer bit shifts. Parity uses the integer parity of `floor(abs(split_theta0-split_theta1))`, XOR jitter, XOR neck. Its separate field phase joins the hinge's supplied phase.

After decoding with `exp`, `cos` and `sin`, the acting hinge evaluates

```text
U_plus(phi)  = H * diag(1,exp(+i*phi)) * H
U_minus(phi) = H * diag(1,exp(-i*phi)) * H
H = (1/sqrt(2))*[[1,1],[1,-1]]
```

`U_plus` is the chosen early [Formalization](../Dawnwood_Interactive_Formalization.pdf), physical p6 Eq7, which is explicitly marked proposed there. The conjugate variant is an authored resident alternative. The cycle does not silently substitute the old native N1 `D(phi)H` update. Split does not add an extra Hadamard.

### Four dependent slopes and active fourth-slot events

For each complex amplitude, the derivative is a damped rotation with `omega=0.2+0.01*d+0.005*(2*jitter-1)` and damping `0.02`. Jitter is a guarded bit supplied directly to each derivative call. The effective interval is `h=dt/(1+0.001*abs(d))`. The plan forms

```text
k1 = f(w)
k2 = f(w + h*k1/2)
k3 = f(w + h*k2/2)
k4 = f(w + h*k3)
```

Each configured Y-up event then applies `ai += eta*ar` and `bi += eta*br` to **k4 only**, where `eta=0.02+0.001*d_yup`. The source count is two. Both shears have numerical effects; they are not inverse operations that cancel. The final current RK4 role computes `w+h*(k1+2*k2+2*k3+k4_modified)/6`.

This is a modified four-stage RK binding. It does not claim classical fourth-order accuracy with the Y-up events enabled. With zero configured events, the dependent-stage construction has the usual RK4 weights for the chosen derivative. Interventions can compare the first three slopes and the modified fourth slope directly through the recorded plan.

### Primitive distance meanings

Let `(x,y,z)=(ar,ai,br)` and `r=0.5+0.01*d_carrier`. For this binding the geometric inputs are computational amplitude coordinates, not physical lengths. The fields use the following declared Euclidean metrics:

| Body | Chosen geometry and distance |
|---|---|
| T | Exact signed distance in `(x,y)` to the eight-edge T polygon. Stem half-width is `0.12`, bottom is `-r`, shoulder is `r-0.12`, bar top is `r+0.12`, and bar half-width is `r`. The nearest boundary segment supplies magnitude; union membership supplies sign. |
| Pyramid side | Exact signed distance in `(x,z)` to the triangle `(-r,0),(r,0),(0,r)`, using all three boundary segments and triangle membership. This is a two-dimensional side, not an invented full pyramid equation. |
| Circle | `sqrt(x*x+y*y)-r` in two dimensions, evaluated with scaled norm arithmetic. |
| Capped cone | Exact three-dimensional distance to a capped cone of base radius and height `r`. In `(rho,z)`, compare the base-disk distance with the clamped lateral segment `(r,0)→(0,r)`; interior membership supplies the negative sign. |
| Sphere | `sqrt(x*x+y*y+z*z)-r` in three dimensions. |
| Apex | Unsigned distance to `(0.01*d_carrier,0,0)`; a point has no claimed inside. |

These are analytic exact-distance claims in the stated metric, subject to finite arithmetic. Executable guards require `r>0` for the signed primitives and `r>0.12` for the T polygon; the apex has no radius requirement. The T is not implemented by taking the minimum of overlapping box SDFs and calling the result exact. Pyramid and cone are not unnormalized plane residuals. The other amplitude component can remain part of the carried wave without being an axis of every geometric body.

### Delta, growth, coupling and channel return

Delta unwraps the actual PHI-encoded angle against its preceding encoded history using `atan2(sin(delta),cos(delta))`, then computes a second difference with declared interval/jitter and field terms. Its returned unwrapped angle becomes the next history sample. This is a nearest-branch convention; it does not infer unresolved rotations exceeding π between samples. It avoids mixing encoded angles with unrelated control-phase history.

Phyllotaxis uses angle `gamma*delta + 0.05*dt*sum(geometry) + 0.01*d`, with the golden-angle constant gamma, to produce a bounded candidate complex pair. Thus current geometry and PSI enter that body directly. The double-dot body applies a Frobenius contraction to the two real 2×2 amplitude arrays, with an explicit field term, while carrying the original pair. Blend uses that contraction, all six geometric values and its field to form a bounded convex mixture. These are numerical choices for the open coupling/growth bindings, not a claim of proven optimization.

The typed RGBA payload has **12 reals**: R is one complex stream, G is another, B is a four-component finite history, and A is a 2×2 inverse matrix. No scalar alpha value stands in for the matrix. History combines its preceding value with all four slopes, jitter and its current field. T has diagonals at least one and a symmetric off-diagonal bounded by `0.02`, so the authored construction is positive definite. The inverse body selects adjugate or Schur evaluation according to its field, with positive-pivot/determinant guards; both branches compute the same mathematical inverse. The current pinion return consumes every inverse entry and every B component.

## Execution and scope

Compile a fresh bundle from the source files:

```powershell
.\Dawnwood-Cycle.cmd compile --output output/my_cycle
.\Dawnwood-Resident2.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 8 --input output/my_cycle/program.bin --output output/my_cycle/gpu_8.bin
.\Dawnwood-Resident2.cmd inspect output/my_cycle/gpu_8.bin --manifest output/my_cycle/manifest.json
```

Use `--backend cpu` without `--device` for CPU evaluation. Pass the returned full checkpoint as the next `--input` to continue. `--cycle` accepts an explicit cycle file, including a deliberate Y-up-count change; invalid phase dependencies fail. `--model` accepts a supported model including its actual wave seed; unbound body/field/placement edits fail. `--instances` changes the number of independent instances. The generated JSON can also be inspected and deliberately edited before compilation through the generic v2 frontend; invoking the source-cycle compiler regenerates the declared edition.

Each instance has 44 state floats and its own 31-record LUT. The state includes current amplitudes, carrier and surface charts, encoded phase history, B history, full T/inverse matrices and retained channel values. Some stored diagnostics and previous-pair values are archival; their presence is not a claim that every scalar independently affects every following epoch. Relevant feedback proceeds through the current wave, chart, encoded phase history, B and live definitions.

The same epoch transaction as the resident component validates all provisional records, applies the complete new table, and commits only after the whole action plan succeeds. Failure rolls back the instance's state and records and freezes its failure checkpoint. Current and next tables stay on the device across epochs. A checkpoint retains the entire function/family bank, call plans, live records and numerical state.

The compile bundle records exact source/model/cycle bytes, the generator, its resident-binding dependency and their hashes. Source phase ranges and typed call traces are included. The [final campaign](../output/source_cycle_2026-09-24/REPORT.md) records 46 complete-cycle CPU/GPU pairs, two RK-prefix pairs, 3,902 independent mathematical cases and sustained 100% reported laptop GPU utilization. The [source audit](../output/source_cycle_2026-09-24/SOURCE_FIDELITY_AUDIT.md) separates static relationships from those measurements; successful compilation alone is not numerical evidence. Optional BC5/Bayer layout work, broader selected-role coverage and a useful domain application remain separate tasks. This finite authored edition does not establish arbitrary program synthesis, unrestricted source expressibility or performance advantages.
