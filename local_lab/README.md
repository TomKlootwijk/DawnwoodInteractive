# Dawnwood headless specialization tools

`specialize.py` compiles explicit domain constraints into the native
**DWI-D1-0.1** recurrence and returns audited candidate assignments.
`definition_experiments.py` separately inspects operator interventions in the
preserved **DWI-N1-0.5** executable. Both use Python 3.10+ and the standard
library. Run commands from the repository root.

These are numerical experiments, not the original source application. That
application is restored under [source_workbench](../source_workbench/README.md).
D1's fixed projection algorithm does not execute the source's editable
body/field/anchor application model; the
[literal application contract](../docs/LITERAL_APPLICATION_CONTRACT.md) identifies
the missing integration.

## Native domain run

```powershell
python local_lab/specialize.py --example enzyme_repair --count 257 --epochs 64 --stride 16 --output output/enzyme_repair_live_01
```

The bundled interpreter on this laptop is also usable:

```powershell
$dwPython = 'C:\Users\ietsm\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $dwPython local_lab/specialize.py --example metabolic_flux --count 257 --epochs 64 --stride 16 --output output/metabolic_flux_live_01
```

The executable is
`Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/bin/windows-domain/dawnwood.exe`.
The default backend is Vulkan and the device selector is `RTX 5070 Ti`.
The [recorded campaign](../output/domain_kernel_2026-09-24/REPORT.md) covers all
four examples, controller interventions, CPU/GPU agreement, input rejection,
and a 1,048,576-state saturation run.

The authored examples are `enzyme_repair`, `buffer_design`,
`resource_allocation` and `metabolic_flux`, in `domain_knowledge/native/`.
Read their sources and assumptions before interpreting returned values.

For a CPU-only run, also disable the separate GPU comparison:

```powershell
python local_lab/specialize.py --example resource_allocation --backend cpu --verify-steps 0 --count 257 --epochs 64 --stride 16 --output output/resource_cpu_01
```

`--backend cpu` alone still performs the default eight-epoch CPU/GPU verification.
Verification runs from the initial checkpoint and does not advance the production
trajectory. `--verify-steps 0` skips the comparison rather than reporting a pass.

## Compiled computation

The candidate is `q = physical_value / scale` in four declared coordinates.
State slots `px, py, pz, pw` store `q` in D1. A domain checkpoint starts with
`DWKD0001`; an ordinary N1 checkpoint starts with `DWKN0003`. The profile marker
prevents treating domain coordinates as the old inspection embedding.

Each extra operator stores one immutable affine law:

| Kind | Feasible set in normalized coordinates | Individual field |
|---|---|---|
| `equality` | `a·q = b` | `(a·q-b)/norm(a)`; absolute value supplies violation |
| `halfspace` | `a·q <= b` | `(a·q-b)/norm(a)` |
| `slab` | `abs(a·q-b) <= halfwidth` | `(abs(a·q-b)-halfwidth)/norm(a)` |

Mean nonnegative violation enters the existing geometry input before the root
operator body. One ordered projection sweep then updates the candidate at each
epoch's end. Operator 30's situated response controls each relaxation in
`[0.25, 0.95]`. Remaining violation returns through `state.field` to subsequent
mutation. The six existing primitives and the other N1 stages remain active.

The individual fields have exact Euclidean distance definitions in the declared
normalized metric, evaluated with native FP32 arithmetic. Their mean and the
body-transformed geometry are not automatically exact SDFs. Scientific law
records remain byte-for-byte protected; evolving solver behavior cannot change
the constraints to make a candidate appear feasible.

## Author a definition

Use `--spec path/to/definition.json` instead of `--example`. This finite example
repairs two-component balance proposals while fixing the remaining coordinates:

```json
{
  "name": "Two-component balance",
  "description": "A finite affine feasibility example",
  "coordinates": ["x", "y", "z", "w"],
  "unit": "dimensionless",
  "scale": [1, 1, 1, 1],
  "initial": [-0.4, 1.3, 0.1, 0],
  "spread": [0.2, 0.2, 0.1, 0],
  "constraints": [
    {"id": "balance", "kind": "equality", "normal": [1, 1, 0, 0], "offset": 1},
    {"id": "x_nonnegative", "kind": "halfspace", "normal": [-1, 0, 0, 0], "offset": 0},
    {"id": "y_nonnegative", "kind": "halfspace", "normal": [0, -1, 0, 0], "offset": 0},
    {"id": "z_fixed", "kind": "equality", "normal": [0, 0, 1, 0], "offset": 0},
    {"id": "w_fixed", "kind": "equality", "normal": [0, 0, 0, 1], "offset": 0}
  ],
  "sources": [],
  "assumptions": ["Authored mathematics, not measured data"],
  "tolerance": 0.00002
}
```

