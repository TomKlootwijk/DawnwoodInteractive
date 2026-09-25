# Fresh holdouts after AI-guided construction

Both resident policies cover **1,200/1,200** fresh points in each independently selected lane **0, 64 and 128**. The guided `.034` policy reduces the newly added fourth box's area by approximately **42.914%**, and total region area by **10.975–10.977%**, without losing coverage in this sample. Each retained three-box parent covers **900/1,200**. The independently hand-defined four-box reference also covers **1,200/1,200**, with less total area than either constructed policy.

This assesses six sampled programs from two 129-lane populations, their three corresponding parents, and one fixed reference. **It is not a holdout result for every lane.** These measurements evaluate the actual retained packed programs with a host mathematical oracle. Native query execution is separate and is not claimed by this report. The task uses authored normalized resource-demand clusters; it is not an allocation trace, allocator, or measured hardware-performance result.

## Freeze and fresh data

[Decision 004](incoming_decision_ledger.jsonl) declared the new four-cluster comparison before these results. The incoming [checkpoint freeze](incoming_frozen_checkpoints.json) has SHA256 `4716f493515514e4b72db83ced8bfb6afbfa05a30200394965c70ad9f518feeb` and identifies the final CPU/Vulkan checkpoints. Their bytes match within each policy.

The local [freeze receipt](freeze_receipt.json) records lane selection, full checkpoint/source/manifest hashes, extracted program hashes and the comparison protocol at `2026-09-25T00:08:06.716414+00:00`, **before creating the random generator**. Full checkpoints, compressed manifests and all [frozen programs](frozen_programs.json) are retained. All existing parent leaf constants and first five AST nodes remain unchanged in the sampled descendants; the fourth leaf and its union are new. Hashes were checked again after assessment.

The fresh generator uses `random.Random(2026092502)`, with 300 points per center `(.72,.16)`, `(.16,.72)`, `(.42,.42)`, `(.20,.20)`. Each axis independently receives a uniform offset in `[-.015,.015]`, in cluster-major order. No holdout coordinates were supplied to the constructor or used to change a candidate or parameter.

[queries.json](queries.json) contains the 1,200 raw coordinate pairs for native evaluation; its SHA256 is `dd41d90ce4a792278c8d251222466f329b8fbbdf6302a7303a01b536e1857c33`. Packed FP32 queries and a [dataset receipt](dataset_receipt.json) are also retained. The reference is declared before generation as four boxes at the centers, all with half-extents `(.03,.03)`.

## Independent measurements

The oracle projects onto rectangle edges using exact rational arithmetic on packed FP32 constants and queries, determines sign by exact membership, and uses one final binary64 square root. It does not execute the constructor or use the box-SDF formula as its reference. Separate binary64 postorder SDF evaluation differs by at most `2.220446049250313e-16` over **19,480 comparisons**: 12,000 fresh holdout evaluations, 120 training evaluations and 7,360 reused outside-quota probes. Complete per-query results are [compressed](oracle_values.json.xz); [metrics.json](metrics.json) and [REPORT.json](REPORT.json) retain aggregates.

Coverage requires distance `<= -FP32(1e-4)`. There are **zero holdout values within the declared `1e-5` ambiguity band**. The least interior guided holdout distance is approximately `-.0033531`, still away from the coverage threshold. The later native FP32 query tolerance remains the predeclared absolute `1e-5`; the host agreement does not establish that native result.

| Program | Sampled lanes | Holdout coverage in each lane | Total area range |
|---|---|---:|---:|
| Retained three-box parent | 0, 64, 128 | 900/1,200 | .01631921–.01632087 |
| Original `.045` policy | 0, 64, 128 | 1,200/1,200 | .02192833–.02192953 |
| Guided `.034` policy | 0, 64, 128 | 1,200/1,200 | .01952130–.01952266 |
| Hand-defined four-box reference | One fixed program | 1,200/1,200 | .01440000 |

The objective remains `coverage - FP32(.02)*leaf_count - FP32(.005)*union_area`. Under exact packed-cost arithmetic, the guided training-score improvement over the original policy is approximately `1.2034e-5` in each sampled lane. The corresponding resident FP32 score change is separately reported in the [guidance comparison](../guidance_comparison/REPORT.json); rounding means the two figures need not be identical. This assessment does not change weights or thresholds to obtain a pass.

All ten programs pass their [exact packed-constant certificates](exact_certificates.json), with no tolerance on containment or separation inequalities. Each also rejects all 736 outside-quota probes reused from the first assessment. Those probes are explicitly not part of the fresh holdout count; the certificate provides the general region-containment result.

The evidence supports the AI's narrower policy choice: a smaller new leaf covers the declared unseen support while using less region area than the original proposal rule. The fixed reference retains a better total area penalty. Neither policy has been shown to outperform a conventional allocator or to discover a physical law, and the six-lane sample does not establish holdout behavior for all 129 lanes.
