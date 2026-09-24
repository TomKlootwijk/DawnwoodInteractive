# Dawnwood situated-operator experiment

Run `20260924-143343-84dbd9fd`; 2026-09-24T12:33:43.262137+00:00.

Kernel **0.5.1-rtx1**, profile **DWI-N1-0.5**, device **NVIDIA GeForce RTX 5070 Ti Laptop GPU**.

Executable SHA-256: `cb6b069a2082b2ee55cdf57a8332d4c1904f2190ba4061a416f63c6d83911015`.

257 states; 16 epochs; recorded stride 4.

## Live operator field

Unchanged initial state and live mutable operator field.

CPU/GPU verification: {'passed': True, 'bitwise_equal': True, 'epochs_checked': 4, 'validation_layer_enabled': False}.

Final state SHA-256: `5a5d55f9e364444ad80dc408b4d0df8a1150f0f0b1c5f937da0fed42241e5f9d`.

Final operator SHA-256: `aaf0448acf6505dda30d1b5e03a709bd86b04163514487a84d6c75b6da340d38`.

## Shifted operator anchor

Shifted only operator 30 anchor by (0.2, 0.1), applying the Klein seam/orientation rule.

CPU/GPU verification: {'passed': True, 'bitwise_equal': True, 'epochs_checked': 4, 'validation_layer_enabled': False}.

Final state SHA-256: `2dd8245ae48a4705758a1b502f3d4f0160f85cc8ee533f9b88d97b72398bb66e`.

Final operator SHA-256: `4853beb80eef5aa3ce95cbb8cbc6ebe5b8d359c2885db6e1a462474d7b04d578`.

## Changed amplitude phase

Applied an exact pi phase shift to channel a in every initial state by flipping ar/ai sign bits. Stored energy and all non-amplitude words are unchanged.

CPU/GPU verification: {'passed': True, 'bitwise_equal': True, 'epochs_checked': 4, 'validation_layer_enabled': False}.

Final state SHA-256: `2ccfebdd83caac706dbfd0ac0fde8d84ef7f1a6c152307da9295d24a9cb46828`.

Final operator SHA-256: `aaf0448acf6505dda30d1b5e03a709bd86b04163514487a84d6c75b6da340d38`.

## Complete-record comparisons

| Variant against live | Changed states | Changed state words | Changed operators | Changed operator words |
|---|---:|---:|---:|---:|
| shifted | 257 | 4189 | 31 | 82 |
| phase | 257 | 1269 | 0 | 0 |

## Interpretation

- These runs execute the unchanged DWI-N1-0.5 / 0.5.1-rtx1 numerical kernel. They do not replace it with a separate simulation.
- Every variant starts from one common checkpoint, with only the recorded intervention. Complete states are compared; the UI state table is sampled.
- Recorded frames are checkpoint boundaries. Kernel setup/readback occurs at each boundary, so this authoring tool is not a throughput benchmark.
- Program and anchor changes are interventions in the acting definition. An observed effect establishes influence, not useful learning or complete architectural closure.
- Core/synchronization validation is not enabled by this tool. Per-variant CPU/GPU comparison executes the actual intervention; the separate RTX campaign records validation-layer evidence.
- No application performance claim follows from a changed trajectory. Proposed constraint, memory and planning applications have separate contracts in the roadmap.
- The exact amplitude-phase intervention changed 1028 final amplitude words, 0 other non-energy state words, and 0 operator words. This is a finite-run witness for the amplitude-to-operator feedback question, not an all-input proof.
