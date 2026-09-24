# Resident enzyme application: static source-fidelity audit

24 September 2026. This audit traces the final authored enzyme specialization from the preserved source cycle through resident domain calls and returned state. It verifies static relationships and compiler protections. CPU/GPU agreement, numerical accuracy, intervention sensitivity and performance belong to the separately retained execution evidence; they are not inferred from code inspection.

Reviewed implementation: [source_enzyme.py](../../local_lab/source_enzyme.py), [base cycle](../../local_lab/source_cycle.py), [resident compiler](../../local_lab/source_resident_v2.py), and [result reader](../../local_lab/source_enzyme_results.py). The controlling source is [kernel.py](../../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py), with its original catalogue/cycle declarations. The [base source audit](../source_cycle_2026-09-24/SOURCE_FIDELITY_AUDIT.md) retains the original source-page mapping. Application semantics are declared in the [enzyme binding](../../docs/RESIDENT_ENZYME_BINDING.md), [domain grounding](../../docs/ENZYME_POOL_DOMAIN_GROUNDING.md), and [resident v2 ABI](../../docs/RESIDENT_V2_ABI.md).

## Exact reviewed files

| File | SHA-256 |
|---|---|
| `local_lab/source_enzyme.py` | `2875592287d4905881422da819e55068cab9b4b2b20e985a1b673168a6419911` |
| `local_lab/source_cycle.py` | `b8bb4255b19e0e53d664449addc984b6c0c44ed795a3f78bfa8190d848ab9f51` |
| `local_lab/source_resident_v2.py` | `311206687ae0c1b9b1a76dfdaec295761836a2f6e1c4f0afac4994de1c6070d7` |
| `local_lab/source_enzyme_results.py` | `423e42e7f7d8af1f1bb68670526c49b6f6c1496129996b0b83941048afe4c3e5` |
| `source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py` | `df363ea81a756d5f1adc26ccabf0e4a5c5e5eeca28c2aa144c09c6d6562b86d4` |

Line references below apply to these revisions. The generated application manifest additionally identifies its input document, complete bank, protected law hashes, base generator and enzyme generator. Changed inputs/totals define a separately identified numerical task.

## The original eight stages remain executable

`source_enzyme.py:286–295` obtains the original authored cycle from `base.build_definition`. `extend_action`, lines 247–283, preserves the entire original action-tape prefix and verifies equality after accounting for the wider initial state read. The extra domain calls execute within `surface_return`, after the original provisional state writes and before transaction commit. The base wavefront initialization and configured Y-up count remain source inputs. Mutation expressions are deliberately extended with domain feedback; the claim of unchanged prefix concerns the action tape, not unchanged controller semantics.

| Source stage | Original source | Retained base numerical relationship |
|---|---|---|
| `operator_mutation` | `kernel.py:82–96` | `source_cycle.py:374–397,415–418`: all targets read the old record/state image; current mutator and pinion produce new definitions/anchors; rebinding precedes action. Previous returned chart and wave feed the Klein update. |
| `log_polar` | `kernel.py:98–99` | Base lines 190–198,420: actual scaled log-radius and atan2 encoding of both complex channels, with current resident field context and guarded numerical domains. |
| `split_and_hinge` | `kernel.py:101–104` | Base lines 199–209,422–427: jitter-dependent split, actual split-phase parity with neck, then the current double-Hadamard family. |
| `selected_operator` | `kernel.py:106–119` | Base lines 210–216,429–432: exact source-index routing, current K/jitter routing context, and dynamic current placement/field/body calls. Unsupported roles or missing identities fail without modulo aliasing. |
| `rk4_four_slots` | `kernel.py:121–127` | Base lines 217–232,434–442: dependent slope inputs, explicit interval/jitter, configured fourth-slot Y-up applications, and four-slope combination. |
| `geometry_divergence` | `kernel.py:129–136` | Base lines 233–277,444–448: six working-wave/current-K primitive values; encoded-angle history/jitter/interval; geometric growth; contraction and blend. |
| `rgba_crystal` | `kernel.py:138–149` | Base lines 278–298,450–454: both complex streams, all B-history values and all RK slots, actual T transformation and its guarded inverse. |
| `surface_return` | `kernel.py:151–155` | Base lines 299–317,456–470: current pinion and return consume K, complex channels, B, inverse matrix, neck, parity and interval. Domain calls then consume these returned values before the same transaction commits. |

The original source supplies relationships rather than these unique numerical equations. The typed wave/history projections, RK derivative law, finite families, numerical couplings and enzyme optimization policy are authored choices. The original source's abstract LUT context is bound to actual current resident records and situated fields; it is not an all-record numerical reduction on every call.

## Two different geometric meanings

The existing Math_blend field slot remains the intrinsic Klein carrier disk. `Plan.situated` in the base compiler, lines 356–372, evaluates current placement and carrier field. Concentrations are never identified with Klein chart coordinates.

The added domain role uses four-species order `(E,S,ES,P)`. `source_enzyme.py:92–113` declares the conservation plane

```text
q(c,p) = (E_total-c, S_total-c-p, c, p)
y = (sqrt(5/2)*c, (c+2*p)/sqrt(2)).
```

In real arithmetic this transform preserves equal-weight four-concentration Euclidean distance within the plane. The domain is the transformed trapezoid `0<=c<=E_total`, `p>=0`, `c+p<=S_total`, under the explicitly supported pool ratio `0<E_total<S_total`. One common concentration scale applies to every species and both totals; independent enzyme/substrate rescaling would change the metric.

