# Resident construction of computational SDF definitions

`DWI-SDF-DEVELOPMENT-0.1` makes a bounded SDF expression part of the state returned by the source cycle. An old situated mutator proposes an edit from preceding domain evidence. The current resource operator constructs candidate instruction and child-reference words, evaluates the candidate, and retains a complete program only when the declared objective improves. A fixed interpreter executes the changing program data.

This is a new numerical application binding of the original body/field/position and whole-return architecture. The grammar, scientific/model constraints, objective and constructor policies are authored by the guiding AI. This edition constructs combinations of declared primitives; it does not invent arbitrary primitives or establish general meta-reasoning.

## What is defined

The coordinates are persistent and scratch memory demand divided by the same positive reference byte count. The protected model is `x>=0`, `y>=0`, `x+y<=quota`. The developing SDF defines a preferred request region inside that quota. It is not the signed distance to the entire quota triangle and does not guarantee a hardware allocation succeeds.

The [domain derivation](DEVELOPMENT_RESOURCE_DOMAIN.md) establishes exact signed distance in real arithmetic for the strictly separated box-union language. The native [admission bounds](DEVELOPMENT_ADMISSION_BOUNDS.md) explain why two-margin box guards imply the exact packed-coordinate certificate despite FP32 rounding. Protected geometry and scoring margins are distinct.

Forty state words carry three header values, seven possible opcode/child triples and four possible box definitions. `BOX` evaluates a leaf; `SEPARATED_UNION` evaluates the minimum of its two earlier children. Inactive slots are zero. The resident constructor can append one leaf and one union node, creating new operations and references where no active instruction existed. At most four leaves and seven nodes fit this edition. The initial example has one box.

The complete instance has 100 state words and 32 situated records. The source core's eight phases remain connected. The additional resource record is source index 31, with explicitly declared body, carrier field and placement. The old mutator's additional role and the resource record's development roles come from the supplied development source document. The original selected-wave interface is retained; it is not silently relabeled as a resource-distance function.

## The resident feedback loop

1. Every mutation target uses the same preceding state and operator bank. The old mutator's proposal reads the previous uncovered request, its distance, program size, quota, wave, control and old situated fields.
2. Only the resource record receives the proposed center, extent and eligibility in its reserved descriptor words. Other records retain their corresponding reserved words. This mutation completes before action publication.
3. The current resource record executes its placement and carrier-field chain. Its protected mathematical roles share that execution context; their resource metric is not changed by the carrier distance. Carrier fields influence construction through the old mutator proposal.
4. Live program structure and geometry must pass protected guards before interpretation. Candidate instructions and leaf constants are then constructed from old program words and the published descriptor.
5. Candidate structure and both geometry gates determine eligibility. Invalid candidate data is replaced with safe incumbent data before eager interpretation. A corrupt live definition fails the epoch instead of being treated as an ordinary unsuccessful proposal.
6. The same training requests and objective evaluate incumbent and candidate. Strict improvement selects the entire corresponding program. The score, coverage and next witness are selected from the matching evaluations under that same acceptance bit. The returned query distance is freshly interpreted from the retained program.
7. Program words, diagnostics, records and the entire source state commit as one transaction. Subsequent mutation consumes the retained witness. The checkpoint contains the acting program and all required state; normal continuation uses that checkpoint directly.

The [construction components](DEVELOPMENT_BINDINGS.md) specify the arithmetic. The [structural audit](../local_lab/source_development_fidelity.py) follows all forty corresponding words, both training-request interpreter sets, the final retained-program query, descriptor publication and source dependencies. Its small selector/guard definitions are checked as well. Structural checks complement numerical evidence; they do not replace the distance proof or independent output verification. The retained [source audit](../output/source_development_2026-09-25/source_audit/REPORT.json) passes the baseline and a complete node-renaming control, rejects fifteen broken dependency/guard graphs, and rejects three modified protected source bindings.

