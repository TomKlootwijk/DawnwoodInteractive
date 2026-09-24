# Headless native experiments

Two profiles answer different questions. **DWI-N1-0.5** establishes the existing
operator/state dependencies. **DWI-D1-0.1** adds an explicit domain-coordinate
binding and native constraint projection controlled by the existing mutable
operator field. Keep their evidence separate. The
[D1 campaign](../output/domain_kernel_2026-09-24/REPORT.md) records four useful
domain workloads and causal interventions; the prior RTX campaign remains N1 evidence.

## Run and inspect a literal domain definition

From the repository root:

```powershell
python local_lab/specialize.py --example enzyme_repair --count 257 --epochs 64 --stride 16 --output output/enzyme_live_01
python local_lab/specialize.py --example buffer_design --count 257 --epochs 64 --stride 16 --output output/buffer_live_01
python local_lab/specialize.py --example metabolic_flux --count 257 --epochs 64 --stride 16 --output output/flux_live_01
python local_lab/specialize.py --example resource_allocation --count 257 --epochs 64 --stride 16 --output output/resource_live_01
```

Use new output directories. This laptop's interpreter can replace `python`:

```powershell
$dwPython = 'C:\Users\ietsm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $dwPython local_lab/specialize.py --example enzyme_repair --count 257 --epochs 64 --stride 16 --output output/enzyme_live_02
```

The native executable is
`Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/bin/windows-domain/dawnwood.exe`.
The wrapper creates an N1 seed, compiles a D1 checkpoint, performs the requested
per-epoch CPU/GPU comparison, and runs the domain trajectory on Vulkan by default.
It audits all returned assignments against both the actual packed laws and the
original authored coefficients in float64. Both must pass.

Read `result.json` and `solutions.csv`, retaining native reports, receipts and
checkpoints. Feasibility means every individual constraint is within the declared
normalized-distance tolerance. A small mean alone cannot hide one violated law:
the audit uses each candidate's maximum violation. Check `laws_unchanged` and
per-law violations alongside the whole-population feasible count.

Exit `2` records a completed but unresolved population. Preserve it. More epochs
may be a new declared experiment; they do not turn the earlier outcome into a
pass. Failure to converge does not prove the authored sets have no intersection.

## Controlled solver interventions

```powershell
python local_lab/specialize.py --example enzyme_repair --controller frozen --count 257 --epochs 64 --stride 16 --output output/enzyme_frozen_01
python local_lab/specialize.py --example enzyme_repair --controller edited --count 257 --epochs 64 --stride 16 --output output/enzyme_edited_01
python local_lab/specialize.py --example enzyme_repair --controller constant --count 257 --epochs 64 --stride 16 --output output/enzyme_constant_01
```

These pair with `enzyme_live_01` above. Hold proposal seed, input definition,
binary, device, count and cadence fixed. All modes use identical protected laws.
`frozen` disables core LUT mutation; its field-conditioned response may still
vary with state. `edited` changes operator 30's initial scalar body to `0x342`.
`constant` additionally replaces that response with zero, giving relaxation 0.6.

Compare initial candidate hashes, law hashes, returned assignments, saved-epoch
violations, feasible counts and actual timings. A changed controller trajectory
establishes influence; a usefulness claim requires a better declared outcome.
The four conditions need not converge at the same rate or to the same feasible
point. The implementation is not a nearest-point or objective-minimization solver.

One projection sweep occurs per native epoch. The selected controller acts on
each law's current distance, while the six original fields and the rest of N1's
recurrence continue. This is the causal connection being examined: domain error
enters the acting field and returned state; that state influences future operator
updates. The law coefficients themselves must remain unchanged.

## Finite acceptance record

| Question | Required observation |
|---|---|
| Was the right model compiled? | Saved input, coordinate scales, packed-law values, profile and checkpoint magic |
| Did the native backends agree? | Per-epoch `verify` output, tolerance and bitwise counters, first divergence if any |
| Were scientific constraints preserved? | Identical protected-law bytes throughout checkpoints |
| Did a candidate satisfy the task? | Independently audited per-law violation at declared tolerance |
| Did feedback matter? | Controlled live/frozen/edited/constant comparison of domain outputs |
| What remains unresolved? | Nonconverged cases, rejected definitions and explicit model assumptions |

Retain contradictory or impossible authored cases as unresolved observations.
Use the existing CLI and direct experiments; repository instructions prohibit
adding test source. No benchmark, scientific-model validity or all-device claim
follows solely from a successful native comparison.

The wrapper's `verify` work does not enable validation layers. To collect a
separate layer-enabled record, use the existing `tools/record_gpu_run.py` around
the domain executable and the exact `initial.dwk`, with explicit layer settings.
Zero messages are meaningful as layer evidence only when the report says the
layers were enabled. Do not transfer N1 saturation numbers to D1.

## Source architecture dependencies in N1

```powershell
python local_lab/definition_experiments.py --experiment compare --count 257 --epochs 16 --stride 4 --operator-index 30 --program 0x342 --output output/definition_compare_01
python local_lab/definition_experiments.py --experiment fidelity --count 257 --epochs 16 --stride 4 --operator-index 30 --output output/definition_fidelity_01
```

These commands use the preserved `0.5.1-rtx1` executable. They branch from a
common initial checkpoint and compare complete state/operator records. Their JSON
frame samples are smaller than the full comparison. A first difference at a
saved boundary is not necessarily the first divergent epoch.

The body intervention tests whether an acting definition changes other acting
definitions and numerical state. The anchor intervention tests whether operator
location affects computation through `dw_field` and `dw_apply`. A changed body
word or anchor alone is insufficient; inspect the downstream state.

The phase intervention reverses both sign bits of one complex channel, preserving
its initial energy exactly. Individual channel amplitudes do not currently drive
the N1 mutation or kinematic derivative. Compare operator and non-amplitude state
words separately from the deliberately changed amplitudes. This exposes the
present coupling boundary rather than redefining the source's intention.

## Architecture questions still requiring explicit bindings

The amplitude step currently uses one Hadamard followed by opposite phase
rotations. A two-Hadamard phase sandwich is a different composition. Editing the
named record changes a response, not the matrix or hinge count. Likewise, deeper
amplitude-to-rule feedback, full asymmetric-frame transport and expressing more
of the native evaluator as mutable geometry require specified equations and
separate profile evidence.

D1 does not silently claim those gaps are solved. It supplies a narrower useful
binding: authored affine law fields, candidates evolving inside the existing
recurrence, feedback-controlled projection and independent feasibility readout.
See [the tool guide](../local_lab/README.md) for authoring and
[the roadmap](SPECIALIZATION_ROADMAP.md) for further task contracts.
