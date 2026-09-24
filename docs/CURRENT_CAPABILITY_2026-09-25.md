# Current capability and source fidelity — 25 September 2026

## Superseding update: resident SDF construction is now measured

**Dawnwood now has a working, bounded program-construction layer inside its numerical source architecture.** The resident runtime creates new SDF expression nodes and child references, evaluates the resulting region, compares it with the incumbent, and retains the accepted executable program as part of the returned state. Its first measured application constructs resource-admissibility regions. This supersedes the earlier assessment below wherever that assessment says resident construction is still unimplemented or unmeasured.

This is stronger than changing a scalar or selecting an existing M0/M1 function. Starting from one box, the GPU constructs `separated_union(box0, box1)` and then `separated_union(separated_union(box0, box1), box2)`. Those new expression edges were not populated in the initial program. The fixed resident interpreter subsequently uses the constructed code and constants to calculate distances and admission decisions. The mathematical guarantee is an exact Euclidean SDF for the permitted, strictly separated boxes in real arithmetic; FP32 execution has separately measured error. The [domain definition](DEVELOPMENT_RESOURCE_DOMAIN.md) and [admission bounds](DEVELOPMENT_ADMISSION_BOUNDS.md) specify the units, metric and protected quota.

### What the new measurements establish

The [resident construction campaign](../output/source_development_2026-09-25/resident_construction/REPORT.json) runs 129 instances. Every instance progresses from one active AST node and coverage 3/9 at epoch 1, to three nodes and coverage 6/9 at epoch 2, to five nodes and coverage 9/9 at epoch 3. The accepted programs remain unchanged through epoch 64. They share a three-leaf topology but have 129 distinct packed semantic regions.

Disabling construction retains the initial program and its task behavior. A checkpoint resumed for 3+5 epochs equals a continuous eight-epoch run; reversing record-mutation traversal also gives the identical checkpoint. Malformed live code and a deliberately introduced late failure preserve all preceding state and record words on rollback. The campaign records nine CPU/Vulkan pairs, 12 exact full-checkpoint comparisons and **1,867,187 compared words with zero differences**, with Vulkan validation reporting zero errors and warnings. The late-failure experiment is an explicit modified-configuration intervention, not ordinary same-configuration continuation.

The later [source integration audit](../output/source_development_2026-09-25/source_audit/REPORT.json) supplements that campaign's originally pending source-audit entry. It accepts the actual graph and a version with every node ID renamed, rejects 15 broken graph relationships and three protected-binding changes, and retains the audited initial-program hash. Its positive program matches the preliminary three-lane CPU/GPU execution. This is evidence for the declared structural obligations; arithmetic validity, numerical sensitivity and runtime behavior are checked separately.

The [frozen holdout assessment](../output/source_development_2026-09-25/heldout_assessment/REPORT.md) evaluates three actual retained programs on 900 points generated after freezing their checkpoint and hashes. Each covers **900/900**, versus **300/900** for the initial one-box program. All exact packed-geometry certificates pass, with zero admissions on 736 outside-quota probes per program. An independently hand-defined three-box reference also covers 900/900 and has a smaller area penalty. Therefore the demonstrated benefit is over the one-box baseline in this authored structural benchmark. It is not an advantage over that fixed three-box solution, a measured allocator benefit, or a learned policy from real workload traces. **These holdout evaluations are currently host-oracle measurements; native execution of the 900 queries is pending.**

### How this corresponds to the original architecture

[Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf), physical p9 equations 21–25, joins body, field and anchor and requires the preceding operator field to govern record changes. Its p13 equation 36 describes returned state becoming the changed operator field that acts next. Its p16 explicitly leaves numerical meanings to be supplied. The implementation realizes a finite numerical edition of these relationships; the specific resource domain, box grammar, objective and construction law are authored specializations, not equations uniquely dictated by the PDF.

