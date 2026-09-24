# Explicit numerical source bindings

[resident_v0.1.json](resident_v0.1.json) adds **DWI-RESIDENT-0.1**. Its selected
Hadamard, pinion and mutation records retain live executable handles, parameters
and anchors. The old controllers compute replacements, including the mutator's
own successor, and action dispatches through the newly published records.
The [resident documentation](../docs/RESIDENT_DEFINITIONS.md) states every
numerical choice, source dependency, validation result and remaining limitation.
Use `Dawnwood-Resident.cmd` to compile, run and inspect complete checkpoints.
This bounded component does not yet execute the full source catalogue or cycle.

[situated_v0.1.json](situated_v0.1.json) adds **DWI-APPLY-0.1**: the selected
source record's placement, field and body execute together. Its binding joins
phyllotaxis placement, intrinsic Klein distance and the early two-Hadamard
body through an explicit phase law. [Situated application documentation](../docs/SITUATED_APPLICATION.md)
states the formulas, units, source relationships and measured limits.

```powershell
.\Dawnwood-Apply.cmd compile --bindings source_bindings/situated_v0.1.json --operator hadamard --inputs source_bindings/examples/situated_inputs.json --output output/my_situated
.\Dawnwood-Apply.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_situated/program.bin --output output/my_situated/gpu.bin
.\Dawnwood-Apply.cmd inspect output/my_situated/gpu.bin --manifest output/my_situated/manifest.json
```

This composes one situated action. The source cycle and resident mutation still
need integration. The body-only command below retains its narrower scope.

[xir_v0.1.json](xir_v0.1.json) contains executable expression definitions for
three source-named body overloads. These expressions compile to the same finite
instruction representation for CPU and Vulkan. They are numerical components
for integrating the source application; the source cycle is not implemented by
this release.

From the repository root, with a fresh output directory:

```powershell
.\Dawnwood-IR.cmd compile --bindings source_bindings/xir_v0.1.json --operator hadamard --inputs source_bindings/examples/hinge_inputs.json --output output/my_hinge
.\Dawnwood-IR.cmd run --backend vulkan --device "RTX 5070 Ti" --input output/my_hinge/program.bin --output output/my_hinge/gpu.bin
.\Dawnwood-IR.cmd inspect output/my_hinge/gpu.bin --manifest output/my_hinge/manifest.json
```

Use `--backend cpu` and omit `--device` for CPU evaluation. `compile` refuses an
existing output directory. The native `run` command replaces its named result
file, so use distinct names for comparisons. `inspect` reports lane statuses as
well as numerical values; a failed lane's zero row is not a successful result.

The optional `DAWNWOOD_VALIDATION=1` environment variable enables Vulkan's
Khronos validation layer, which must be available. Numerical correctness is
checked separately against independent formulas. The
[recorded campaign](../output/source_ir_2026-09-24/REPORT.md) contains both kinds
of evidence, including actual RTX execution.

| Source body | Typed numerical operands/result | Provenance and scope |
|---|---|---|
| `Hadamard_mitosis` | Two complex amplitudes plus phase → two complex amplitudes | Early formalization, physical p6, Eq7: `H diag(1,exp(i*phase)) H`. The explicit phase is an operand; its pinion/field construction still needs integration. |
| `SDF_sphere` | Local `x,y,z,radius` → signed distance | Euclidean `sqrt(x*x+y*y+z*z)-radius`; the positive-radius guard is executable. Carrier-relative coordinate construction is not part of this component. |
| `Pinion_double_dot` | Two real 2×2 matrices → scalar contraction | Early formalization's proposed Frobenius interpretation. Tensor construction from current pinions still needs integration. |

The original named bodies resolve through this registry. A source operator can
instead carry `body: {"expression": ...}` with an explicit input list, named
output expressions and optional preconditions. Such an edit changes executable
instructions, rather than only an expression hash. Unknown symbols or syntax
are rejected. This does not give an unspecified symbolic name an invented law.

Each expression is a finite number, `{"input":"name"}`, or
`{"op":"operation","args":[...]}`. Operations are `add`, `sub`, `mul`, `div`,
`sin`, `cos`, `exp`, `sqrt`, `abs`, `min`, `max`, `neg`, `floor`, `less`,
`select` and `require`. Arithmetic uses the existing N1 portable FP32 helpers
where applicable. Declared guards execute before output expressions; arithmetic
domain errors and nonfinite intermediate values produce a failed lane status.

In this component `select` selects already computed operands: it is not a
short-circuit branch. A failing operand cannot be hidden by selecting the other
operand. Dynamic control flow and typed application dispatch are separate
integration requirements.

The compiler reports the selected source record, original file hashes, executed
body binding, input/output names, instruction count and unimplemented parts.
Its field and placement descriptions are retained as provenance but are **not
executed by the body-component command**. It cannot claim full situated action
or self-reference from this isolated numerical result.

The [integration ledger](../docs/SOURCE_NUMERICAL_INTEGRATION.md) retains the
whole source architecture, typed call requirements and remaining work. The
original [symbolic application](../source_workbench/README.md) is preserved
unchanged, and the existing N1/D1 numerical releases remain separate profiles.

To rebuild the separate Windows evaluator, use Python 3.10+ with
`Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/tools/build_source_ir.py`.
The tool accepts `--compiler` and `--sdk`; on this laptop it also locates the
existing cached LLVM-MinGW and Vulkan SDK. It compiles and validates the shader,
builds the executable with FP contraction disabled, and records source hashes,
commands and artifact hashes in `bin/windows-source/build.json`. Both
`dawnwood-source-ir.exe` and the adjacent `source_ir.spv` are required.
