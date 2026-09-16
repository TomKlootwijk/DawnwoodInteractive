# Dawnwood Interactive: complete integer edition requirements

This is the source and completion contract for the new integer edition. It does not replace the historical v0.3 binding, measurements or PDF. The current request is to implement and optimize the whole computation using integer words, integer SDF operations and a small log-polar LUT. Converting only SDF membership into a mask while leaving the circulation, RK stages, log/phase encoding or dot products in floating point does not meet that request.

The source is the complete 24-page `source/double-slit-theory.pdf`, SHA-256 `e3cf7d49e6a4942c7ccad4805f6a2a07e1c817753ff8d384b1f2e37791ebbe27`. Its original user statements define the intended components. Other-assistant commentary proposes interpretations and makes predictions; it is not a source of measured guarantees. [integer_binding.json](../model/integer_binding.json) records the edition's numerical choices and verification contract. The runtime model identifier is `integer-1`, report version `0.4`, with snapshot version 4. Historical floating snapshot version 3 is incompatible and must be rejected rather than reinterpreted.

## 1. Literal computational components

| ID | Source user statement / pages | Required implementation | Evidence needed |
|---|---|---|---|
| INT-01 | Current request: full integer words, SDFs and small L1 log-polar LUT; source cache aspiration p18 | Integer arithmetic throughout the closed device recurrence, including initialization, movement, routing, calculus, packing and self-mutation. Native sampler float-typed arguments/results are an explicitly reported bit-preserving boundary, not a floating arithmetic fallback. | Review the complete call graph and compiled PTX/SASS of all edition kernels; reject floating arithmetic, conversions, comparisons and SFU instructions; report the sampler/bit-transfer boundary separately. |
| INT-02 | Two pinions and Hadamard mitosis hinges, p3-4 | Two independently encoded complex streams and an explicitly scaled integer sum/difference action. | Exact equal-input and opposite-input cancellation; bounded independent fixed-point reference comparison over every LP8 pair. |
| INT-03 | Log-encoded polar LUT, lower-case phi, p3; log-encoded polar radius PHI, p11 | A small integer LUT represents log radius and periodic phase. Integer operations perform reconstruction and re-encoding, including zero handling. | LUT byte count, integer element types, all nonzero cell roundtrips, phase seam cases and defined zero aliases. |
| INT-04 | Even/odd one-bit parity, p4-5 | Precisely defined parity, packed bit operations and one-bit decisions. | Population-parity checks, all word shifts valid, executable mutation changes at most the specified bit. |
| INT-05 | `[0,2,0,1]` wavefront and jitter, p6 | The designated source block binds R/G amplitudes, B and A to documented integer values; jitter remains one bit. | Inspect initialized words and their decoded values; same seed/state reproducibility. A Fourier transform of timestamp 756 is not invented. |
| INT-06 | Two Y-up shifts at fourth RK4 timeslot, p7 | Four integer stages with the +2 chart-unit y event in stage four, followed by defined weighted integer accumulation. | Stage-by-stage reference comparison; event affects only the fourth stage input; event-off comparison and arithmetic-range analysis. |
| INT-07 | T, pyramid side, circle, cone, sphere, apex, p8 | All six named geometric supports return signed integer field values with declared units and approximation limits. | Interior, boundary and exterior cases for every primitive; magnitude comparisons, not only one-bit membership checks. |
| INT-08 | Pinion double-dot product, p8 | Typed integer contraction of the two decoded complex vectors, with explicit scale and a wide intermediate. | Independent dot-product oracle, extrema and sign cases; no overflow for the supported amplitude domain. |
| INT-09 | Delta-delta-phi, Fibonacci phyllotaxis and math blend, p8-9 | Wrapped phase second difference, integer golden-angle placement/order and defined fixed-point blend operations. | Phase seam and wrap checks; known placement sequence; blend endpoints, rounding and range checks. No claim of uniform Klein area without a separate measurement. |
| INT-10 | Dichromatic R/G leaving the remaining color slots, p11; A inverse T, p9 | Each R/G token holds a complete stream value; exact B/A words have explicit storage. Define the T being inverted. | Channel isolation, real allocation accounting, all modular inverse words compose to identity. Do not claim A inverts the entire lossy recurrence. |
| INT-11 | Disregard rasterization, raymarching, raytracing and square fields, p12 | Recurrence runs without a renderer or geometric lattice. Array dimensions are a physical storage layout. | Headless execution and call-graph inspection; location and support use quotient coordinates, not pixel-grid geometry. |
| INT-12 | Self-referential SDF Klein bottle, p12; pinions keep operators on its surface, p14 | Integer quotient folding and integer K realization; every live operator owns a movable signed support attached to that quotient. | Positive and negative winding, exact discrete seam identities where construction permits, bounded location, and sampled geometric-distance checks. |
| INT-13 | SDF of all operators in a BST, p12; operators themselves move/change at Psi, p14 | Packed records contain executable body, support and location. Field feedback changes instruction words, references/support and positions; the next interval consumes them. | Body-change, support-change and location-change evidence; perturbing body/reference changes a later field result; frozen-control comparison. |
| INT-14 | One-bit BST at interval Psi, p8/p14 | Bounded binary routing plus ordered interval semantics; implicit children are the adopted p22 implementation suggestion. | All traversals terminate in valid leaves; stage reads old state; commit destinations are unique; no mixed old/new operator bank. |
| INT-15 | Cached substrate and packed VRAM without hot swap, p18 | Small hot integer LUT and operator bank; on-device packed field and data-directed chain reads; no recurrent host field replacement. | Exact resource byte counts, integer texture-fetch evidence, memory timeline/transfer scope, all payload blocks reached in a full sweep. |
| INT-16 | Hypothetical packing, complexity and comparisons requested, p20 | Report observed byte layout, usable allocation, work per interval/sweep and repeated runtime measurements. | New-edition reports tied to hashes and parameters; fixed recurrence comparisons and explicit capacity headroom. |
| INT-17 | Optional Bayer readout, p12 | Optional downstream presentation must not participate in the recurrence. | Absence of a renderer is acceptable. If added, enabling it must not alter the stored state at a fixed interval. |