## Run and inspect locally

Use a fresh output directory for compilation:

```powershell
.\Dawnwood-Develop.cmd compile --instances 129 --output output/my_development
.\Dawnwood-Develop.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 8 --input output/my_development/program.bin --output output/my_development/gpu8.bin
.\Dawnwood-Develop.cmd results output/my_development/gpu8.bin --manifest output/my_development/manifest.json --output output/my_development/results8.json
```

To continue the same instance population, pass `gpu8.bin` as the next `run --input`. `--epochs` is the number of additional epochs. Use `--backend cpu` for the paired scalar implementation. `inspect` shows the raw named state and record image. The results reader returns the actual generated expression, hashes, query decision, independently checked geometry, witness and numerical diagnostics. It never repairs the checkpoint.

To apply one retained definition to new requests, write a JSON array of normalized coordinate pairs, such as `[[0.16,0.72],[0.50,0.50]]`, and prepare a query population:

```powershell
.\Dawnwood-Develop.cmd prepare --input output/my_development/gpu8.bin --manifest output/my_development/manifest.json --queries requests.json --lane 0 --output output/my_requests
.\Dawnwood-Develop.cmd run --backend vulkan --device "RTX 5070 Ti" --epochs 1 --input output/my_requests/program.bin --output output/my_requests/answers.bin
.\Dawnwood-Develop.cmd results output/my_requests/answers.bin --manifest output/my_requests/manifest.json --output output/my_requests/answers.json
```

Preparation clones the selected complete instance for each request and changes only the two query coordinates and the construction-enable bit. The constructed program stays fixed; each native instance executes the full source cycle to answer its query. This is an explicit fork into a query population, with parent checkpoint and program provenance. Prepared diagnostics remain marked pending until the native epoch executes. It does not allocate buffers or measure available memory: inputs, normalization and quota are supplied by the calling application.

Compilation retains `development_source.json`, `source_model.json`, `source_cycle.json`, `source_graph.json`, `definition.json`, compiler sources and a manifest. `--source`, `--model`, `--cycle` and `--graph` accept those explicit documents. This numerical edition fixes the protected definitions and grammar; changing their meaning requires a new declared and verified edition. Extra graph composition remains subject to complete source and development dependency checks.

For the default example, the AI supplies three request clusters and an initial box covering the first. A safe single axis-aligned box can cover at most one cluster; its best possible training coverage is 3/9. The declared objective rewards coverage and penalizes region area and leaf count. This authored structural benchmark demonstrates why creating additional regions can matter. It is not a measured laptop allocation trace, a learned general resource scheduler or a speedup claim.

The current campaign is recorded under [source_development_2026-09-25](../output/source_development_2026-09-25/). Consult its concrete run receipts for measured population, epochs, CPU/GPU agreement, continuation, intervention and query results. The [decision ledger](../output/source_development_2026-09-25/decision_ledger.jsonl) distinguishes AI guidance, resident construction and remaining work. The standing [agent guide](../DAWNWOOD_AGENT.md) keeps broader definition development active beyond this first grammar.

## Measured construction and limits

The [resident construction campaign](../output/source_development_2026-09-25/resident_construction/REPORT.json) passes 63 checks. Across 129 independent instances, the program grows from one to three to five active nodes, with training coverage increasing from three to six to nine requests. The generated program persists through epoch 64. Disabling construction retains the initial one-box program. CPU/Vulkan comparisons cover 1,867,187 words with zero differences; checkpoint continuation, reversed mutation-target order and complete epoch rollback also pass.

The first [held-out assessment](../output/source_development_2026-09-25/heldout_assessment/REPORT.md) freezes three generated programs before creating 900 unseen requests. Each covers all 900, compared with 300 for the initial box. A hand-defined three-box reference also covers all 900 and uses less region area. This demonstrates benefit over the seed and exposes a policy limitation; it does not establish superiority over an informed fixed definition. These are synthetic request distributions with explicit support, not measured allocation traces.

