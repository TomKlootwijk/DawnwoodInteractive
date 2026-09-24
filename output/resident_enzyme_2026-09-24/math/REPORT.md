# Independent resident enzyme-domain numerical audit

The seven direct component workloads completed **3,486 cases and 37,776 committed instance-epochs per backend**. Every CPU checkpoint matched its Vulkan counterpart byte for byte. The actual GPU was **NVIDIA GeForce RTX 5070 Ti Laptop GPU**; Vulkan validation reported zero errors and warnings, and no lane failed.

The numerical implementation approximates the stated conservation-plane SDF and projection well in the sampled domain. It does **not** provide an exact-nearest, guaranteed-monotonic, or rigorously certified finite-precision optimizer. The hard boundary fixtures demonstrate why those qualifications matter.

## What was executed

The probe programs call the actual expression definitions from `tmp/enzyme_compile_smoke2/definition.json` through a resident typed body family: role 101 `enzyme_domain_sdf`, role 102 `enzyme_project_evaluate`, role 103 `enzyme_accept`, and role 104 `enzyme_witness_gap`. Recurrent probes additionally call the actual fast or cautious role 100 proposal. A single source `blend` record retains its original source-slot identities. A generation-only mutation plan isolates these numerical functions.

These component probes do not execute the original eight-stage source cycle, carrier placement/field, or evolving proposal strategy. The separate root campaign covers that integration. Here, direct call arguments deliberately make the mathematical cause of each result inspectable.

Scientific constants are `ET=1`, `ST=10` in normalized concentration units; the principal fixture uses a concentration scale of 10 μM. Both totals and all four observed species share that scale. All numerical references use the **packed FP32 inputs**. Input rounding is separately recorded per group in `independent_numeric_audit.json`.

The independent oracle enumerates zero-species active sets directly in four-species space. It solves the two equality constraints with rational arithmetic, keeps nonnegative candidates, minimizes squared distance, and checks projection optimality against all four feasible vertices. It does not evaluate the resident AST or reuse its edge-projection algorithm. Intrinsic input points are decoded using 80-digit decimal square roots before rational active-set analysis, independently of the expression bank's rounded coefficients.

## Measurements

| Workload | Cases | Main result |
|---|---:|---|
| Domain SDF, boundary witness, projection and gap |598|Maximum SDF absolute error1.446e-6; maximum projected-species error9.694e-7 normalized|
| Acceptance cancellation fixtures |1,024|147 accepted decreases had identical old/new full-objective FP32 words; no wrong exact-objective signs in this group|
| Fast proposal recurrence,128 epochs |135|Maximum species error3.588e-4 normalized against the exact nearest feasible species|
| Cautious proposal recurrence,128 epochs |135|Maximum species error1.443e-3 normalized against the exact nearest feasible species|
| Focused near-boundary next step |398|19 accepted tiny exact-objective increases;12 rejected exact decreases|
| Common concentration scaling by2^-10 |598|Zero normalized-output bit differences; zero physical-output differences after exact power-of-two rescaling|
| Common concentration scaling by2^10 |598|Same result|

The SDF fixtures cover corners, edges, interior, points just across boundaries, broad outside points, negative observations and observations outside the conservation plane. There were no SDF sign disagreements farther than 2e-6 from the exact boundary. The boundary-witness distance error was at most9.345e-7 normalized. The subgroup of 192 independently orthoprojecting arbitrary observations had its full four-species nearest-feasible comparison recorded separately.

Retained rounding residuals include negative returned species as low as−9.537e-7 normalized and pool residuals up to8.583e-7 normalized in the principal domain group. The reference did not clip them away. Distance and species errors multiply by the declared concentration scale to recover μM; objective differences multiply by its square.

Of the 1,024 direct acceptance fixtures, 156 deliberately use observation magnitudes outside the application frontend's normalized 10,000 limit. Those cases stress the finite arithmetic component and do not establish that the application CLI accepts such inputs. The remaining application-range and boundary cases remain separately identifiable in the retained inputs.