In [source_development.py](../local_lab/source_development.py:248), the **old resident mutator** receives the preceding uncovered witness, program count, returned wave, its own situated field and the target field. It writes a construction descriptor into the resource record during common-old mutation. Current situated resource-record methods then construct and check code/box words, evaluate incumbent and candidate programs, and select all 40 retained program words with the same acceptance bit. The selected program's distance, score and witness return with it. The witness can drive a subsequent resident proposal. No host chooses a winning program each epoch.

The existing source graph still contains all eight source phases, current-record dispatch, old-mutator/old-pinion mutation, PHI, the declared double-Hadamard binding, implicit routing, dependent RK slots and Y-up events, geometry/coupling, R/G/history/inverse, pinion and whole return. [source_development_fidelity.py](../local_lab/source_development_fidelity.py:249) checks those core obligations plus the construction/validation/retention paths. Some protected resource-law calls execute after the same record's placement and field evaluation without arithmetically using that carrier-distance value; the audit records this distinction. The biochemical/resource coordinate metric is not silently identified with the Klein carrier metric.

### Which meta-levels exist

These are explanatory distinctions, not an official capability scale from the source.

| Layer | What is present | What remains fixed or unproved |
|---|---|---|
| Acting computation | Current situated operators execute numerical definitions and return state. | Chosen finite numerical bindings and FP32 limits. |
| Definition change | Resident rules change executable records; the mutator's own successor can change later behavior. | The default M0→M1 transition is predetermined, as described in the historical assessment. |
| Program construction | Resident methods now add new SDF AST operations and references, evaluate their effect, retain accepted programs and resume them. | At most four boxes/seven nodes, with the current constructor appending a box and union. It does not synthesize arbitrary new opcodes. |
| Policy assessment | Incumbent/candidate comparison, rejection, retained score and uncovered-witness feedback run inside the application. | Quota, exactness gates, training requests, objective, interpreter and constructor arithmetic are fixed during a run. They are not newly reasoned-out laws. |
| AI-guided reflection | The assisting AI supplies domain knowledge, selects a representation and records decisions from observed evidence. | A second measured AI-guidance comparison is pending here. General semantic explanation, objective invention and scientific reasoning have not been established as kernel-internal abilities. |

A fixed interpreter does not cancel self-reference: changing the interpreted program changes the computation that interpreter executes, and that changed program is carried in the circulating state. Conversely, this does not mean every implementation layer recursively rewrites itself. The current constructor method itself is not being synthesized by the constructed box AST. The [early Formalization](../Dawnwood_Interactive_Formalization.pdf), physical p9 §7.3, p11 §10.3 and p15 §14.2, already distinguishes finite self-reference, self-optimization and a separately required universality construction.

For the user's question about “full meta reasoning”: **there is now actual source-connected self-modification plus bounded SDF program construction and internal task evaluation. General meta-reasoning is a broader, unmeasured claim.** “F8” is not a defined numerical reasoning or fidelity score in the reviewed source documents. Eight executed source stages are not eight demonstrated levels of reasoning, and assigning a fidelity percentage would obscure the concrete implementation boundaries.

Remaining source/device differences include unrestricted symbolic-language execution, runtime catalogue allocation beyond fixed capacity, shared population-wide operator-field semantics, BC5/device texture compression and the proposed on-chip/cache organization. The numerical two-Hadamard law, record packing and transaction buffering are distinct claims; they do not jointly prove every proposed meaning of “double packing.” These boundaries preserve the source's broader proposal while identifying what this edition actually delivers.

The immediate unfinished evidence is the native holdout-query run and a measured second AI-guided construction decision. The active development goal is not marked complete by this assessment. Continue from the [decision ledger](../output/source_development_2026-09-25/decision_ledger.jsonl) and the retained checkpoint rather than treating the historical text below as current status.

## Historical assessment: before the resident-construction campaign

**The remainder is preserved from the earlier assessment on this same local date. Its statements about construction being unimplemented were accurate before the campaign above and are now superseded. Earlier source-cycle and hardware results retain their own scope; they are not retrospectively measurements of the new construction layer.**

