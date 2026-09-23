# Portable elementary functions — DWI-N1-0.5

The v0.4 recurrence used native `sin`, `cos`, and `exp` implementations independently on CPU and Vulkan. GLSL/SPIR-V elementary instructions do not promise identical results to the host C++ library. The measured first-epoch POCO amplitude mismatch and longer GTX drift therefore required eliminating this uncontrolled arithmetic difference before judging the recurrence itself.

`include/numeric_math.inc` now defines the same ordered FP32 arithmetic on both backends. It approximates the same sine, cosine, and exponential functions; it does not clip angles, remove fields, normalize amplitudes, or change the declared CPU/GPU tolerance. This changes individual FP32 results and thus the bitwise trajectory relative to v0.4. Old checkpoint records retain their layout, but continuation uses the new numerical definition.

## Sine and cosine

Arguments with magnitude at most 128 use a three-part pi/2 constant. The first two parts have short significands so their products with the small integer quadrant count are exact; the third supplies the remaining angle. Larger finite binary32 inputs use the exact product of the input's 24-bit significand and 256 fractional bits of 2/pi, then extract the quadrant and 48 fractional bits. Integer complementation occurs before conversion when the nearest quadrant is above the input, avoiding subtraction of two almost equal floating-point fractions. No shader int64 capability is required: GLSL uses `umulExtended`, while C++ computes its identical high/low uint32 result with uint64.

Reduced arguments are evaluated with degree-13 sine and degree-12 cosine Taylor polynomials on approximately [-pi/4, pi/4], using explicit noncontracting Horner arithmetic. Negative signs and quadrants are applied after evaluation. Signed zero is retained for sine; nonfinite inputs produce a quiet NaN. The full-range reducer is an independently written fixed-point implementation; the 2/pi mathematical constant is cross-checked against the published OpenLibm table.

## Exponential

Arguments are reduced as x = n*ln(2) + r, with |r| approximately at most ln(2)/2, using a two-part ln(2) constant. A degree-8 polynomial evaluates exp(r). The exponent is then constructed in the IEEE binary32 representation; subnormal outputs use explicit integer rounding to nearest/even. Inputs at or above the binary32 threshold 88.72283935546875 produce positive infinity; inputs at or below -103.97208404541015625 produce positive zero. These branches also handle positive and negative infinity respectively. NaN produces a quiet NaN before any integer conversion. Other finite inputs are reduced and scaled; near the maximum finite exponent the constructed result can also overflow. No finite coordinate is clamped into a smaller artificial domain.

Producing a subnormal bit pattern does not guarantee that a Vulkan device preserves it in subsequent floating-point arithmetic. The measured default recurrence uses ordinary normal magnitudes. Extreme custom parameter configurations still require state-health and backend comparison checks; this revision is not a proof of identical behavior for every finite checkpoint.

## Recorded approximation measurements

A temporary diagnostic program compiled with MSVC 19.44, `/O2 /fp:strict`, sampled 2,000,001 evenly spaced FP32 arguments in [-128,128], 1,992,127 finite random FP32 bit patterns (from 2,000,001 xorshift32 values seeded with 756, rejecting exponent 255) for trig, and 2,000,001 exponential arguments in [-103.97,88.72]. Each reference receives the exact double conversion of the sampled binary32 input. ULP comparisons use that reference rounded back to binary32. References were host double-precision `std::sin`, `std::cos`, and `std::exp`. It was an exploratory measurement, not a new repository test. The JSON record is `results/v0.5/portable_math_accuracy.json`.

| Function | Worst sampled error |
|---|---:|
| sin | 1.088186935e-7 absolute; 3 ULP versus rounded double reference |
| cos | 1.062778879e-7 absolute; 6 ULP versus rounded double reference |
| exp, normal reference result | 9.414731314e-8 relative |
| exp, all samples | 1 ULP versus rounded double reference |
| exp, subnormal reference result | 1.079641608e-45 absolute |

These are sampled measurements, not proven exhaustive worst-case bounds. The real-polynomial truncation errors on the reduced domains are smaller than binary32 rounding; the measurements also include range reduction and arithmetic rounding. These isolated function measurements do not establish backend integration or performance. The first portable-trig candidate still failed the 257-state GTX comparison at epoch 305. Square root and division were therefore also replaced by the integer-corrected operations described below; those preliminary GPU results do not validate the final arithmetic.

## Correctly rounded division and square root

Native GLSL division and square root can differ from the host result by a few last-place bits even when contraction is disabled. The final v0.5 candidate retains each native operation only to get an initial estimate on a safe, normalized argument. Its final value is selected with exact uint32 high/low integer products and IEEE round-to-nearest/even rules.

For division, both 24-bit significands are normalized first, including subnormal inputs. The estimate supplies a candidate integer quotient. Exact 24-by-24-bit products and correction loops determine the quotient floor and remainder. Twice the exact remainder selects the nearest significand; equality selects the even significand. Subnormal output rounding uses the discarded quotient bits and the original remainder together, avoiding double rounding. Signed zero and infinity are constructed from their IEEE bits. NaN, 0/0 and infinity/infinity return a quiet NaN. These rules replace all dynamic divisions in the recurrence, including division by six in the RK accumulation and geometric average. Polynomial constant coefficients remain compile-time constants.