## Acceptance and boundary limitations

The revised acceptance law evaluates the intrinsic quadratic change rather than subtracting two large full objectives. This successfully resolves many cancellation cases. In real arithmetic the change equals the full four-species squared-error change; its finite-precision evaluation is approximate.

The 398 focused fixtures include all 270 final recurrent states and 128 near-face cases with outward gradients up to 4,000. They produced 19 accepted increases in the exact objective, the largest **1.4581e-8** normalized squared units. Twelve rejected proposals were exact decreases, with maximum missed decrease **3.4801e-12**. In 112 rejected cases, the ideal feasible projection would have improved the objective from an independently feasible old point. These counts include cases where a rounded old point or projected candidate lies slightly off the mathematical boundary.

Large gradients normal to a constraint amplify tiny off-face coordinate errors. The maximum candidate-species deviation from an ideal projection in these stress cases was 3.140e-5 normalized. A strict computed decrease can therefore reject useful tangential progress or accept a minute exact increase. Raw states, actual candidate changes, ideal-projection changes, and feasibility deviations are in `boundary_next_step/reference_comparisons.json`.

For an exact Euclidean projection and constant step α in(0,1), the fixed-context proposal obeys a contraction bound `(1−α)^n` on distance to the optimum. The measured FP32 recurrences plateau instead. Their constants were approximately 0.67725 and 0.22625; these are component settings, not universal rates for the evolving full source cycle.

## Gap estimate and metric coefficients

The exact rational gap inequality held on all 270 independently feasible reference copies of the recurrent results. Those reference copies exist only to satisfy the mathematical theorem's feasibility hypothesis; they are not substituted into any native checkpoint or application result. Their maximum feasibility correction was 5.574e-7 normalized.

The stored FP32 gap underestimated the exact feasible-reference objective excess in 110 cases, with maximum shortfall **8.6881e-7** normalized squared units. A rounded gap without a rounding allowance and a feasibility guarantee is consequently an **estimate**, not a rigorous certificate.

The coefficient audit retains the exact FP32 words for sqrt(5/2), sqrt(2), sqrt(2/5), and the vertex factor 1/sqrt(2). For the rounded nominal forward isometry, the largest entry of `TᵀT−[[3,1],[1,2]]` is 6.846e-8. For the actual target formula interpreted with real division by its rounded sqrt(2), it is 7.775e-8. The species decoder's largest coefficient-only metric defect `DᵀD−I` is **3.423e-8**. These are coefficient errors; the executed ordered FP32 operations contribute additional rounding. Independently packed vertices and edges also have their own rounding.

## Provenance and retained artifacts

The source definition SHA256 is `023187679965c7275c4339a68fcbc723eb800327a51e5ae213aca036dd31e021`. The generator remained unchanged throughout this component campaign at SHA256 `2875592287d4905881422da819e55068cab9b4b2b20e985a1b673168a6419911`.

The initial four diagnostic model copies were read using the Windows default text encoding, which altered non-ASCII title metadata. This did not change selected source slots or numerical bodies. Every one of the seven programs was independently recompiled using the original model with explicit UTF-8; **all resulting program bytes were identical** to their executed originals. This provenance discrepancy is recorded explicitly in `model_encoding_provenance`, and the original UTF-8 model is retained. The historical diagnostic copies were not silently replaced.

Each group retains `program.bin`, `cpu.bin`, `vulkan.bin`, its definition, model, manifest, both stdout/stderr pairs, and execution receipts with native/shader hashes. The top-level JSON audit contains precise maxima, function hashes, input-rounding disclosure and model-equivalence checks. Independent per-case references and script text snapshots support reproduction. `artifact_manifest.json` hashes the retained files.

The result concerns equal-weight consistency reconciliation under supplied closed enzyme and substrate pools. It does not infer reaction rates, kinetic trajectories, assay validity, disease effects, or biological benefit. The scientific derivation and primary sources are in `docs/ENZYME_POOL_DOMAIN_GROUNDING.md`.