Dawnwood currently provides an executable, source-connected, self-referential numerical substrate on the laptop GPU. Current records determine actions, changed records determine later actions, and complete state and records survive checkpoint continuation. It has measured metaprogram effects and bounded scientific/computational applications. General meta-reasoning and resident invention of new useful SDF programs have not yet been demonstrated.

This is a dated assessment, not a completion claim for the active definition-development objective. “F8” is not a defined reasoning scale in the reviewed source documents. Architectural fidelity and reasoning capability require separate evidence; neither has a defensible percentage score here.

## What runs now

The [source graph interface](SOURCE_GRAPH_PROGRAM.md) lets an author supply the complete named mutation/action graph and numerical definitions. The compiler produces resident CPU/Vulkan programs. The current graph determines old-snapshot mutation, current body/field/placement calls, routing, all eight source stages and all returned values. A headless application can continue from the resulting checkpoint.

| Source relationship | Present implementation and evidence | Boundary |
|---|---|---|
| An operator joins body, field and placement. Unified v0.2 physical p9, equations 21–22. | Actual record handles resolve placement, nearest-lift field evaluation and body action. Source-edit interventions change executed results. | A nominal distance type is not itself a mathematical proof that arbitrary edited arithmetic is an SDF. |
| The preceding operator field changes the next field; its mutator is resident too. Unified p9, equations 23–25; p13, equation 36. | Common-old mutation includes the mutator's own record. A changed successor acts on the next epoch; traversal-order and continuation checks preserve this boundary. | The shipped default mutator makes a predetermined M0→M1 transition, then retains M1. Feedback continues to affect finite controls and authored program selection. |
| Paired Hadamard/pinion, Klein return, PHI, routing and the connected recurrence. Unified pp5–12. | The graph executes the two-Hadamard numerical binding, source-index routing, dependent RK slots and declared Y-up events, geometry/coupling, R/G, four-component history, matrix inverse, pinion and return. | Numerical laws fill explicitly open source bindings. Mandatory graph ancestry establishes dependency structure, not sensitivity to every argument. |
| Returned state includes the definitions that act next. Unified pp12–13. | CPU/GPU checkpoints retain current records, state, plans and bank. Resume and whole-epoch rollback are measured. | Function banks and graph plans remain immutable during the existing run; mutable handles choose among their declared meanings. |
| Applications use the operator field computationally. Unified p13. | Resident enzyme-pool consistency, amplitude projection and typed matrix composition produce independently checked numerical outputs. | These do not establish general inference, biochemical dynamics, autonomous scientific discovery or better performance than a matched conventional solver. |

The source is [Unified v0.2](../Dawnwood_Interactive_Unified_v0.2.pdf), with the [original discussion](../double-slit-theory.pdf), [early Formalization](../Dawnwood_Interactive_Formalization.pdf) and preserved [symbolic application](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py) distinguished in the [literal application contract](LITERAL_APPLICATION_CONTRACT.md). Physical PDF pages include the cover.

## What “meta” has actually been measured

The source makes acting definitions part of the returned state. This creates a concrete level of computation about computation: an operator changes which operator will act. The [delayed-successor intervention](../output/source_graph_2026-09-24/self_change.json) freezes the default mutator's successor. At epoch 1 the state is unchanged; at epoch 2 the intervention changes waves in 129/129 instances and decoded chemical compositions in 80/129. An identity control remains exact. This supports a causal claim about self-changing execution.

The exact limitation is visible in [source_cycle.py](../local_lab/source_cycle.py): both `mutation` and `mutation_successor` return the `mutation_successor` family for source index 30. The default thus performs one predetermined family transition. Continuing record/control evolution and feedback-dependent choices are real, but no sequence of newly invented mutation programs follows from this rule.