The design is complete only when these components form one executed circulation. A kernel that evaluates integer SDFs but still dispatches the floating v0.3 Hadamard/encoding/RK4 path is an incomplete implementation of INT-01 through INT-13.

## 2. Phi, logarithms and the distinction between two streams

The user's p3 wording places lower-case phi in a log-encoded polar LUT. The p11 wording specifically says log-encoded polar radius PHI. Neither defines a logarithm of phase, a logarithm base, an angular branch cut, units or bit widths. The claim that logarithmically encoding phase linearizes probability is introduced by the other assistant on p4 and is not a usable numerical specification.

This edition therefore binds **logarithmic radius and linear modular phase**. The two chart coordinates are `(u,v)`, with `u` a normalized logarithmic-radius coordinate and `v` an angle measured in turns. R and G are two complete log-polar complex tokens; they are not radius and phase channels of one shared complex value. Lower-case phi and upper-case PHI are treated as references to this angular coordinate, not silently as the golden ratio. Golden-angle constants are named separately.

A logarithm of phase would require another explicit binding because zero/negative angles and phase periodicity have no unique ordinary real logarithm. It is not required merely by the word log-polar and is not inserted here.

## 3. Integer representation contract

The following choices fill open source positions. They are mathematical implementation definitions, not equations copied from the PDF:

