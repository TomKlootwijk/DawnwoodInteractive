# Numerical source-body integration: DWI-XIR-0.1

24 September 2026. This campaign evaluates explicitly bound source operator
bodies on CPU and the actual **NVIDIA GeForce RTX 5070 Ti Laptop GPU**.
It does not execute the source's complete situated recurrence and does not claim
full architectural adherence or saturation performance.

## Implemented and measured

The compiler reads an actual operator body from the restored source catalogue,
resolves its explicit numerical expression, and emits bounded FP32 instructions.
An inline expression can replace that body. The shared C++/GLSL evaluator reads
those instructions; there is no native case for the name of the application or
for `Hadamard_mitosis`. Source fields and placements remain identified as
unlowered in every compilation manifest.

| Direct experiment | Observed result |
|---|---|
| Early formalization Eq7 `H diag(1,exp(i*phase)) H` | 257 complex-pair inputs; CPU/GPU bit-identical; maximum component error `3.643339403502921e-7` against an independent complex-matrix expression |
| Pair-norm preservation on those inputs | Maximum relative energy error `2.784104912776674e-7`; no renormalization |
| Phase-zero source seed | Identity within `1.1920928955078125e-7`, not a bitwise mathematical identity |
| Local Euclidean sphere binding | Four outputs exactly `[-1,0,4,1]` |
| Proposed 2×2 Frobenius double-dot binding | Authored example exactly `70` |
| External numerical body edit | Negating the first output changes 256 of 257 rows, exactly as declared; other outputs unchanged; same evaluator executable/shader |
| Complete evaluator instruction vocabulary | All 18 opcodes executed; 64 scalar outputs agree with independent elementary formulas within maximum error `1.0681886131180818e-7` |
| Zero-input constant program | CPU/GPU agree, including preserved negative-zero bits |
| Invalid square root, division by zero, overflow, eager invalid branch, and failed radius guard | First-failure statuses agree bit-for-bit across CPU/GPU; failed rows are zeroed; healthy rows still return their values |
| Malformed programs and source declarations | 11 native and 11 frontend cases rejected before producing output |
| Vulkan validation | Enabled for all recorded GPU executions; zero errors and warnings |

The final-build campaign comprises **11 workloads, 537 lanes and 2,142 output
words**, with identical CPU/GPU statuses and output bits. Five lanes deliberately
fail numerical preconditions or arithmetic. The initial three-binding campaign
and final rebuilt artifact return identical binary results. The final build
has no compiler warnings; the shader passed `spirv-val --target-env vulkan1.1`.

The independent hinge reference uses the closed complex matrix with
`(1+exp(i*phase))/2` and `(1-exp(i*phase))/2`, rather than replaying compiler
instructions. It uses the actual packed FP32 inputs. Original JSON input
rounding is recorded separately in each manifest. Phases in this dataset span
approximately `[-pi,pi]`; this is not an all-FP32 accuracy bound.

## Reproduction and artifacts

- [commands.json](commands.json): exact commands, exit codes, executable
  identities and validation requests. Matching stdout/stderr files retain raw
  runtime reports and failures.
- [independent_numeric_audit.json](independent_numeric_audit.json): independent
  complex-matrix, primitive and contraction comparisons.
- [extended_numeric_audit.json](extended_numeric_audit.json): body edit,
  instruction execution and failure cases from the final executable.
- [final_artifact_audit.json](final_artifact_audit.json): final/initial result
  identity, independent instruction values and validation reports.
- [rejections/summary.json](rejections/summary.json): all 22 rejected input
  cases, messages and absence of produced results.
- [hadamard/manifest.json](hadamard/manifest.json),
  [sphere/manifest.json](sphere/manifest.json),
  [double_dot/manifest.json](double_dot/manifest.json): source hashes, saved
  original inputs, selected expressions, instructions and partial-lowering
  boundaries.
- [Build record](../../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/bin/windows-source/build.json): compiler commands, paired source/shader hashes and final artifacts.

Final executable SHA-256:
`c7f0ab76c3956222f3abbf93b214d0ab3c2d8be6b682ec3f531d1c7c6df68e01`.
Shader SHA-256:
`c2b19ba3901e7fcd8ac1cbd22410de53dfee6e43fca044fd44239b259f782f44`.

Run the published headless commands in
[source_bindings/README.md](../../source_bindings/README.md). CPU timing covers
the evaluation loop. Vulkan timing covers host submission through fence wait,
excluding setup and readback; it is not a GPU timestamp or a saturation result.

## Remaining architectural work

This campaign verifies **compiled numerical bodies**, including the declared
two-Hadamard formula. It does not establish numerical carrier-relative fields
and anchors, typed application dispatch, the editable eight-stage source cycle,
resident operator/metarule changes, whole-state return, or a complete domain
application. The old N1 mixer and schedule are unchanged historical bindings.

The [integration ledger](../../docs/SOURCE_NUMERICAL_INTEGRATION.md) retains the
31 operator requirements and full stage dependencies. A strict-adherence claim
for the complete architecture remains unproved and must wait for those
requirements to be implemented and verified.
