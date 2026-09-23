# Dawnwood v0.4 - corrections and formalization changes

Date: 16 September 2026. Baseline formalization: the user-confirmed latest `Dawnwood_Interactive_Unified_v0.2.pdf`. Implementation baseline: numerical kernel v0.3. Source PDFs remain unchanged. This is a new numerical revision, not a claim that the original physical or universality proposals have been proved.

## Numerical corrections

| Change | Defect corrected | Observable consequence |
|---|---|---|
| Explicit FP32 constants | Unsuffixed C++ decimal literals promoted intermediates to double while GLSL used float. | CPU now follows the declared FP32 profile; old bitwise trajectories are not promised. |
| Non-contracted shader arithmetic | GPU arithmetic permitted multiply/add contraction and reassociation while CPU compiler flags prohibited contraction. | GLSL `precise`, including function return temporaries, emits `NoContraction` for basic arithmetic. Transcendental results remain backend dependent. |
| Overflow-safe feedback indices | `(stride*i+epoch+offset)` overflowed uint32 before reduction by N. | Exact reduced arithmetic implements the documented indices without requiring shader uint64. At N=257, i=1, epoch=4294967294, the two mathematical indices are 16 and 31; the old expressions gave 15 and 30. |
| Floating seam parity | Casting large finite seam counts to uint was outside the defined range. | Parity is reduced in floating point without that cast. FP32 cannot recover fractional detail already lost in a large coordinate. |
| Half-open remainder repair | The FP32 fractional part of a tiny negative value can round to 1. | A remainder equal to 1 is represented by 0.9999999403953552, retaining the computed seam orientation. |
| Canonical transient field queries | Three neighboring lifted images were searched even when RK stage coordinates were not canonical. | Field evaluation canonicalizes a local state copy before the search. Stored stages and double fourth-slot Y-up remain intact. |
| Structured inverse determinant | Expanded determinant subtraction could cancel large shear terms to zero. | Uses `cos(angle)^2+sin(angle)^2`. This avoids that cancellation but does not cure ill-conditioning or overflow at extreme parameters. |

## Shader compilation resources

Phone compilation exposed native compiler memory exhaustion even for one state. The build now marks the actual shader loops `DontUnroll` and uses scoped precise-return blocks instead of artificial `do/while(false)` loops. This reduces loop-merge constructs from 20 to 3 in mutation and from 22 to 4 in evolution while preserving arithmetic decorations. These are compiler hints, not a guarantee of driver compatibility. The validation record contains the actual phone outcome. Offline optimization alone did not resolve the phone compiler failure. A subsequent four-stage loop shares one derivative call site while retaining all stage inputs, slopes and double Y-up. This reduced the optimized evolution module from 578,760 to 268,608 bytes. The 257-state, 95-epoch CPU full-state/LUT digest remained exactly `0380ebf43a2cfb07`, and the existing fourth-slot fixture still passed. Final artifacts use `tools/build_shaders.py --optimize`; the default unoptimized variant remains available for diagnosis.

## Runtime and evidence corrections

- Validate complete checkpoints and snapshots: sizes, finite values, chart coordinates, orientation, route, inverse reference, jitter value, positive primitive dimensions and every bytecode nibble. Python editing/readout uses the same storage invariants.
- Reject partly parsed floating arguments, zero-epoch verification, and epoch exhaustion before a run. A zero-epoch ordinary run remains valid for readback.
- Include prior transfer writes in the dependency for GPU readback, including a run with no evolution dispatch.
- Account for actual padded allocations against each selected Vulkan heap, including staging and a zero-free-budget condition. Apply the declared 80% startup-free-budget policy rather than estimating against the largest heap.
- Capture Vulkan validation messages and make validation errors fail the command. Record warnings and the actual device separately.
- Report all numerical configuration values with enough digits to reproduce FP32 inputs. Unhealthy final records fail visibly; a health pass denotes structural/finite validity, not an unlimited norm-accuracy guarantee.
- Claim reporting requires successful commands, valid reports and actual state hashes. A missing explicitly requested device cannot produce a successful device-validation exit.
- Phone reporting checks final state health and identifies the actual model; APK creation alone is not a phone success.

## Formalization corrections

`FORMALIZATION_v0.4.md` preserves the latest baseline's fifteen sections and all 31 named catalogue entries, with explicit numerical bindings:

- The carrier is fixed; the situated operator field evolves. The present law is a canonical-chart discrete recurrence. Correct seam wrapping does not establish a smooth tangent field or transported asymmetric operator frames.
- The numerical amplitude hinge follows integration. Double Y-up acts on the fourth intermediate position before its derivative. These specialize open symbolic bindings and are not asserted to commute with the baseline's written order.
- The implicit tree is a routing tree. Child-index arithmetic alone does not prove binary-search semantics.
- The colon operation has explicit tensor operands. The phase quantity is an unscaled second difference over epochs. Modified RK4 does not inherit an unproved fourth-order convergence guarantee.
- A disabled jitter switch fixes the bit at zero; it does not remove the negative epsilon offset. Disabled feedback freezes operator mutation while state/history evolution continues.
- Finite bytecode self-modification does not implement arbitrary symbolic bodies or prove universality. The apex field is unsigned; transformed and blended fields need not remain exact metric SDFs.
- Bayer denotes ordered-threshold downstream readout, not a camera color-filter simulation. Full-state storage remains separate from BC5 texel-size scenarios.

## Compatibility and validation limits

The 128-byte state, 64-byte operator, 64-byte configuration, and `DWKN0003` checkpoint storage layout remain compatible. A valid v0.3 snapshot can seed v0.4, but subsequent dynamics use corrected equations and arithmetic. Checkpoints do not contain a semantic-profile tag; record the executable/profile with them.

No new tests were written. Existing checks and manual invocations supplied the evidence in `../results/v0.4/VALIDATION.md`; every retained command includes exit status and raw output. Short-run backend agreement does not imply indefinite agreement. The longer 257-state comparison still exceeded the unchanged tolerance after the arithmetic corrections; details remain in the validation record.
