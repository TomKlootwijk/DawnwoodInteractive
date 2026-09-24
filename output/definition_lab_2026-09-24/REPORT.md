# Definition interventions on the laptop GPU

24 September 2026. Actual RTX 5070 Ti Laptop GPU execution of DWI-N1-0.5,
runtime 0.5.1-rtx1. Binary SHA-256:
`cb6b069a2082b2ee55cdf57a8332d4c1904f2190ba4061a416f63c6d83911015`.

Each campaign used 257 states, 16 epochs, and complete checkpoints every four
epochs. Every intervention began from a shared initial checkpoint. Its first
four epochs passed CPU/GPU verification with zero differing words; all recorded
GPU readbacks passed numerical health checks. The two independent live runs
returned identical state and operator hashes.

| Intervention versus live | Changed states | Changed state words | Changed operators | Changed operator words |
|---|---:|---:|---:|---:|
| Freeze the operator field | 257 | 7,424 | 31 | 202 |
| Mutation controller body `0x341` → `0x342` | 257 | 5,910 | 31 | 151 |
| Move controller anchor by `(0.2,0.1)` | 257 | 4,189 | 31 | 82 |
| Apply an exact π phase shift to complex channel a | 257 | 1,269 | 0 | 0 |

Changing the controller's body or situated position affects actual computation.
The phase intervention changed 1,028 amplitude words and energy words, but no
other state words and no operator words. This is a measured limitation of this
binding's amplitude-to-controller feedback, consistent with its source code.
It is not evidence that the broader source architecture cannot support that link.

The raw reports' `first_*_difference_epoch` fields identify the first **recorded
boundary**, with a four-epoch stride; they are not measurements of the first
native epoch at which divergence occurred. Later headless runner code names
these fields `first_observed_*` to make that distinction explicit.

- [Controller/feedback experiment](compare/report.md), [complete result](compare/result.json).
- [Anchor/amplitude experiment](fidelity/report.md), [complete result](fidelity/result.json).

Each subdirectory retains original command receipts, stdout/stderr, intervention
checkpoints, and all returned snapshots. Historical JSON export URLs refer to
an abandoned local UI; the files themselves remain in these directories.
Current reproduction is headless through
[`local_lab/definition_experiments.py`](../../local_lab/definition_experiments.py).
The separate [DWI-D1 domain campaign](../domain_kernel_2026-09-24/REPORT.md)
tests the new task-bearing domain profile rather than attributing it to N1.