For square root, exponent parity reduces the input to [1,4). The native square root supplies an integer candidate; exact squaring determines the floor root. If the floor is q, the midpoint squared is q*q+q+1/4. The radicand is an integer, so the exact remainder greater than q selects the upper root; a midpoint tie is impossible. Finite negative inputs and negative infinity return NaN, signed zero is preserved, and positive infinity remains infinity. Finite positive binary32 inputs have normal square-root outputs, including subnormal input values.

A separate temporary MSVC `/O2 /fp:strict` diagnostic evaluated 5,000,000 xorshift32 pairs seeded with 756. There were **4,961,170 finite divisions with nonzero denominator** and **4,980,524 finite nonnegative square-root inputs**. Every result bit matched the host's native correctly rounded operation: **zero mismatches**. Division cases included underflow and overflow results. See `results/v0.5/portable_rounded_accuracy.json`. This random sample verifies the implementation against that host; the integer rounding construction, not the sample count, explains why the arithmetic can remove backend-native rounding variation.

The optional shader build command `python tools/build_shaders.py --optimize --preserve-math-functions` marks the six portable math functions as SPIR-V `DontInline` before offline optimization. This avoids duplicating their full-range arithmetic into every field call during that offline pass. Adding `--preserve-interpreter-functions` also retains the available shape, body, field, application, geometry and derivative boundaries. Both are compiler-resource hints, not changed equations, measured speedups, or guarantees that a device driver will respect function boundaries. The accepted September 23 artifacts use both options; the phone additionally needs the smaller evolution entry points described below.

## September 16 audit and actual GTX result

The integer correction was reviewed separately for quotient normalization, sign handling, normal/subnormal boundaries, overflow carry and square-root rounding. An additional CPU diagnostic enumerated **all 16,777,216 binary32 inputs in [1,4)**, the two normalized square-root mantissa intervals. All returned bits matched the host square root. It also checked **2,496,400 signed division boundary combinations** spanning every binary exponent and neighboring mantissas, underflow midpoints, maximum finite values, zeros, infinities and NaNs: zero result-bit or NaN-class mismatches. Another **1,580 square-root boundary/special cases** had zero mismatches. These records are in `results/v0.5/portable_boundary_accuracy.json`; they are CPU evidence, not an exhaustive check of device behavior.

The September 16 optimized evolution SPIR-V contains **3,682 floating-point add/subtract/multiply/divide instructions**, all decorated `NoContraction`. Native Sin, Cos and Exp instructions are absent. Its one remaining native Sqrt instruction supplies the integer-corrected estimate described above. The predecessor's 10,244 arithmetic instructions were also all noncontracting, so merely adding noncontraction was not the missing fix. See the preserved historical record `results/v0.5/portable_spirv_inspection.json`; the current module counts appear below.

Actual GTX 1650 Ti verification of **257 states for 1,024 consecutive epochs** then passed every state and operator field at every epoch. Maximum absolute error and scaled error were both **zero**, with zero integer mismatches, nonfinite values, invalid snapshots or Vulkan core/synchronization validation messages. The command exited zero. The absolute/relative tolerances remained **1e-5 / 2e-5**. Raw evidence: `results/v0.5/verify_corrected_257_1024_v05.stdout` and its `.command.json`.

The trig/exponential replacement alone had delayed the GTX failure to epoch 305. Correcting the remaining division/square-root rounding removed that observed disagreement completely in the 1,024-epoch comparison. These interventions do not by themselves isolate which individual native division or square-root instruction contributed most. This historical result does not establish arbitrary-horizon agreement; the later phone evidence is separate below.

Preserving the six math function boundaries reduced that evolution shader to **315,372 bytes** despite adding the exact rounding corrections; the earlier trig-only fully inlined candidate occupied **1,052,796 bytes**. These are compiled artifact sizes, not runtime speedup measurements.

## September 23 phone compiler failure and shared split implementation

The actual POCO X7 Pro, model 2412DPC0AG with Mali-G720 MC7, initially failed to create the evolution pipeline: `vkCreateComputePipelines` returned `VkResult -3`. A separate attempt ended with a native Scudo out-of-memory abort during setup. This happened before a completed GPU comparison or capacity run; it was not evidence that the requested state population exceeded usable RAM. The initial reports remain under `results/v0.5/2026-09-23/phone_validation`.

Disabling pipeline optimization, retaining more function boundaries, and reducing repeated operator/segment call sites did not resolve the monolithic phone failure. The compact intermediate evolution module was 164,448 bytes, but driver compilation still failed. A later retry after the user closed YouTube reported **5,590,233,088 bytes of available system RAM before the probe**, and still returned the pipeline error (`phone_after_youtube/probe.json`). These observations do not isolate a pure compiler defect or rule out all memory pressure and driver conditions. They establish that freeing that amount of RAM and applying those hints were insufficient in the observed runs.