Lines 140–159 evaluate all four closed edge segments and select the first minimum on exact ties, returning signed intrinsic distance and its nearest boundary point. This is a true distance formula within the declared conservation plane. It is not a signed distance to a four-dimensional solid. The full correction distance reported for raw observations is unsigned. Actual execution uses rounded FP32 constants and arithmetic, so small conservation/nonnegativity residuals require explicit reporting.

## Added typed resident roles

`source_enzyme.py:115–195` installs these methods on the existing Math_blend body family:

| Role | Executed meaning |
|---|---|
| 100 | Fast or cautious proposal. Current returned wave, all four B values, all inverse entries, interval and current carrier field determine a bounded step toward the observation's plane target. |
| 101 | Protected intrinsic domain SDF and nearest-boundary witness. Carrier distance does not change this scientific law. |
| 102 | Protected projection/evaluation. An interior trial remains unchanged; an exterior trial uses the domain boundary witness. Full four-species discrepancy is evaluated. |
| 103 | Protected acceptance. A cancellation-resistant intrinsic quadratic change decides improvement; an ordinary rejection retains the incumbent and continues the cycle. |
| 104 | Protected decoding, full objective and convex-gap estimate for the accepted state. |

These are expression-bank programs executed through current typed resident record calls, not a host correction pass. `protect_laws`, lines 198–210, requires every reachable family with the blend interface to retain identical role0 and role101–104 function handles. Only proposal role100 may vary between the declared strategies. Matching signatures alone would not protect conservation semantics; this extra identity check does. Totals, metric constants, bank functions and role maps are immutable during execution.

The carrier field is evaluated when the domain methods are dispatched, but protected pure-law roles do not consume it as a numerical modifier. Carrier/placement effects enter proposal generation. This separation prevents a moved operator from changing the conservation law it is meant to obey.

## Resident feedback and transaction timing

`extend_mutation`, lines 213–244, adds prior trial distance, prior improvement and prior acceptance to the old mutator's typed inputs. These values select the next blend proposal family. The original mutator-to-successor change remains present. All targets still read the common old snapshot, so newly changed controller definitions do not retroactively govern earlier targets in the same pass.

For the mutation record only, the authored control update also receives

```text
0.02*sin(prior_trial_sdf)
+ 0.01*sin(prior_improvement)
+ 0.01*(2*prior_accepted-1).
```

That creates an inspected path from chemical results to later old-mutator hinge selection through `mutator_control` in `source_cycle.py:158–173`. Each added increment is bounded; accumulated controller state is not thereby bounded, and no stability claim follows. A threshold-based later selector need not change its choice for every control perturbation.

The application calls and writes are at `source_enzyme.py:261–273`. Observations and incumbent coordinates survive in registers44–49. Scratch registers0–28 are reused only after the original 44 provisional state writes. The added state reaches the same checkpoint and next old-image read. Native epoch rollback includes the original core and added domain state together. A declined optimization proposal is successful execution, whereas a VM arithmetic/domain failure rolls back and freezes that instance under the resident contract.

The host initializes a declared feasible corner independent of the observation; it does not solve the observation before dispatch. `source_enzyme_results.py:31–110` reads returned species and diagnostics without repairing them. It separately reports conservation, nonnegativity, correction distance and FP32 gap estimate. Epoch-zero gap/acceptance placeholders are not reported as evaluated convergence diagnostics. The nearest boundary witness is used internally; a separate durable boundary-edge label and boundary-witness export are not currently provided.

## Numerical and evidentiary limits

Acceptance uses `DeltaJ=2*(old_y-y_target) dot delta+||delta||^2`, lines 168–179. This avoids subtracting two large costs sharing the same off-plane error. The full objective remains diagnostic. FP32 rounding can still produce a plateau near a solution; neither a finite run nor a small computed gap proves exact nearest projection. The gap is explicitly an estimate, not an interval-certified bound. Accuracy must be checked against an independent original-input oracle and the stated metric/tolerances.

Use the campaign [report](REPORT.md), [baseline summary](baseline_summary.json), [intervention summary](interventions_summary.json), and [initial independent accuracy audit](initial_full_cycle_accuracy_audit.json) for actual recorded outcomes and their artifact hashes. The chemical-control ablation has finite-horizon cases where controller words change while wave/domain outputs remain unchanged. Those null output results must remain visible: a stored control change alone does not establish activated wave feedback.

The separate [long-feedback audit](long_feedback_audit.json), inspected after the static review, records actual delayed activation. The tested chemical-control ablations through 128 epochs showed no core-wave difference. At 2,048 epochs the baseline and feedback-ablation runs each matched their respective CPU/GPU checkpoints exactly; comparison between the two runs changed core-wave values in 45 of 129 instances (180 words), with 1,485 changed core-state words and 141 changed domain-diagnostic words. Accepted concentrations remained identical. This establishes conditional, delayed chemical-feedback influence on the later core for those recorded cases, not a uniform per-epoch response or a different repaired solution after the accepted state had settled.

This is a finite, authored resident consistency-reconciliation application. It does not establish reaction kinetics, equilibrium, kinetic reachability, assay validity, biological benefit, universal computation or new physics. The selected source route adapters remain bounded to the six supported geometric records; history is a finite projection; BC5 texture encoding and a Bayer texture layout remain outside the completed core claim. The circulation uses the declared fixed Klein metric and does not establish general smooth metric/tangent covariance. It also does not establish that this recurrence is necessary or faster than a conventional projection method: the domain has a finite closed-form geometric construction, and performance comparisons require equivalent tasks.

Within those boundaries, inspection found the domain computations resident, the core-to-proposal and task-to-mutator connections explicit, and protected scientific roles invariant across supported strategy changes. Their runtime effect and numerical quality remain separately measurable claims.
