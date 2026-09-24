# DWI-D1-0.1: native domain fields in the Dawnwood recurrence

Runtime `0.6.0-domain1` adds an optional, explicitly identified numerical profile to the existing C++/Vulkan kernel. **DWI-D1-0.1 carries four task coordinates in each live state, evaluates immutable affine domain laws in the operator LUT, and uses the existing mutable situated controller to regulate their cyclic projection.** Domain violations also affect geometry and return to operator mutation. This is native computation in the shared equations, not a GUI or a Python replacement for the recurrence.

The [source's Unified definition](../Dawnwood_Interactive_Unified_v0.2.pdf), pp. 3, 9 and 12–13, supplies the architectural relationship: situated definitions act on state, the changing operator field returns with that state, and the operator changing definitions is itself in the field. Original [discussion pp. 12–16](../double-slit-theory.pdf) supplies the author's self-referential SDF computing intent. The affine laws, task slots and projection formulas below are **new declared operational bindings**, not equations retrospectively attributed to those documents.

## Profile boundary and storage

| Item | N1 behavior | D1 behavior |
|---|---|---|
| Reported numerical profile | `DWI-N1-0.5` | `DWI-D1-0.1` |
| Checkpoint magic, first eight bytes | `DWKN0003` | `DWKD0001` |
| State `px,py,pz,pw`, words 16–19 | Four-coordinate inspection embedding | Four normalized task coordinates `z0,z1,z2,z3` |
| Operator 0 flag bit 30 | Unset | Set; enables domain semantics |
| Operator 0 `reserved` | Existing numeric record field | Exact FP32 integer law count, 1–32 |
| LUT | Existing configured catalogue | 31 mutable core records followed by exactly the declared protected laws |
| Routing | Configured implicit tree | Depth 4, confined to core indices 0–30 |

State, Operator and Config remain 128, 64 and 64 bytes. The different magic is essential: unchanged byte widths do not make the meanings interchangeable. The new reader rejects mismatches between magic and operator-0 mode marker. The previous RTX executable remains separately available and rejects the new magic.

The carrier still uses `(u,v)` and its orientation bit. Log radius, phase, paired amplitudes, history, inverse-T coefficients and four kinematic slopes retain their existing roles. D1 does not store the inspection embedding in the task slots; it could be recomputed from the carrier when explicitly needed. `Config.reserved0/1` retain their transient Vulkan partition/stage roles and never encode the domain profile.

An appended law is a protected `Operator` record:

| Fields | D1 law meaning |
|---|---|
| `flags` bit 31 | Protected law; mutation returns this record unchanged |
| `kind` | 0: equality, 1: halfspace, 2: slab |
| `phase,gain,coupling,shear` | Four-component normal `a` |
| `du` | Offset `b` |
| `dv` | Nonnegative slab halfwidth `w` in raw residual units |
| `program` | Zero; scientific coefficients are not passed through mutable scalar bytecode |
| `u,v,radius,height` | Valid ABI fields; the law evaluator uses task coordinates rather than carrier displacement |

Protection includes seed, anchor and all coefficients. Law anchors do not select a law or change its domain distance: every law is visited in declared order. The mutable core controller is situated on the Klein carrier and its body/field still influence action. This is a specific integration boundary, not full geometric self-definition of the scientific law evaluator.

## Exact field definitions and task metric

For task coordinate `z`, define `r=a·z-b` and `n²=a·a`. The three law fields are

\[
d_{eq}(z)=r/\sqrt{n^2},\qquad
d_{half}(z)=r/\sqrt{n^2},\qquad
d_{slab}(z)=(|r|-w)/\sqrt{n^2}.
\]

The equality is satisfied at zero; the halfspace and slab are satisfied when their fields are nonpositive. Their nonnegative violation measures are respectively `abs(d)`, `max(d,0)` and `max(d,0)`. Each analytic field has the stated Euclidean distance meaning before rounding. The authoring compiler requires strictly positive slab halfwidth. Raw native validation also accepts zero, which degenerates to unsigned distance to a hyperplane rather than a slab with an interior; use equality for that authored relationship. Their mean violation is a diagnostic/coupling scalar; it is not claimed to be an exact distance to the intersection.

The compiler defines `z_i=x_i/scale_i`, so distances refer to the Euclidean metric in **normalized coordinates**. Its input normals and offsets are already expressed in that coordinate system. To encode a physical affine equation `sum(c_i*x_i)=b`, supply `a_i=c_i*scale_i`. Changing scales without transforming the equation changes the problem. Returned physical values are `x_i=z_i*scale_i`; the source definition records coordinate names, units, scales and assumptions.

The current profile accepts affine equalities, halfspaces and slabs. Nonlinear enzyme kinetics is not silently treated as an exact SDF or compiled into this vocabulary. The separate [domain field library](DOMAIN_FIELDS.md) distinguishes such residual models from exact affine fields.

## One native epoch

The existing mutation-then-evolution ordering remains. During mutation, protected laws are copied unchanged. Core operator 30 continues to control mutation through its current body and situated field, and is itself updated by the preceding controller record.

During evolution, mean domain violation is added to the mean of the six primitive fields **before** the existing operator-0 application. Consequently task error participates in the kinematic/phase/history machinery. The existing RK stages, fourth-stage double Y-up, hinge action, inverse transformation and history update still execute.

At the end of the state update, the kernel retains the previous task coordinates and performs one ordered sweep through the laws. For each law it recomputes distance on the coordinates produced by the preceding projection. With current controller 30, it evaluates

\[
h=Apply(z, O_{30}, d(z)),\qquad
\lambda=\mathrm{clamp}(0.6+0.35\sin h,\;0.25,\;0.95).
\]

`Apply` here is the existing scalar-body plus situated-field evaluator; its carrier inputs come from the same evolving state. It is not a detached random relaxation setting. Define signed projection excess `e` as `r` for equality, `max(r,0)` for halfspace, and `r-w`, `r+w` or zero for a slab according to whether `r>w`, `r<-w` or the point is inside. Then

\[
z\leftarrow z-\lambda\,(e/n^2)a.
\]

The kernel finally stores `state.field = preprojection_geometry_result + postprojection_mean_violation`. That returned field is read by subsequent mutation. The practical connection is therefore task error → acting core definitions → controller-modulated task correction → returned task error. Scientific law coefficients are protected while executable strategy changes.

This is cyclic relaxed projection over a convex affine constraint family with an evolving controller. The native projection algorithm, permitted law kinds, update order and controller response formula remain fixed code. There is no implemented rollback program, optimality objective, arbitrary program synthesis, reaction simulator or proof that the chosen controller outperforms constant relaxation.

## Compiler, execution and audit

[local_lab/specialize.py](../local_lab/specialize.py) compiles an authored JSON definition into a D1 checkpoint. Its declared keys include four coordinate names, units/scales, initial values, optional population spread, affine constraints, source links, assumptions and a tolerance. Lane zero retains the supplied proposal exactly before FP32 packing; other lanes explore the declared neighborhood from a recorded seed. These are computational candidates, not fabricated measurements.

Use a distinct output directory for each experiment:

```text
python local_lab/specialize.py --example enzyme_repair --count 257 --epochs 64 --stride 16 --controller live --output output/my-domain-run
```

The [native definitions](../domain_knowledge/native) include `enzyme_repair` (conserved pools and a selected complex-concentration band), `buffer_design` (a declared logarithmic activity window), `resource_allocation` (budget and minimum allocations), and `metabolic_flux` (toy steady-state balances and bounds). Their parameters are authored examples with stated sources and assumptions. Use `--spec path/to/domain.json` for another four-coordinate affine definition; a new domain name alone does not establish new scientific semantics.

The compiler uses the separately built `bin/windows-domain/dawnwood.exe`. It records the definition, invocation, commands, executable hash, checkpoints and returned values. Default verification compares CPU and Vulkan for eight epochs from the actual D1 checkpoint. Advancing the GPU then produces native checkpoints; Python only initializes/serializes them and independently audits the returned task coordinates. It does not perform their projection updates.

The audit evaluates both the **packed FP32 coefficients** and the **original authored JSON coefficients** in float64 on the returned task coordinates. Success requires every candidate to pass both sets at the declared tolerance; satisfying a rounded replacement equation alone is insufficient. Reports separate packed/authored violations and feasible counts, lane-zero values and law-record identity. `solutions.csv` contains physical coordinates and both maximum violation measures. A completed but nonconverged or authored-precision-rejected run returns exit code 2; failure to find a feasible point is not an infeasibility proof. Native health, backend agreement, unchanged law bytes and task feasibility answer different questions and must remain separately reported.

Controller modes support direct comparison: `live` uses mutable core feedback; `frozen` freezes that field; `edited` changes operator 30's initial body; `constant` freezes feedback and configures its body to return zero, giving relaxation 0.6. None guarantees that adaptive behavior is better. Compare task residuals at equal work and retained inputs.

## Validation envelope and evidence

The native reader checks record counts before indexing, an exact law count 1–32, exactly `31+count` operators, depth 4, marker placement, protected laws, kind 0–2, zero law program, nonnegative halfwidth, finite values, valid carrier fields and positive legacy shape dimensions. Normal squared length must be within `[1e-12,1e12]`. Mode bit 30 is permitted only on operator 0; law bit 31 is forbidden on core records and outside D1. These bits now have declared semantics in the new runtime.

The authoring compiler additionally limits numeric input magnitudes and the initial normalized coordinate envelope to `1e6`. These are input bounds, not a theorem that every generated trajectory stays bounded. Handcrafted checkpoints can bypass the compiler's tighter magnitude envelope but remain subject to native structural/finite checks and subsequent health reporting. Source provenance remains in the retained definition; the compact binary law record is not a complete scientific citation container.

Implementation locations are [numeric_types.inc](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_types.inc) for domain fields/protection, [numeric_evolve.inc](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/numeric_evolve.inc) for coupling/projection, and [driver.cpp](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/src/driver.cpp) for validation, checkpoint identity and reported profile. Actual success claims require the dated run's command receipts, comparisons and independent constraint audit. The earlier RTX saturation campaign validates N1, not this newly changed profile.

## Recorded domain validation

The 24 September 2026 RTX runs independently audit all 257 returned task states. All satisfy their declared `2e-5` normalized-distance tolerance: [enzyme repair](../output/domain_kernel_2026-09-24/enzyme_live/result.json) after 64 epochs, and [buffer design](../output/domain_kernel_2026-09-24/buffer_design_live/result.json), [resource allocation](../output/domain_kernel_2026-09-24/resource_allocation_live/result.json) and [toy metabolic flux](../output/domain_kernel_2026-09-24/metabolic_flux_live/result.json) after 128 epochs. Each report confirms unchanged protected-law records. The subsequent dual audits also pass both authored and packed equations for [enzyme](../output/domain_kernel_2026-09-24/enzyme_live/authored_and_packed_audit.json), [buffer](../output/domain_kernel_2026-09-24/buffer_design_live/authored_and_packed_audit.json), [resources](../output/domain_kernel_2026-09-24/resource_allocation_live/authored_and_packed_audit.json) and [flux](../output/domain_kernel_2026-09-24/metabolic_flux_live/authored_and_packed_audit.json). These are feasible numerical assignments under the supplied models, not measured biological outcomes or proof of optimality.

Each example's separate 32-epoch CPU/Vulkan comparison reports **zero differing state/operator words at every checked epoch**. The longer [buffer comparison through 128 epochs](../output/domain_kernel_2026-09-24/buffer_full_verify.stdout) passes the unchanged `atol=1e-5`, `rtol=2e-5` acceptance rule but is **not bit-identical**: the first bitwise differences occur at epoch 91. Over the full comparison, maximum absolute error is approximately `1.8427e-38`, with no tolerance failures, integer mismatches, nonfinite values or invalid snapshots.

The retained [epoch-91 analysis](../output/domain_kernel_2026-09-24/buffer_subnormal_analysis.json) locates the initial differences in task words 18 and 19 (`pz` and `pw`), the buffer example's auxiliary coordinates approaching zero near the FP32 subnormal boundary. That checkpoint has 236 differing words and identical operator records. Examples include a CPU value around `1.0016e-38` versus GPU zero, and other GPU values near the minimum normal magnitude. This supports a subnormal-arithmetic explanation for the inspected difference; it does not establish arbitrary-horizon bitwise replay or diagnose every device's floating-point behavior. The differing words and raw reports remain evidence rather than being hidden by a changed tolerance.

A larger [native enzyme workload](../output/domain_kernel_2026-09-24/saturation/epoch-001024.json) completes 1,048,576 states × 1,024 epochs in 112.8336 seconds of GPU device time with healthy full readback. The separate [dual audit](../output/domain_kernel_2026-09-24/saturation/authored_and_packed_audit.json) confirms all returned states satisfy both authored and packed constraints. This is a full-population feasibility/health observation, not a CPU reference comparison of that complete workload or a VRAM-capacity maximum.