| Quantity | Integer definition |
|---|---|
| Chart coordinates | Q16: 65,536 units per chart period/phase turn. An extended signed u retains winding until folding. |
| Klein fold | `u=raw_u mod 65536`; each odd signed u winding negates phase modulo 65,536. Negative winding must use mathematical floor division, not truncation toward zero. |
| Complex coordinates | Signed Q11 x/y in two int16 values packed into one uint32. Wider integer intermediates are required for products and weighted sums. |
| Log radius | Fifteen nonzero cell centres over `rho=-4+7.5*u`, base two; sixteen phase cells. High-nibble-zero tokens all mean zero complex amplitude. |
| Log-polar table | 256 packed uint32 entries, 1,024 bytes. |
| Trigonometric table | 257 uint16 quarter-sine samples in Q15; peak 32,768; integer interpolation and quadrant symmetry. |
| Complete math table | `lp[256]` and `sin_quarter[257]`, 1,538 payload bytes, `sizeof(MathLut)=1540` with four-byte alignment. No 1 MiB all-pairs table is required. |
| Mutable routing masks | 15 internal tree nodes times 256 input tokens, one bit each: 480 bytes. Rebuild the live signed-support >=0 predicate; the optimized integer sign specialization avoids unnecessary magnitude calculations and is checked against full signed evaluation. |
| Combined hot set | 1,984 bytes of operator records + 1,540-byte math table + 480-byte routing masks = 4,004 payload bytes. Actual shared allocation/alignment must also be reported. |
| Hadamard factor | 23,170 / 32,768; symmetric nearest rounding with ties away from zero. Exact integer antipodes cancel before encoding. |
| Geometric support units | Q18; one chart unit equals four geometry units. Radius is `low16(support)+1` in Q18. |
| Integer functions | Defined integer square root, log2 magnitude and phase angle/CORDIC, with explicit rounding, iteration counts and zero handling. No libm fallback in the device recurrence. |

Fixed-point means integer words with declared scale; it does not mean the numerical result is an exact real number. The implementation must document rounding order and whether each operation uses modular, bounded or widened arithmetic. Signed C++ overflow and undefined shifts are not acceptable arithmetic definitions. CLI parsing and report presentation may use host floating values only if they are converted once to an explicitly recorded integer configuration before recurrence execution.

Time-step and inverse-gain words are also Q16. Default `dt_q16=1024` means 1/64; default `inverse_gain_q16=16384` means 1/4. Allowed dt words are 1 through 65,536 and gain words 0 through 65,536. The drive is Q16 with `drive_u=nearest(signed16(reg0)/2)` and `drive_v=nearest(signed16(reg1)/2)+25032`. Coupling is Q16 `nearest((low16(coeff)+1)/16)`. This last rounding can produce zero coupling for the smallest coefficients and is a deliberate new integer binding, not bitwise equivalence to the old positive floating coefficient.

For every signed product/division in the flow, nearest means symmetric nearest with ties away from zero. The four derivative argument stages use integer chart coordinates. The fourth argument is `q + round(dt_q16*k3/65536) + (0,2)`. The second and third arguments use one rounding of `dt_q16*slope/131072`; the final increment uses one rounding of `dt_q16*(k1+2*k2+2*k3+k4)/393216`. Inverse feedback and phase words remain integer. Exact rounding order and seed-placement constants are implementation definitions and must be synchronized with `integer_binding.json`.

## 4. What integer SDF fidelity requires

Signed support values must exist, rather than just cached Boolean masks. For a circle, box, triangle and apex, the integer function returns a quantized distance in the stated geometric scale. Radial and triangle functions preserve exact integer inside/outside membership with a value of -1 or +1 when nearest-distance rounding alone would produce zero for a nonboundary point. The T is a union of box fields; minimum composition is a useful support field but is not an exact Euclidean signed distance at every interior overlap. The cone is a documented two-dimensional meridian triangle. The sphere support measures an ambient radial distance from a centre on the four-coordinate K realization.

The user asks for a Klein surface and operator SDFs but does not provide a global scalar signed-distance equation. A closed non-orientable Klein surface does not have the source assistant's purported single edge or an ordinary global inside/outside sign in three-dimensional space. This edition uses quotient-constrained locations with signed **local operator supports**. That interpretation must be stated explicitly; a global Klein SDF cannot be declared implemented merely because a Boolean route bit exists.

Operator attachment to K is by construction from integer chart coordinates. A signed support can move while remaining attached to that chart. This meets the executable surface/circulation interpretation; it is not proof of a smooth intrinsic flow or a physical non-orientable material.

## 5. Texture/cache boundary and arithmetic evidence

The arithmetic claim must cover both numerical helper functions and how their inputs are fetched. The selected edition retains native BC5 hardware texture decoding, so it is accurately described as **integer software arithmetic with an explicit native UNORM sampler boundary**. BC5 sampler arguments/results have float-typed CUDA interfaces. Texture coordinate IEEE bit patterns are constructed with integers, and normalized result bit patterns are decoded to token integers with integer operations. The ABI bitcasts/loads/stores are not floating arithmetic. RG8 uses integer `tex2D<uint2>` results with the same bit-constructed coordinate convention.

