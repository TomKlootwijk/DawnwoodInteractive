# Frozen-program holdout assessment

The three resident-constructed programs each cover **900/900** unseen benchmark points, compared with **300/900** for the actual initial one-box program. The independently hand-defined three-box reference also covers **900/900** and uses less area. This establishes improved coverage over the single-box baseline in this authored structural task; it does not establish superiority over the fixed three-box reference or performance on real allocation traces.

The assessed programs were read from the actual eight-epoch checkpoint, whose bytes match the supplied CPU checkpoint. This assessment evaluates those retained packed programs on the host. **It does not execute the heldout queries in the native CPU/GPU runtime.** The query file is retained for that separate campaign.

## Freeze and provenance

The [freeze receipt](freeze_receipt.json) was written at `2026-09-24T23:41:24.705904+00:00`, before creating the seeded random generator or any holdout points. It includes the checkpoint, manifest, source, initial-checkpoint, library and program hashes. The actual checkpoint and initial image are retained locally. No constructor, candidate or parameter changed after the freeze; the checkpoint and all five comparison-program hashes were checked again at completion.

- Checkpoint: `fff1ca1ed34c57fa9c6a967b211330b42c13fc5c37074039f8e41a8aba7a1639`.
- [Queries](queries.json), 900 raw `[x,y]` points: `bc770ef0451a843665789b4a1bae623490d33dd79a320bde969c8d93c349e61e`.
- [Frozen programs](frozen_programs.json) contain all code triples, operands and revisions; separate structural and semantic hashes appear in the freeze receipt.
- [Experiment source](experiment.txt), [dataset receipt](dataset_receipt.json), [exact certificates](exact_packed_certificates.json), [per-query values](oracle_values.json), [metrics](metrics.json), and [summary](summary.json) retain the direct computation.

The incoming campaign ledger snapshot is included. Its last entry precedes full resident execution; the present assessment records its own subsequent observation in [assessment_decision.json](assessment_decision.json), without rewriting earlier decisions.

## Fixed protocol and comparisons

The earlier [predeclared protocol](../admission_bounds/predeclared_protocol.json) specifies quota 1, nine training points and 300 holdouts around each center `(.72,.16)`, `(.16,.72)`, `(.42,.42)`. Holdouts use independent uniform x/y offsets in `[-.015,.015]`, Python `random.Random(202609252)`, in cluster-major order. The nine training points lie on cluster diagonals; the holdouts exercise both coordinates independently. Query coordinates are packed to FP32 before evaluation, and their packed values are retained separately.

The initial baseline is extracted from the actual initial image and checked against the declared box `(.72,.16,.03,.03)`. The reference, declared before generating queries, consists of three boxes at the cluster centers, each with half-extents `(.03,.03)`. It is a hand-authored benchmark reference, not a measured true operating region or a resident-generated result.

Every safe one-box program covers at most three of the nine training points: a rectangle containing points from two different clusters needs upper-x plus upper-y at least 1.12 or 1.42, exceeding quota 1. Therefore the one-box training comparison is not an arbitrarily weak choice of box parameters. The three-box reference demonstrates that a fixed larger representation can solve this designed task too.

Coverage requires signed distance `<= -FP32(1e-4)`. Values within `1e-5` of that threshold are marked ambiguous; there are **zero ambiguous holdout values** in all five programs. The mathematical oracle projects onto rectangle edges with exact rational arithmetic, determines inside/outside by exact interval membership, and takes a final binary64 square root. A separate binary64 postorder box-SDF/min calculation agrees to a maximum absolute error of `2.220446049250313e-16` across all 8,225 comparisons. This is a host arithmetic observation; the predeclared **native FP32** absolute error limit remains `1e-5` for the later query batch.

## Results

All constructed lanes have three leaves, five active AST nodes and revision 2. The initial program has one leaf, one active node and revision 0. The reference and constructed programs share the three-leaf topology but have distinct semantic regions and program hashes.

| Program | Training coverage | Holdout coverage | Union area | Training count score |
|---|---:|---:|---:|---:|
| Initial one box | 3/9 | 300/900 | 0.00360000 | 2.97998200 |
| Hand-defined three boxes | 9/9 | 900/900 | 0.01080000 | 8.93994600 |
| Constructed lane 0 | 9/9 | 900/900 | 0.01631998 | 8.93991840 |
| Constructed lane 1 | 9/9 | 900/900 | 0.01644730 | 8.93991776 |
| Constructed lane 2 | 9/9 | 900/900 | 0.01632097 | 8.93991840 |

The unchanged count score is `coverage - .02*leaf_count - .005*union_area`; training and holdout counts are scored separately and are not directly comparable to each other. At equal coverage and leaf count, the smaller reference has a slightly higher score. Constructed/reference intersection-over-union is approximately 0.657–0.659. This is a geometric comparison with the authored reference, not an accuracy estimate against observed resource behavior.

Constructed holdout distance ranges are approximately `[-.03996,-.01485]`; all points remain well inside their admitted regions. The initial baseline has a maximum holdout distance of approximately `.76932`, corresponding to uncovered clusters.

All five programs pass the exact packed-constant quota-containment and strict-separation certificates with no numerical tolerance on their proof inequalities. Each was also evaluated on **736 outside-quota probes**: all outside points on a 31×31 grid over `[-.25,1.25]^2`, plus six near-boundary probes. There are **zero outside-quota admissions**. These samples illustrate the behavior; the containment certificate supplies the general mathematical guarantee for each retained region.

The retained decision is to keep these programs unchanged for native holdout evaluation. This result supports a bounded, resident-constructed admissibility representation on an authored benchmark. It establishes neither an allocator, real memory-budget safety under changing system conditions, an advantage over an independently specified three-box solution, nor general learning from allocation traces.
