# DWI-XIR-0.2: portable logarithm and phase angle

The resident-v2 expression vocabulary adds natural logarithm and two-argument
phase angle. These functions let an authored PHI body express a numerical
log-polar binding. They do not by themselves select that binding, implement a
source phase, or establish the complete application cycle.

The controlling source connects log-polar encoding to the current LUT and
operator motion: original source pages 3–4, 11–12 and 14–16; restored
[unified specification](../source_workbench/Dawnwood_Interactive_v0.2/docs/unified_specification.md),
section describing PHI; source catalogue record 2, `phi`; and
[`kernel.py`'s `_log_polar`](../source_workbench/Dawnwood_Interactive_v0.2/src/dawnwood/kernel.py).
The formalization explicitly leaves log base, phase coding and numerical
precision to the editable PHI binding. Natural log, radians, the domains below
and these approximations are declared implementation choices, not recovered
source equations. The authored body still determines its operands and outputs.

## Interface and version boundary

The shared C++/GLSL implementation is
[`source_math_v2.inc`](../Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3/include/source_math_v2.inc).
Its caller must include `numeric_types.inc` first, exactly once. It exports:

```cpp
bool dw_source_log_valid(float x);
float dw_source_log(float x);
bool dw_source_atan2_valid(float y, float x);
float dw_source_atan2(float y, float x);
```

[`source_ir_v2.py`](../local_lab/source_ir_v2.py) supplies a separate
`ExpressionCompiler`, operation tables, the existing validation/packing helpers
and `compile_binding(binding)`. It neither modifies v1 globals nor aliases the
v1 body-compilation CLI as a v2 compiler. Existing operation subtrees compile to
the same instruction tuples. Nested v2 operations use the same postorder SSA,
exact-key validation, structural instruction sharing, 256-instruction limit,
64-input limit, 32-output limit and eager failure order as v1. No algebraic
rewriting or constant folding is introduced.

| JSON expression | Four-word instruction | Runtime domain failure |
|---|---|---|
| `{"op":"log","args":[x]}` | `[18, x_register, 0, 0]` | reason 5 |
| `{"op":"atan2","args":[y,x]}` | `[19, y_register, x_register, 0]` | reason 6 |

The instruction width remains four little-endian uint32 words. A v2-compatible
enclosing resident format/evaluator is required; the frozen v1 loaders reject
opcodes 18 and 19. Reusing instruction layout does not make these operations
executable by a v1 binary. Domain errors use the resident interpreter's ordinary
XIR-failure path and transaction rollback. Invalid direct helper calls return a
canonical quiet NaN (`0x7fc00000`); the interpreter checks validity first and
reports the specific reason instead.

## Input domains and signed axes

`log(x)` accepts only strictly positive **normal finite FP32** values: bit
patterns `0x00800000` through `0x7f7fffff`. Zero of either sign, negative values,
subnormals, infinities and NaNs fail with reason 5. `log(1)` returns positive
zero. The function is the natural logarithm, not base 2 or base 10.

`atan2(y,x)` accepts finite normal values and either signed zero for each
operand, but rejects the origin, including all four signed-zero pairs. Either
subnormal input, infinity or NaN fails with reason 6. The result is in radians,
with the following bit-defined endpoints:

| Arguments | Result |
|---|---|
| `atan2(+0, positive x)` | `+0`, `0x00000000` |
| `atan2(-0, positive x)` | `-0`, `0x80000000` |
| `atan2(+0, negative x)` | nearest FP32 `+pi`, `0x40490fdb` |
| `atan2(-0, negative x)` | nearest FP32 `-pi`, `0xc0490fdb` |
| `atan2(positive y, either signed zero)` | nearest FP32 `+pi/2`, `0x3fc90fdb` |
| `atan2(negative y, either signed zero)` | nearest FP32 `-pi/2`, `0xbfc90fdb` |

Normal arguments can have a subnormal or zero magnitude ratio. The corrected
integer-assisted `dw_div` returns that ratio's rounded bits. A small-angle
branch avoids floating-point multiplication on a tiny ratio, and the final
sign is applied through integer bits. Thus the helper intends to preserve a
representable subnormal small-angle result even though subnormal **inputs**
are outside its domain. This is not a promise that later, unrelated arithmetic
preserves subnormals on every device. Actual device equivalence still requires
measurement, including these cases.

## Ordered approximations

The functions use explicit FP32 intermediate values, GLSL `precise` and C++
noncontraction flags. They call the existing corrected `dw_div`; neither calls
native logarithm or native arctangent. Existing v1 arithmetic files are unchanged.

For log, bit decomposition produces `x = m * 2^e`. A possible factor-of-two
adjustment centers `m` approximately in `[1/sqrt(2), sqrt(2)]`. Then
`z = (m-1)/(m+1)` and the ordered polynomial evaluates

```text
log(m) ~= 2 * (z + z^3/3 + z^5/5 + ... + z^13/13)
log(x) ~= e * ln2_hi + (log(m) + e * ln2_lo)
ln2_hi = 0.693145751953125
ln2_lo = 0.000001428606765330187045
```

The atanh-series truncation error over the mathematical reduced interval is
below `5e-13`. That bound excludes FP32 range reduction and polynomial rounding;
it is not a bound on the implemented result.

For atan2, the absolute-value ratio is `min(abs(x),abs(y))/max(abs(x),abs(y))`,
which avoids overflow. Ratios at most `2^-12` use the ratio directly; the omitted
cubic correction is below 0.34 FP32 ULP in that interval. Larger ratios use
`atan(r)` directly below `tan(pi/8)`, or
`pi/4 + atan((r-1)/(r+1))` above it. The reduced argument has magnitude at most
approximately `sqrt(2)-1`. The odd alternating Taylor polynomial runs through
degree 21. Its mathematical truncation error is below `7e-11`; FP32 range
reduction and rounding are additional errors. Split pi/4, pi/2 and pi constants
restore octant and quadrant; the y sign bit selects the final sign.

These are approximations. Neither implementation is claimed correctly rounded
for every legal input or independently proved bit-identical across all devices.

## Direct CPU accuracy check, 24 September 2026

A temporary C++ audit compiled with the bundled llvm-mingw `clang++`, C++17,
`-O2 -ffp-contract=off -fno-fast-math`, and static linking. It compared the
helpers with host `std::log(double)` and `std::atan2(double,double)`, using the
actual FP32 inputs promoted exactly to binary64. The reference has much higher
precision but is not an arbitrary-precision proof oracle.

| Function | Evaluations | Largest absolute error | Largest ULP distance from binary64 reference rounded to FP32 |
|---|---:|---:|---:|
| log | 12,485,252 | `3.865695589411189e-6` | 2 |
| atan2 | 18,001,604 | `2.810667085739738e-7` | 2 |

The log sweep sampled every normal exponent with mantissa stride 257, every
FP32 value between bit patterns `0x3f600000` and `0x3fa00000`, and selected
boundary neighborhoods. The atan2 sweep combined deterministic pseudorandom
normal pairs across exponent ranges, a dense ratio grid with both argument
orders and all sign combinations, and boundary neighborhoods against tiny,
unit and maximal normal arguments. These counts include repeated endpoints.
Explicit domain guards and signed-axis cases had zero failures.

The frontend directly compiled nested log/atan2 expressions, rejected seven
malformed AST cases, left v1 operation tables unchanged and produced identical
instructions for an existing-operation-only expression. No persistent test
suite was added. Temporary reproduction files are
`tmp/source_math_v2_audit.cpp`, `tmp/source_math_v2_audit.exe` and
`tmp/source_math_v2_audit.json`; the JSON records source hashes and flags.

## Physical GPU comparison, 24 September 2026

The separate experiment in
[`output/source_cycle_2026-09-24/math`](../output/source_cycle_2026-09-24/math)
ran 27,240 independent diagnostic lanes for one resident-v2 epoch on the
**NVIDIA GeForce RTX 5070 Ti Laptop GPU**. The corresponding CPU and Vulkan
checkpoints were byte-identical, including all configuration, state, record
and failure-header words. Vulkan validation was enabled and recorded zero
errors and zero warnings. This does not assert all-device equivalence.

The diagnostic used a one-record generation increment followed by an explicit
fixed helper call for log and atan2. Source `phi` identity was retained only to
exercise the real resident format; placeholder field and placement functions
were not called. This is an elementary-math diagnostic, not evidence that PHI
or the complete source cycle has been integrated.

| Outcome | Count / result |
|---|---:|
| Successful lanes | 27,220 |
| Deliberate log-domain failures, reason 5 | 8 |
| Deliberate atan2-domain failures, reason 6 | 12 |
| Exact whole-epoch rollbacks, including provisional generation | 20 |
| Explicit signed-axis cases with exact expected bits | 8 |
| Successful representable subnormal atan2 outputs | 394 |
| Successful zero atan2 outputs | 379 |
| CPU/Vulkan differing checkpoint words | 0 |

Both native processes returned exit code **3**, the expected `lane_failure`
result for the intentionally mixed valid/invalid input set. All failing lanes
retained their previous state and complete record, epoch zero, and the expected
XIR reason, action step and failure header. Valid lanes advanced to epoch one
and generation one. No failure was silently counted as a successful result.

An independent binary64 comparison on the actual packed checkpoint inputs
gave the following sampled error on successful GPU outputs:

| Function | Largest absolute error | Largest ULP distance from rounded binary64 reference |
|---|---:|---:|
| log | `3.836931327327875e-6` | 1 |
| atan2 | `2.575875290844465e-7` | 2 |

The cases include deterministic normal FP32 samples spanning the exponent
range, dense ratios and their swaps in every quadrant, reduction boundaries,
extreme ratios, signed axes, and rejected subnormal/zero-domain inputs. The
random seed is `0xD02A724`; `cases.json`, `definition.json` and `program.bin`
retain every actual input and diagnostic program. The independent results are
in [`gpu_math_audit.json`](../output/source_cycle_2026-09-24/math/gpu_math_audit.json).
Both raw checkpoints, stdout/stderr, execution command receipts, native build
receipt, and the separately rerun CPU sweep with compiler receipt are retained
in that directory. The GPU executable hash is
`d6e08b44edf484571ad5d49954a8b3797c71e5bfc80ec4ce8cde795e8d865d29`;
the shader hash is
`9e90c89135a93a115db1ceaea5475338a389f8ab41ab7e64165751d4410f6098`.

These measurements validate this arithmetic component on the named workload
and device. Whole-cycle fidelity, application utility and physical claims
require their separate source and execution evidence.