Reasoning about whether a computational rule explains evidence, choosing a better representation and grounding a new domain law is currently performed by the assisting AI and recorded authoring process. It is not established as an internal ability of the kernel. The kernel's evolution is not evidence that the assisting model's weights were trained.

The early Formalization physical p9 section 7.3 distinguishes self-reference from self-optimization; physical p11 section 10.3 and p15 section 14.2 separate its finite profile from unrestricted self-modification and universality. Unified p16 leaves numerous numerical bindings open. Those source boundaries are part of faithful interpretation.

## Useful results and hardware evidence

- **Enzyme-pool consistency:** candidate concentrations are reconciled against two conserved pools in a declared closed model. The [actual command-line readout](../output/source_graph_2026-09-24/cli/enzyme/results.json) contains concentrations, conservation residuals and gap estimates. Some gap estimates remain above the requested threshold; feasibility is not proof of convergence or a kinetic prediction.
- **Amplitude constraint:** the authored amplitude-budget operator evaluates a Euclidean constraint and projects an immediate complex-pair output. Later transformations can change that output again.
- **Matrix composition:** current routed T and inverse-T procedures compose numerically inside the recurrence, with independent inverse/application checks.
- **GPU execution:** the [completed graph campaign](../output/source_graph_2026-09-24/REPORT.md) reports 51 paired workloads and 5,902,446 compared mutable words. Its additional saturation run executes 33,024 instances for 2,048 epochs, reaches 100% GPU utilization and 71°C, and compares 26,881,536 mutable words without differences. These are implementation/load results, not a reasoning or task-speedup benchmark.

## What is being built next

The active goal goes beyond selecting pre-authored alternatives: circulating evidence and resident metarules must construct new executable SDF structures, evaluate their useful effects, retain accepted definitions, and continue from them while AI guidance responds to evidence.

Completed foundations in the current working milestone:

1. [DAWNWOOD_AGENT.md](../DAWNWOOD_AGENT.md) defines source obligations, knowledge provenance, protected laws, structural novelty, evidence and continuation requirements for the guiding agent.
2. The isolated [resident-v3 runtime](RESIDENT_V3_ABI.md) supports 128 state words while retaining the existing expression limits and transaction semantics. Its [runtime report](../output/source_development_2026-09-25/runtime_v3/REPORT.json) records 64 passing checks and 16 passing rejection cases, including paired CPU/GPU execution, rollback and continuation. Capacity alone does not construct a program.
3. A [resource-distance language](DEVELOPMENT_RESOURCE_DOMAIN.md) represents exact-distance regions composed of strictly separated boxes. It declares normalized persistent/scratch memory coordinates, a protected quota and a mutable preference region. Its [source-library report](../output/source_development_2026-09-25/domain_definition/summary.json) records 3,608 independent boundary-oracle comparisons and explicit malformed/geometric rejections. These are source-library checks, not a resident synthesis result.

The constructor binding and graph integration are in progress. The evidence at this assessment does **not** yet contain a complete resident propose→construct→evaluate→accept→checkpoint→resume run for newly composed SDF programs. The proposed first grammar is bounded to four box leaves and seven nodes. Demonstrating it would establish bounded program construction; it would still not establish unrestricted invention or general intelligence.

The initial resource requests are authored structural examples, not measured laptop workload traces. They can check that constructing multiple separated regions is useful for the declared example objective; they do not yet demonstrate real allocation savings or an automatically learned laptop policy.

Remaining source/device differences include general symbolic-language execution, runtime record allocation, the proposed shared operator-field/neighborhood organization, BC5 compressed texture layout and the proposed on-chip/cache organization. Existing FP32 record/checkpoint packing, independent GPU instances and double buffering do not demonstrate those additional features or a second compression factor. Optional graphics is outside the requested computational core and is not a prerequisite for this work.

Follow [the decision ledger](../output/source_development_2026-09-25/decision_ledger.jsonl) and current execution receipts when continuing. Later evidence should supersede this dated assessment explicitly rather than silently broadening earlier claims.