Four unique coordinate names, positive scales and initial values are required. `spread`
defaults to zeros. Supply one to 32 constraints with unique identifiers,
nonzero finite normals and supported kinds. Slabs require a positive
`halfwidth`; other kinds require zero. Tolerance is in normalized distance units, in `(0, 0.01]`. Unknown
definition keys and unsupported law kinds are rejected.

**JSON normals and offsets already describe normalized `q`.** The compiler does
not automatically convert physical coefficients. For `A·x <= b` with
`x_i = scale_i*q_i`, author `normal_i = A_i*scale_i`. Changing scales changes the
metric, projection behavior and tolerance interpretation.

Override an example's proposal with four physical values:

```powershell
python local_lab/specialize.py --example enzyme_repair --values '[0.7,0.5,0.2,0.1]' --count 257 --epochs 64 --stride 16 --output output/enzyme_custom_01
```

Lane zero is the declared proposal after normalization and FP32 storage. Other
lanes sample the declared physical neighborhood uniformly by coordinate.
`--seed` controls Python proposal sampling; native initialization retains its
default seed. These are candidate inputs, not scientific observations.

## Controller comparisons

Keep the definition, count, proposal seed and epoch budget fixed; use a new
directory for each `--controller` condition:

| Controller | Intervention |
|---|---|
| `live` | Native operator mutation remains enabled |
| `frozen` | Freeze the whole core LUT; situated responses may still vary with state |
| `edited` | Set operator 30's initial body to `0x342`, retaining live mutation |
| `constant` | Freeze the core LUT and zero operator 30's response, giving relaxation `0.6` |

The constant condition changes both mutation and controller response. Compare
actual residuals and feasible counts before inferring an improvement.

## Output and exit status

Every output directory must be new. The tool retains:

- `definition.json` and `invocation.json`: resolved definition and invocation.
- `seed.dwk`, `initial.dwk`, `epoch-*.dwk`: complete checkpoints.
- `*.command.json`, `*.stdout`, `*.stderr`, `*.json`: commands, executable
  hash, removed ambient overrides, timings, exit codes and native reports.
- `result.json`: saved-epoch constraint audits, feasible counts, CPU/GPU
  comparison and protected-law hashes.
- `solutions.csv`: every final lane's physical values and maximum normalized
  violation.

The audit separately uses float64 on the packed FP32 coefficients and on the
original JSON coefficients, evaluated at the returned FP32 candidates. Both
must pass. This catches literal equations that device quantization changes by
more than the declared tolerance.
It checks the whole population, separately from native FP32 evolution and from
CPU/GPU bitwise comparison. Inspect `final.all_feasible`, `final.max_violation`,
`final.per_constraint` and `laws_unchanged`.

Exit `0`: all candidates meet tolerance. Exit `2`: a completed run has unresolved
candidates. Exit `1`: input, execution or integrity failure. Nonconvergence is
not an unsatisfiability proof. Partial evidence remains on failure; output is
never silently overwritten or deleted.

Saved intervals resume checkpoints and incur setup/readback costs. These runs
are not saturation benchmarks. The wrapper clears ambient tuning/layer overrides
and does not enable Vulkan validation layers; layer-enabled evidence is separate.

## Preserved N1 definition experiments

These use `bin/windows-rtx5070ti/dawnwood.exe`, not the domain executable:

```powershell
python local_lab/definition_experiments.py --experiment compare --count 257 --epochs 16 --stride 4 --operator-index 30 --program 0x342 --output output/definition_compare_01
python local_lab/definition_experiments.py --experiment fidelity --count 257 --epochs 16 --stride 4 --operator-index 30 --output output/definition_fidelity_01
```

`compare` branches into live, frozen and body-edited conditions. `fidelity`
compares live, shifted-anchor and amplitude-phase conditions. Both retain
complete-record differences, checkpoints, command receipts, JSON, a Markdown
report and operator CSV change ledgers. JSON frame samples contain at most 512
states; comparisons use all states. First observed differences refer to saved
boundaries. See [local experiments](../docs/LOCAL_EXPERIMENTS.md).
