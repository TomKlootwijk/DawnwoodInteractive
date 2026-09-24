# Native domain specialization: measured results

24 September 2026. **DWI-D1-0.1**, runtime **0.6.0-domain1**, actual
**NVIDIA GeForce RTX 5070 Ti Laptop GPU**, vendor `0x10de`, device `0x2f18`.
Executable SHA-256:
`6a682fede4bb7e4437b75754583411fa2509070699a52ccb2e3a280260d76bd0`.

This is a headless native extension of Dawnwood. Authored equations are packed
into protected integer-texture operator records. Four coordinates per state
carry the proposed domain assignment. Violations influence the evolving
operator field; its current mutation controller determines subsequent
projection relaxation. The CPU wrapper supplies inputs and audits returned
values. The GPU performs the actual domain updates without host intervention
between epochs. [Equations and ABI](../../docs/DOMAIN_KERNEL.md).

## Useful task results

All 257 proposals in each example satisfy every constraint at the declared
`2e-5` tolerance in normalized Euclidean coordinates. A separate audit checks
the original JSON coefficients as well as the FP32 laws actually executed.
Protected law records remain byte-identical.

| Authored problem | GPU epochs | Maximum violation of original laws | Result |
|---|---:|---:|---|
| [Enzyme conservation and occupancy](enzyme_live/result.json) | 64 | 5.5061e-7 | 257/257 feasible |
| [Buffer log-activity window](buffer_design_live/result.json) | 128 | 2.0231e-7 | 257/257 feasible |
| [Resource quantities under quotas](resource_allocation_live/result.json) | 128 | 5.9605e-7 | 257/257 feasible |
| [Synthetic steady-state metabolic flux](metabolic_flux_live/result.json) | 128 | 6.8826e-8 | 257/257 feasible |

The enzyme proposal `(E, ES, S, P)=(8,3,78,20)` µM returns approximately
`(7.599999,2.400001,77.800007,19.800000)` µM. Thus `E+ES≈10` and
`ES+S+P≈100`, with nonnegative species and the specified ES band. This is a
constraint-consistent assignment, not a simulated time course or experimental
biological result. Enzyme/buffer constants, resource quotas and the small flux
network are explicitly illustrative. Sources and assumptions accompany each
[native definition](../../domain_knowledge/native).

The [independent crosscheck](independent_field_crosscheck.json) examines all
1,028 returned points against original coefficients and separately invokes the
biochemical reference evaluator on all 257 enzyme results. The final
[launcher run](final_cli/result.json) verifies the current dual-audit CLI and
Windows command wrapper end to end.

## Does self-reference affect the task?

The [causal comparison](causal_comparison.json) records two directions:

- Changing only the domain ES proposals leaves the initial and epoch-1 core
  operators identical, then changes **all 31 core operators at epoch 2**.
  Task error returns into the mutation that acts on its own controller.
- Changing only the initial controller body from `0x341` to `0x342` changes
  **1,027 of 1,028 domain-coordinate words by epoch 4**. Protected laws remain
  identical. The changing executable body affects the task computation.

The four-epoch causal runs intentionally stop before convergence and retain
their unresolved outcomes. Separate 16-epoch controller comparisons all become
feasible. Their maximum residuals are live `8.9773e-6`, frozen `4.1515e-6`,
edited `6.9964e-6`, and constant-relaxation `8.6190e-6`. **This experiment does
not demonstrate an optimization advantage for mutation**; frozen feedback has
the smallest residual here. The executed return path is established, while
benefit requires task-specific comparisons. Projection equations/order remain
native; task-law distance is evaluated in domain coordinates, while the
controller is situated on the Klein carrier.

## Accuracy and implementation checks

- Existing [30 CPU fixtures](cpu_selftest.stdout) pass.
- All four examples compare every CPU/GPU state and operator word for their
  first 32 epochs with **zero bitwise differences**.
- [Synchronization validation](domain_sync_validation.stdout), enabled on the
  actual GPU for 16 flux epochs, reports zero warnings/errors and exact CPU/GPU
  agreement. [Staged evolution](domain_split_verify.stdout) also agrees exactly
  for 16 enzyme epochs.
- [N1 compatibility](n1_compatibility_verify.stdout) passes, and its complete
  16-epoch checkpoint is byte-identical to the older executable's segmented
  trajectory. This supports the measured preserved path, not every input.
- [Seven malformed native inputs](input_validation/results.json) are rejected,
  including wrong magic, invalid law count, missing protection, unknown body,
  unknown law kind and zero normal.
- [Contradictory constraints](infeasible_result/result.json) remain unresolved;
  the laws are not mutated into accepting the result.
- The [precision counterexample](precision_rejection/result.json) has zero
  violation of rounded FP32 coefficients but `0.03` violation of its literal
  authored equation. The current compiler correctly reports it unresolved.

The [128-epoch buffer comparison](buffer_full_verify.stdout) passes the original
`atol=1e-5`, `rtol=2e-5`, but is **not bit-identical**. First bitwise differences
appear at epoch 91 in the two auxiliary coordinates approaching zero. Maximum
absolute error over the run is `1.8427e-38`. The
[diagnostic](buffer_subnormal_analysis.json) and both epoch-91 checkpoints retain
the evidence, consistent with subnormal/flush-to-zero behavior. No tolerances
were relaxed. Arbitrary-horizon bitwise replay is not established.

## Laptop saturation

The [large native run](saturation/epoch-001024.json) completed **1,048,576 states
× 1,024 epochs**, or **1,073,741,824 state updates**, in **112.8336 seconds of
GPU time**. The entire invocation, including setup, readback and audit, took
134.3976 seconds. All state records passed native health checks. The
[complete-population dual audit](saturation/authored_and_packed_audit.json)
finds every state feasible, maximum original-law violation `5.5061e-7`.

The [telemetry receipt](domain_saturation.command.json) and
[raw samples](domain_saturation.telemetry.csv) record 100% peak GPU utilization,
approximately 98.1% mean among numeric samples, peak 80°C, and no reported
thermal-slowdown samples. This saturates compute, not VRAM: the maximum observed
device-wide memory usage was 579 MiB. The separate
[N1 capacity campaign](../rtx5070ti_laptop_2026-09-24/REPORT.md) exercised the much
larger memory population; its capacity is not relabeled as a D1 measurement.
Power readings contain implausible outliers, including 36,117 W; no power or
energy-efficiency claim is made from them. Raw telemetry is preserved.

The large checkpoints and `solutions.csv` remain locally under
`local_lab/runs/domain_saturation/`, excluded from Git. The tracked evidence
contains definitions, exact commands, binary hashes, complete-population
audits, telemetry and native reports. Small domain runs retain all checkpoints.

## Reproduce

```powershell
.\Dawnwood-Specialize.cmd --example enzyme_repair --output output/my_enzyme_run
.\Dawnwood-Specialize.cmd --example metabolic_flux --output output/my_flux_run
.\Dawnwood-Specialize.cmd --spec path/to/my_fields.json --output output/my_custom_run
```

Use a fresh output directory. See [authoring instructions](../../local_lab/README.md)
for the four-coordinate schema, units/scales, supported law kinds and controller
conditions. The shader build's first attempt failed on a reserved GLSL variable
name; its raw failure is retained beside the corrected successful build.