The boundary must be documented and tested: the supported coordinate domain, exact representation of centre coordinates, valid UNORM bit patterns, token recovery/rounding rule, and measured hardware BC5 palette behavior. Input-dependent FP add/multiply/divide, float-to-int conversion, floating comparison, logarithmic/trigonometric intrinsic or reciprocal SFU may not hide inside the hot kernel. Compilers can lower an integer division using floating reciprocal machinery, so a PTX-only check is insufficient: inspect final SASS as well. The audited compiler emits a specifically recognized `HFMA2 dst,-RZ,RZ,literal,literal` form solely to materialize constant bit patterns. This is an explicit constant-only instruction exception with architectural zero operands and immediate literals; it is not data-dependent floating recurrence arithmetic. A claim of zero floating opcodes would therefore be false.

NVIDIA documents integer element reads and normalized-float conversion as different texture modes in its [CUDA texture-object API](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__TEXTURE__OBJECT.html). The native BC5 fixed-function sampler remains part of the hardware codec; this edition does not claim that every transistor in the GPU performs integer logic. The actual claim is about software-visible recurrence arithmetic. `tools/verify_integer_device_code.py` records the separately permitted texture/representation boundary and rejects prohibited arithmetic.

A CPU BC5 oracle must implement the same decoder mapping as the native sampler before complete CPU/GPU state equality is asserted. If native palette rounding differs from the CPU software palette, record that difference separately and use exact GPU reference/optimized comparison for the shared hardware boundary. A one-byte local decode tolerance is not permission to call arbitrarily diverged later recurrence states equal.

The small LUT may be staged in shared memory per CUDA block and backed by texture-cached device memory. Its byte count and shared-memory use are facts; L1 hit rate, occupancy, bandwidth and latency are measured outcomes. Neither shared-memory staging nor an L2 persistence hint is a permanent hardware cache lock. The phrase small L1 LUT is satisfied by an explicitly bounded hot representation and measured behavior, not by allocating an unbounded table and naming it small.

An optional D4-symmetry pair cache adds 8,192 records of eight bytes, or 65,536 bytes, to the compact 4,004-byte active tables. Its combined logical table size is 69,540 bytes. The records cache exact integer Hadamard/log/phase results; they do not change the LUT or recurrence definition. The [component cache checks](../results/integer/integer_pair_cache_tests.txt) exhaustively compare all token pairs, plus/minus branches and eight chart/phase offset settings in 1,253,890 assertions. Exact component equivalence is distinct from complete GPU state equivalence and repeated GPU performance. Compiled CUDA machine code, driver resources, staging and the additional operator bank are not included in the 4,004-byte compact active-data count.

## 6. Completion checklist: code plus evidence

Each item needs both an implementation location and a reproducible evidence record. A checkbox is a review aid, not a claim of current success.

