# Routed matrix application audit

The source-declared graph routes through the current BST to source record **19 (`T_transform`)** and **18 (`inverse_T`)**, evaluates each selected record's placement and field, calls its typed body, and applies the resulting inverse matrix to the two complex channels. The graph contains the routing and matrix application; native code remains the generic resident interpreter.

All **seven paired CPU/Vulkan workloads** produced byte-identical complete checkpoints: **257 independent instances** per workload, **1,799 returned instance observations**, including 514 intentional failures. Vulkan validation was enabled with zero errors and warnings in every completed run. The complete application ran for 1, 8 and 64 epochs without lane failures. See [paired receipts](paired_summary.json) and [source/executable hashes](summary.json).

The 257 initial instances retain the source's complex wavefront seed. Carrier chart positions, neck bits and external phase vary explicitly. This is a bounded numerical sample, not an exhaustive proof over all possible inputs or resident definitions.

## Independent mathematics

Before execution, the experiment declared a `1e-6` bound on `||actual-reference||₂ / max(1, ||reference||₂)` and a `1e-6` maximum-entry bound on `T A − I`. The binary64 reference uses direct 2×2 formulas, `hypot`, `sin` and `cos`; it does not evaluate the source expression AST.

The diagnostic executes the same mutation plan and action calls. It captures actual live inputs and outputs at their call boundaries, replacing only the diagnostic state's writes. It is executed for one epoch and is not a valid application continuation. Every captured final pair was bit-identical to the corresponding full application result. [Capture map](diagnostic_capture_map.json)

| Quantity | Maximum measured error |
|---|---:|
| Authored T matrix, scaled vector error | 5.6469e-8 |
| Inverse of the actual packed T, scaled vector error | 8.8254e-8 |
| Maximum entry of T A − I | 1.0736e-7 |
| Extra graph matrix application, scaled vector error | 5.7430e-8 |
| Final complex pair through pinion and return, scaled vector error | 1.1329e-7 |

The evaluated inverse field selected the adjugate branch in 30 cases and the Schur branch in 227. Both branches therefore contributed to the audit. Every routed source index was correct for both neck values. [All captured values and comparisons](mathematical_comparison.json)

The added graph operation computes

`(a′, b′) = (A00 a + A01 b, A10 a + A11 b)`

for complex `a,b` and real matrix `A`. The existing pinion already applies `A`; consequently this graph deliberately adds another application before pinion's history/field contribution and final return rotation. It does not merely relabel the existing inverse. Against the unconditioned graph, returned amplitudes changed in **257/257** instances after one epoch, while the computed T and A remained identical at that epoch. [Application effect](full_application_effect.json)

## Typed failure and rollback

Two source-graph counterexamples exchange the destination of one matrix route while retaining its declared call contract. Both destinations exist and provide role zero. Routing the T call to inverse-T, or the inverse call to T, therefore reaches an incompatible function signature rather than a missing address or missing role.

Both CPU and GPU reported **status 11** at the corresponding dynamic body call, at action steps 831 and 878 respectively. Each case restored all old state bits and record words in **257/257 instances**, including provisional mutations, and left epoch zero unchanged. This is the runtime typed-call guard; it is not a numerical singular-matrix rejection. [Rollback evidence](wrong_interface_rollback.json)

The first launch omitted the local Vulkan validation-layer search path and stopped before producing a GPU checkpoint. Its logs remain in `attempt1_application_1/`; it is excluded from the seven completed pairs. The recorded experiment then set `VK_LAYER_PATH` explicitly and completed all checks. [Retained experiment](experiment.txt)