The native box-admission guard in this integration uses twice the proof margin. The earlier component campaign exercised its original default one-margin binding; that exact earlier module is preserved as [a source snapshot](../output/source_development_2026-09-25/binding_capacity/source_development_bindings.py.txt). The [admission investigation](../output/source_development_2026-09-25/admission_bounds/) derives and checks the revised bound, while the resident campaign exercises it on the device. Earlier receipts keep their original source hashes.

## Changing guidance while retaining a definition

The Python API in `local_lab.source_development_guidance` accepts the actual parent checkpoint and manifest plus a newly compiled program and its manifest:

```python
from local_lab.source_development_guidance import migrate_guidance

published_bytes, published_manifest = migrate_guidance(
    parent_checkpoint_bytes, parent_manifest,
    new_program_bytes, new_manifest,
    query=(0.20, 0.20),
)
```

This is an explicit publication of AI-authored guidance between runs. It copies the complete parent program, state, live records and epoch into the new immutable configuration. An optional query changes only its two declared state words. Function and family handles retain their declared identities; numerical function definitions can change within the checked source profile. The new compiled template's initial program and records are discarded. Native execution resumes from the returned published bytes.

Publication records both configurations, changed definitions, parent program identities and exact word preservation. Old application diagnostics remain marked pending until another native epoch evaluates the new guidance. This also applies when the request set shrinks: a retained coverage of nine is an old observation, not an invalid encoding merely because the new request set contains three items. Fresh results must obey the new request count.

The publisher validates the authored numerical edition, connects its declared bindings to actual native functions and record roles, audits the development graph, and reconstructs both execution plans to compare their exact native words. This closes a review-discovered gap where a substituted geometry gate could previously disagree with the stated protected law. The [publication revalidation](../output/source_development_2026-09-25/guidance_comparison/publication_revalidation.json) rejects ten malformed changes without modifying either input; both legitimate publications remain byte-identical after the correction. The [independent readout review](../output/source_development_2026-09-25/guidance_reader/REPORT.json) also checks the gate correction and stale coverage when the request set shrinks.

The guiding AI chooses the policy change and supplies the new source before publication. The resident then constructs, evaluates and accepts or declines subsequent SDF nodes. This mechanism does not claim the resident box program authored its own interpreter, objective or scientific laws. The [decision ledger](../output/source_development_2026-09-25/decision_ledger.jsonl) identifies the evidence behind a guidance change and the later execution that assesses it.

The first [measured guidance comparison](../output/source_development_2026-09-25/guidance_comparison/REPORT.json) preserves the three-leaf epoch-8 program and introduces a fourth request class. It compares proposal half-sizes `.045` and `.034` from the same complete checkpoint. At epoch 9 each policy refreshes the returned witness; at epoch 10 each resident instance appends the fourth leaf and its union, reaching seven nodes, revision three and coverage 12/12. All prior leaves and existing nodes are unchanged. The tighter policy reduces the newly added leaf's area by about 42.9%; this percentage concerns the fourth leaf, not total area or physical memory use. The 36-check campaign includes exact CPU/Vulkan comparisons and 1+1 versus 2-epoch continuation. Both final checkpoints were frozen before fresh holdout generation.

The [fresh holdout assessment](../output/source_development_2026-09-25/guided_holdouts/REPORT.md) and [native query application](../output/source_development_2026-09-25/guided_native_queries/REPORT.md) now verify that follow-up definition on unseen requests. The latter includes directly usable checkpoints and manifests for both policies. For hardware behavior, the separate [construction load continuation](../output/source_development_2026-09-25/construction_saturation/continued_1024/summary.json) reaches epoch 1,152 across 16,384 instances, compares every returned mutable word to CPU template references, and samples 100% GPU utilization with a 61°C observed peak. These workload-specific results do not establish maximum memory capacity or an application speedup.