- [ ] Integer edition has a distinct model identifier and recorded arithmetic ABI; historical floating results are not relabeled as integer results.
- [ ] Every component INT-01 through INT-16 participates in the same actual CUDA run; the optional readout remains downstream.
- [ ] All recurrent functions accept integer state/configuration and execute integer calculations, including seed initialization, signed supports, K, Hadamard, log/phase encoding, fourth-slot calculus, inverse feedback, mutation and both codecs.
- [ ] Compiled kernel call-graph/PTX/SASS inspection records integer versus floating arithmetic, transcendental instructions and conversion/fetch boundaries. The documented native sampler/representation transfers and constant-only HFMA2 materialization are the explicit exceptions; no dynamic-input floating arithmetic is allowed. Float report formatting outside the recurrence is identified separately.
- [ ] The small LUT is built from reproducible integer data/functions; its complete allocated and shared sizes are reported. Quarter-wave and complex antipodal symmetries are checked.
- [ ] Every nonzero LP8 token roundtrips; all zero aliases decode zero; equal/opposite integer complex pairs cancel at the algebraic stage as defined. Exhaustive pair comparisons quantify encoding changes rather than asserting physical norm conservation.
- [ ] Every named support returns a signed integer magnitude, passes interior/boundary/exterior cases and has measured quantization error against an independent reference. K seam, fold parity and negative winding are checked.
- [ ] Integer rounding, overflow bounds, signed division conventions and all bit shifts are reviewed. Hardware sanitizer checks exercise partial windows and page boundaries.
- [ ] Forced four-stage update is compared stage by stage with an independent integer reference, including the explicit two-unit fourth-stage event. A zero-event control demonstrates the chosen difference.
- [ ] All 65,536 phase inverse words compose to zero modulo 65,536; T's scope is stated. Source `[0,2,0,1]` words and decoded values are recorded.
- [ ] Full integer CPU/GPU state or snapshots agree where they use the same decoder law; native BC5 palette differences are explicitly scoped. Exact native GPU reference/optimized state comparisons cover both codecs, multiple seeds, partial/full windows, mutation/jitter controls, zero hops and inverse-gain controls. Integer determinism is tested, not inferred from the word integer.
- [ ] Restart/continuation and graph/sequential execution preserve the integer state. Historical floating snapshots cannot silently resume under another numerical binding.
- [ ] Self-reference is shown by executable-word, support, link and location changes and by later dependence on those changes, with a frozen-control run.
- [ ] Near-capacity allocation initializes useful payload, completes a full sweep, records actual free/reserved bytes and runs without recurrent host field hot-swapping. OS residency claims remain scoped to actual evidence.
- [ ] Repeated optimized/reference timings compare the **same integer law** at fixed W, dt, gain, seed, hops, codec and cache policy when isolating implementation changes. Comparison with the old floating law is labeled a different-model comparison.
- [ ] Report contains speed distribution, stored pairs, updated pairs/s, full-sweep time, total bytes, cache/profiler scope, numerical error and source correspondence. Every claimed result points to a fresh integer-edition artifact.
- [ ] A new formalization/report describes the implemented integer choices and remaining limitations without overwriting the prior historical report.

Tests of the new integer laws establish the new binding. They are not expected to reproduce floating-point roundoff or the earlier catastrophic cancellation residue. A deliberate rounding/symmetry change must be named and measured; it cannot be advertised simultaneously as a new integer definition and bitwise identity to all old floating states.

### Recorded component evidence

The [integer math component log](../results/integer/integer_math_tests.txt) records 11 cases and 1,483,985 assertions passing. The [integer core component log](../results/integer/integer_core_tests.txt) records eight cases and 296,554 assertions passing, including direct/masked route and complete-stage equality, CPU circulation, continuation and recurrence ablations. These are CPU component results, not completion of the whole GPU acceptance checklist. The exact antipodal construction covers all 256 byte symbols, including sixteen zero aliases and 240 nonzero symbols. Every nonzero LP8 centre roundtrips.

| Component diagnostic | Observed maximum | Scope |
|---|---:|---|
| Integer Hadamard relative energy error | 0.0073157, about 0.732% | All 65,536 input-symbol pairs before LP8 re-encoding; coefficient and integer rounding error remain. |
| Quarter-wave sine error | 1.0007 Q15 units | Diagnostic comparison with an independent real reference. |
| Integer logarithm error | 1 Q16 unit | Diagnostic sample set; zero sentinel handled separately. |
| CORDIC phase error | 1 turn16 unit | Diagnostic sample set including axes and small inputs. |
| Integer K coordinate error | 20.38 Q18 units | Sampled coordinate realization compared to the real formula. |
| Integer signed-support error | 25.4844 Q18 units | Sampled named supports compared to the previous geometric binding; preserves the specified support approximations. |

Integer antipodal cancellation removes the earlier floating cancellation residue at that component. It does not remove log-radius wrapping or establish a unitary full LP8 recurrence. Fresh full-path numerical diagnostics are required for any such broader statement.

### Executed integer theory diagnostics

[integer_theory_diagnostics.cpp](../tools/integer_theory_diagnostics.cpp) and its [recorded JSON output](../results/integer/theory_diagnostics.json) supplement the component logs with a 16-point phase sweep, exhaustive encoded-pair energy results, an in-window amplitude-error sample and explicit fourth-stage controls. The JSON includes compiler identity/options, executable and source SHA-256 hashes checked across compilation/execution, and the original PDF hash. Real arithmetic in this diagnostic is limited to statistics and declared ideal-reference formulas; it does not replace any dwi operation being measured.

