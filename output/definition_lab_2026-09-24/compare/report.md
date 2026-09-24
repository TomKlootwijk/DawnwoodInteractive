# Dawnwood situated-operator experiment

Run `20260924-143217-7bb33109`; 2026-09-24T12:32:17.945937+00:00.

Kernel **0.5.1-rtx1**, profile **DWI-N1-0.5**, device **NVIDIA GeForce RTX 5070 Ti Laptop GPU**.

Executable SHA-256: `cb6b069a2082b2ee55cdf57a8332d4c1904f2190ba4061a416f63c6d83911015`.

257 states; 16 epochs; recorded stride 4.

## Live operator field

Unchanged initial state and live mutable operator field.

CPU/GPU verification: {'passed': True, 'bitwise_equal': True, 'epochs_checked': 4, 'validation_layer_enabled': False}.

Final state SHA-256: `5a5d55f9e364444ad80dc408b4d0df8a1150f0f0b1c5f937da0fed42241e5f9d`.

Final operator SHA-256: `aaf0448acf6505dda30d1b5e03a709bd86b04163514487a84d6c75b6da340d38`.

## Frozen operator field

Set Config.feedback=0 in the initial checkpoint; the kernel freezes the entire operator field.

CPU/GPU verification: {'passed': True, 'bitwise_equal': True, 'epochs_checked': 4, 'validation_layer_enabled': False}.

Final state SHA-256: `19071325d6bdfd4a64315778595c7a81c5c21112fe6729b6c54ef2032e25b806`.

Final operator SHA-256: `c6450b5b697618bfe5442361b831addd248b1fb876de7f650681ecf03e902bf3`.

## Edited operator body

Changed only operator 30 (mutation) program from 0x00000341 to 0x00000342.

CPU/GPU verification: {'passed': True, 'bitwise_equal': True, 'epochs_checked': 4, 'validation_layer_enabled': False}.

Final state SHA-256: `48e3a03e592422543748590369e99b861d8116222190d2f06452694d6f3a2732`.

Final operator SHA-256: `01a2903d695dc1f46d2bac429ce04a13392c14f3636f8be5fcc7dfa1967109e5`.

## Complete-record comparisons

| Variant against live | Changed states | Changed state words | Changed operators | Changed operator words |
|---|---:|---:|---:|---:|
| frozen | 257 | 7424 | 31 | 202 |
| edited | 257 | 5910 | 31 | 151 |

## Interpretation

- These runs execute the unchanged DWI-N1-0.5 / 0.5.1-rtx1 numerical kernel. They do not replace it with a separate simulation.
- Every variant starts from one common checkpoint, with only the recorded intervention. Complete states are compared; the UI state table is sampled.
- Recorded frames are checkpoint boundaries. Kernel setup/readback occurs at each boundary, so this authoring tool is not a throughput benchmark.
- Program and anchor changes are interventions in the acting definition. An observed effect establishes influence, not useful learning or complete architectural closure.
- Core/synchronization validation is not enabled by this tool. Per-variant CPU/GPU comparison executes the actual intervention; the separate RTX campaign records validation-layer evidence.
- No application performance claim follows from a changed trajectory. Proposed constraint, memory and planning applications have separate contracts in the roadmap.