The accepted implementation shares `dw_prepare`, `dw_slope`, `dw_combine`, `dw_geometry`, and `dw_finish` between the CPU, monolithic GTX path, and split ARM path. ARM evolution runs eight dependent dispatches per chunk: prepare, four slopes, combine, geometry, finish. Operator mutation remains once per global epoch. The 96-byte scratch record holds adjusted step size, delta, fourth-stage Y-up, final field, route/jitter values and all four slopes. It is reused across at most 65,536 states, so its payload is bounded at **6,291,456 bytes (6 MiB)** rather than scaling with the whole population. State and checkpoint layouts are unchanged.

The fourth-stage Y-up expression is computed from the original point with updated delta and applied as two separate additions in that stage. FP32 expression grouping, geometry, amplitude rotation, inverse transform, feedback, and history are retained. Pipeline barriers connect the dependent passes; transient dispatch controls do not enter saved configuration. The split schedule successfully compiled and executed on the phone. This is an observed compatibility improvement; its extra dispatches and memory traffic require separate performance measurements.

The accepted shader build contains seven validated SPIR-V modules. `results/shader_build.json` records their complete SHA256 identities, compiler and validator; `results/v0.5/2026-09-23/split_spirv_inspection.json` records the inspection below.

| Module | Artifact bytes | FP add/subtract/multiply/divide instructions, all `NoContraction` |
|---|---:|---:|
| mutate | 46,636 | 236 |
| evolve, monolithic | 75,068 | 384 |
| prepare | 43,972 | 212 |
| slope, reused four times | 61,984 | 274 |
| combine | 44,164 | 241 |
| geometry | 44,236 | 206 |
| finish | 50,328 | 272 |
| Total across the seven modules | 366,388 | 1,825 |

All **1,825** inspected arithmetic instructions carry `NoContraction`. Native Sin, Cos, Exp and Fma are absent. Each module retains one native Sqrt instruction inside the corrected estimate implementation. The five split modules have the expected scratch member offsets and a 96-byte array stride. These are static module observations, not measured driver compiler memory, executed instruction counts or performance gains. Historical inspection records and failed candidates remain preserved.

## Actual phone numerical agreement and its scope

The accepted Android APK has SHA256 `8c86dbcd791a824b1402a5561c3ef3926a8f539900d0dcdf95b1563d89726430`. On the connected POCO, all **30 existing CPU fixtures** passed. CPU-versus-Vulkan comparisons also passed for **128 states × 16 epochs**, **257 × 1,024**, **4,096 × 256**, and **65,537 × 4**, the last crossing the dispatch-chunk boundary. Every checked state and operator word agreed bitwise: zero floating-point mismatches, integer mismatches, nonfinite values, invalid snapshots, maximum absolute error, or scaled error.

Evidence is in `results/v0.5/2026-09-23/phone_split/{selftest,verify}.json` and `phone_extended/verify_257_1024_sep23.json`, `phone_extended/verify_4096_256_sep23.json`, `phone_extended/verify_65537_4_sep23.json`, with associated command records and logs. These are actual Mali executions with `split_evolution=true`. Android Vulkan validation layers were **not enabled**, so zero diagnostic counters there do not constitute a validation-layer pass. The tolerances remain absolute **1e-5** plus relative **2e-5**; they were not relaxed to obtain agreement.

The scope is CPU and GPU evolution from **the same initialized snapshot on each host**. `src/cpu.cpp::initialize` still uses native host library square root, sine, cosine, logarithm and remainder operations. Independently generated Windows and Android initial snapshots therefore are not guaranteed bitwise equal. These comparisons do not establish matching trajectories across independently initialized binaries, arbitrary configurations, unlimited epochs, or physical accuracy.

The separate, completed phone capacity campaign advanced **14,569,792 states for two epochs** with full readback, valid state health and a retained digest. Its summed Vulkan timestamp interval was **11.91558916 seconds**, or **2,445,500.899 state updates per second**; actual Vulkan buffer/image allocations totaled **3,753,000,960 bytes**. Growth ended at the current shared-memory policy boundary without an allocation failure or serious runtime error. This large run establishes completed population and measured throughput under those conditions, not numerical equivalence for all those states or an absolute hardware maximum. The Android app work interval was 76.886 seconds and external launch-to-report interval 77.546 seconds; neither is GPU execution time. See `results/v0.5/2026-09-23/phone_capacity/summary.json` and `docs/PHONE_CAPACITY_v0.5.md` for the allocation, timing and policy details.

## Sources and limits

- SPIR-V GLSL extended instructions: https://registry.khronos.org/SPIR-V/specs/unified1/GLSL.std.450.html
- Published 2/pi digits and general range-reduction background: https://raw.githubusercontent.com/JuliaMath/openlibm/master/src/k_rem_pio2.c

The existing absolute tolerance 1e-5 plus relative tolerance 2e-5 remains unchanged. A successful polynomial approximation measurement is not itself CPU/GPU agreement or a claim about physical accuracy.