The 16-point sweep uses radial nibble 8 and relative phase `k/16` turns. It provides four distinct curves: the ideal constant-radius interference identity; the exact real sum/difference identity for the actual decoded Q11 inputs; rounded integer Hadamard energies; and energies after LP8 re-encoding. It is a two-stream algebraic comparison, not a detector experiment or spatial fringe measurement.

| Diagnostic | Result | Interpretation |
|---|---:|---|
| Raw integer Hadamard relative norm error | Median 0.011252%; maximum 0.731570% | Integer coefficient/component rounding before LP8 re-encoding, across all nonzero-input token pairs. |
| LP8-encoded output/input energy ratio | Minimum 0.0000304249; maximum 32,867.8153 | Quotient folding still prevents full physical norm conservation. Maximum witness `[0,16]` encodes to `[255,247]`. |
| LP8-encoded relative norm error | Median 1.54334%; 95th percentile 41.0609% | Exhaustive integer token population, not an observed application workload distribution. |
| In-window LP8 relative amplitude error | Median 8.63196%; 95th percentile 16.7266%; maximum 19.3762% | 245,744 accepted Q11 samples from a declared log-radius/phase grid; sixteen samples outside the actual nominal radius window excluded and counted. |
| Source amplitude 2 | Encodes to token 176; decoded magnitude 2.37819682 | Relative amplitude error 18.9098%; this is representation quantization, not evidence of gain in a physical wave. |
| Exact quotient and inverse invariants | 36,864 K seam cases and 65,536 phase words; zero failures | Exact discrete invariants for the tested integer cases. |
| Four-stage event control | 16,384 cases; zero reference mismatches; 271 final outputs changed with the event enabled | The +2 y event is still in the fourth input; integer rounding can hide its effect in other cases. |

The encoded energy ratio's median is near one, but its extreme wrap cases remain large. Reporting only the exact cancellations or the median would conceal a material property of this source-inspired quotient law.

### Quantum-style mechanism probes

[quantum_mechanism_checks.cpp](../tools/quantum_mechanism_checks.cpp) applies the actual production integer Hadamard and phase primitives in isolated CPU two-arm circuits; [its recorded JSON](../results/integer/quantum_mechanism_checks.json) preserves complete sampled results. Over all 65,280 nonzero token pairs, applying integer H twice gives minimum normalized state-overlap fidelity 0.999985 and median 1. Inserting LP8 encoding/decoding between the operations and after the second H lowers the minimum to 0.0169163, with median 0.9974364 and output/input squared-norm ratios approximately 0.02083 to 8,216.13. Normalization in a diagnostic must not conceal that gain/loss.

Equal-arm phase sweeps and H-phase-H recombination use sixteen phase settings at radial bins 1, 9 and 15. All sampled port-energy visibilities are 1 because exact dark ports remain, but encoded probability-curve errors reach approximately 96.1 percentage points at some extreme bins. At middle bin 9, the encoded maximum error is approximately 3.537 percentage points. The raw H-phase-H bin-9 maximum is about 0.007502 percentage points. These are component interference and reversibility diagnostics, not a physical screen, particle experiment, Born measurement or entanglement demonstration. The full nonlinear field recurrence has no established quantum-state fidelity or general quantum-simulator claim.

## 7. Claims excluded from automatic acceptance

The following are other-assistant predictions, not guaranteed consequences of the user's requested architecture: actual quantum gates or randomness; physical double-slit validation; prevention of all cycles; beneficial mutations without a task objective; universal computation without a reduction and scalable memory construction; uniform Klein-area density from golden angles; perfect warp coherence; permanently resident caches; zero memory stalls or zero PCIe traffic; 24-48 billion independent payload values in a format that cannot store them; or constant-time rewriting of an arbitrarily large field.

The integer implementation may be a useful and faster classical self-referential machine without those claims. Completion means faithfully implementing all specified computational components, exposing the missing numerical choices, and measuring what the delivered machine actually does.
