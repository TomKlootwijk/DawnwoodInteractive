# Dawnwood Interactive: formal supplement to the literal source

Tom Klootwijk - Dawnwood Interactive - 2026-09-16

This supplement formalizes the executable digital kernel inspired by the supplied 24-page `source/double-slit-theory.pdf`. It distinguishes **literal source requirements**, **numerical definitions chosen for the native binding**, **mathematical deductions**, and **executed measurements**. Equations below specify that binding; they are not physical laws inferred from conversational metaphors. The source PDF SHA-256 is `e3cf7d49e6a4942c7ccad4805f6a2a07e1c817753ff8d384b1f2e37791ebbe27`.

The original conversation supplies the design vocabulary and requested behavior, but leaves numerical positions open. The archived `source/v0.2_open_bindings.json` records those positions. `model/native_binding.json`, `model/operators.json` and [NATIVE_BINDING.md](NATIVE_BINDING.md) make the choices inspectable. [The detailed audit](../results/optimization/THEORY_AUDIT.md) includes a complete claims-to-evidence table and corrections to the source assistant's unsupported predictions.

## 1. Literal requirements and their status

| Source pages | Literal requirement | Native realization and scope |
|---|---|---|
| 3-4 | Double pinion, Hadamard mitosis hinges, log-encoded polar LUT | Two complex streams, Hadamard sum/difference, LP8 chart. No spatial slit aperture or detector has been defined. |
| 4-6 | One-bit parity, jitter and `[0,2,0,1]` wavefront | Population parity and deterministic hash-selected bits; first block holds zero R, encoded amplitude-two G, zero B and phase-inverse identity A. No Fourier transform of timestamp 756 is implied. |
| 7 | Two Y-up shifts in the fourth RK4 timeslot | The fourth derivative receives a fixed y increment `2/65536`. This forced event is retained exactly. |
| 8-9 | T, pyramid side, circle, cone, sphere, apex; double-dot; delta-delta-phi and Fibonacci blend | Local support primitives; real-vector dot product; wrapped phase difference; golden-angle initial placement. These operand and units choices are definitions of the binding. |
| 9-12 | Dichromatic RG; B history; A inverse T | R/G each carry a complete LP8 token. B/A are exact auxiliary words per 16 pairs. A inverts the two defined phase words, not the entire nonlinear map. |
| 12-14 | Klein surface, operator SDFs, no rasterization/raymarching/raytracing/square computational field; optional Bayer output | Canonical quotient coordinates and operator-local support fields. Rectangular arrays specify storage only. No global Klein signed-distance function or renderer is required or implemented. |
| 14-16 | Operators themselves move and change around the surface at Psi | Field feedback changes instruction bits, body references, support, coefficients, location and routing; alternate banks preserve prior-state reads. |
| 18-20 | Small cached substrate and packed resident VRAM without host hot-swapping | Shared hot set, texture-backed field, GPU-owned clock, chain reads and bounded staging. Actual allocation and throughput are measured separately from cache policy. |
| 21-22 | Implicit one-bit hierarchy with children `2i+1`, `2i+2` | A fixed 31-record operator tree with four branch decisions; no stored child pointers. This is not a search tree over all payload tokens. |
| 23 | Universal expression of arbitrary computation | An aspiration requiring a constructive proof and scalable memory/control model. The delivered finite machine and tested bodies do not establish unrestricted universality. |

The source includes another assistant's claims of quantum hardware, guaranteed self-optimization, 24-48 billion stored states and a constant-time update of the whole field. Those conclusions do not follow from the literal user requirements or the actual byte layout. Keeping their distinction is part of faithful formalization.

## 2. State, schedule and causality

At interval `e`, write

```text
F_e = (P_e, O_e, B_e, A_e, e, cursor_e, seed)
```

`P_e` is the packed dichromatic field. `O_e` contains 31 operators of 64 bytes each. Each 4x4 storage block has sixteen R/G pairs and one exact eight-byte B/A record. Let N be the number of storage blocks and W the active window, with `1 <= W <= N`.

```text
index(t) = (cursor_e + t) mod N,       0 <= t < W
Stage_t  = E(F_e, index(t), config)
P_(e+1)[index(t)], B_(e+1), A_(e+1) = commit(Stage_t)
O_(e+1)[i] = M(O_e, sampled Stage, e, seed),    0 <= i < 31
cursor_(e+1) = (cursor_e + W) mod N
```

Evaluation reads only committed prior state. Each commit owns one distinct block. Operator mutation reads the previous bank; it cannot partly observe another operator's new value. Separate kernels and their ordered launch dependencies implement this relation. Self-reference occurs through the next committed interval, rather than unbounded recursive execution on a thread's stack.

Changing W changes the recurrence: it changes how much of the field updates before operators change. Therefore a speed comparison must hold W, dt, seed, hops, codec, jitter and mutation flags fixed to compare the same model.

## 3. LP8 and the Klein quotient

For byte q, let `h=q>>4`, `p=q&15`. All sixteen `h=0` patterns decode as zero complex amplitude. Otherwise:

```text
u = (h - 1/2)/15
v = (p + 1/2)/16
rho = -4 + 7.5*u
L(q) = 2^rho * exp(i*2*pi*v)
```

There are fifteen nonzero log-radius cells and sixteen phase cells. Their spacings are 0.5 in log2 radius and 22.5 degrees in phase. For nonzero complex z, encoding first forms

```text
U = (log2(|z|) + 4)/7.5 + du
V = arg(z)/(2*pi) + dv
n = floor(U)
u = U - n
v = fract((-1)^n * V)
Q(z;du,dv) = 16*(floor(15*u)+1) + floor(16*v)
Q(0;du,dv) = 0
```

This explicitly implements `(u+1,v) ~ (u,-v)` and `(u,v+1) ~ (u,v)`. Its coordinate realization is

```text
K(u,v) = ((2+0.5*cos(2*pi*v))*cos(2*pi*u),
          (2+0.5*cos(2*pi*v))*sin(2*pi*u),
           0.5*sin(2*pi*v)*cos(pi*u),
           0.5*sin(2*pi*v)*sin(pi*u))
K(u+1,-v) = K(u,v)
```

The seam identity is an algebraic property and an executable numerical invariant. The chosen update uses canonical chart coordinates; this alone does not establish a globally smooth intrinsic physical vector field. Local circle, box, triangle and point supports are evaluated in that chart, with the sphere support using ambient distance in K. They are not a global signed distance to a 3D Klein bottle.

Crucially, radius wrapping identifies amplitudes differing by `2^7.5`, approximately 181.02, with a phase reversal. It preserves a quotient-coordinate interpretation but not ordinary physical amplitude magnitude. No automatic clipping or tiny-amplitude threshold is silently introduced by this supplement.

## 4. Routing, executable words and self-reference

Each operator stores its chart location, support, two five-bit body references, coefficient words, eight packed instructions, last result, history, inverse phase and routing parity. The VM uses eight 16-bit registers and sixteen total operations, with modular overflow. Body-reference value 31 aliases root 0.

Routing starts at root 0. At each internal node, its support sign, jitter bit, chart reversal bit, a rotating history bit and operator route bit determine one binary branch. Children are `2i+1` and `2i+2`. Four decisions reach one of leaves 15-30. The selected operator's first referenced body, second referenced body, and own body execute sequentially: 24 instruction words per block before the geometric update.

The feedback hash chooses one instruction word and one bit. With j in {0,1}:

```text
code[(hash>>5) mod 8] ^= j << (hash & 31)
```

The same feedback also updates references and support/coefficient bits; location and route evolve. An altered bit can be reserved, so one changed code bit does not guarantee changed behavior for every input. There is no fitness function here; mutation and self-reference are established mechanisms, while automatic optimization remains a separate hypothesis. The tree remains 31 records; no branch allocation or tree growth occurs.

## 5. Double pinion, phase difference and forced fourth slot

For decoded stream values `a=L(R)` and `b=L(G)`:

```text
h_plus  = (a+b)/sqrt(2)
h_minus = (a-b)/sqrt(2)
dot(a,b) = Re(a)*Re(b) + Im(a)*Im(b)
twist = dt*dot(a,b)
```

The native double-dot operation is this scalar real-vector contraction. Its phase contribution is measured in chart turns by definition; it is not a dimensional physical coupling derived from the source. For neighbour phase coordinates and the first local R phase:

```text
wrap(x) = x - floor(x+1/2)
delta_delta_phi = wrap(v_neighbour_R - 2*v_local_R + v_neighbour_G)
drive_u = signed16(reg[0])/131072
drive_v = signed16(reg[1])/131072 + (3-sqrt(5))/2
coupling = (low16(selected.coeff)+1)/1048576
f(u,v) = (drive_u + coupling*sin(2*pi*v),
          drive_v + coupling*cos(2*pi*u))
```

Preserving source page 7 requires the following forced four-stage map:

```text
epsilon = 2/65536
k1 = f(q)
k2 = f(q + dt*k1/2)
k3 = f(q + dt*k2/2)
k4 = f(q + dt*k3 + (0,epsilon))
next = q + dt*(k1+2*k2+2*k3+k4)/6
du = next.u - q.u
dv = next.v - q.v + dt*delta_delta_phi
```

Classical RK4 is recovered when epsilon is zero. With fixed epsilon, its limiting derivative as dt tends to zero is `(5*f(q)+f(q+(0,epsilon)))/6`. The resulting bias relative to the unforced ODE is intentional source behavior, not an integration accuracy improvement that has been proved by the word RK4.

Let `A_R` and `A_G` be the signed 16-bit interpretations of the two previous inverse words, divided by 65,536, and g the configurable inverse gain:

```text
da =  dv + g*A_R
db = -dv + g*A_G
p_R = floor(fract(da)*65536)
p_G = floor(fract(db)*65536)
q_R = signed16(p_R)/65536
q_G = signed16(p_G)/65536
A_next = (-p_R mod 65536, -p_G mod 65536)
R_next = Q(h_plus;  du, q_R + twist) XOR j
G_next = Q(h_minus; -du, q_G - twist) XOR j
```

The A words therefore compose exactly with their defined p words, not with the complete nonlinear transition. B rolls prior history and incorporates jitter, fold parity, output parity and epoch hash. BC5 then quantizes token bytes; RG8 stores those bytes exactly. Neither mode removes the earlier LP8 quantization or quotient wrapping.

## 6. Isolated analytic interference comparison

This is a mathematical comparison for the linear Hadamard component, before chart drifts, mutation, folding and either codec. Give the two inputs unit amplitudes `a=1` and `b=exp(i*phi)`. The two output intensities are

```text
I_plus(phi)  = |(1+exp(i*phi))/sqrt(2)|^2 = 1+cos(phi)
I_minus(phi) = |(1-exp(i*phi))/sqrt(2)|^2 = 1-cos(phi)
I_plus + I_minus = 2
P_plus = I_plus/2,  P_minus = I_minus/2
```

The probabilities in the last line are a normalized analytic comparison, not a detector rule implemented by the automaton.

| Relative phase | I_plus | I_minus | Interpretation of the isolated component |
|---|---:|---:|---|
| 0 | 2 | 0 | Constructive plus port, destructive minus port |
| pi/2 | 1 | 1 | Equal port intensities |
| pi | 0 | 2 | Destructive plus port, constructive minus port |

For general complex inputs, `|h_plus|^2+|h_minus|^2=|a|^2+|b|^2`. These identities derive directly from complex arithmetic. They explain why the kernel's selected linear component is an interference analogy. They do not define a spatial fringe pattern, which would require a specified relation between phase and detector position. Physical two-path detection uses amplitude addition and squared magnitudes; see [Feynman Lectures, volume III, chapter 1](https://www.feynmanlectures.caltech.edu/III_01.html).

## 7. What the executed numerical experiments actually show

`tools/theory_diagnostics.cpp` uses native header operations for the component diagnostics and a separately labeled double-precision mirror for the four-stage convergence comparison. It compiled and ran on the CPU with MSVC 19.44, C++17 and `/O2`, with the reference-kernel macro enabled. Raw machine-readable evidence is [theory_diagnostics.json](../results/optimization/theory_diagnostics.json).

| Diagnostic | Executed result | Supported conclusion |
|---|---:|---|
| All 65,280 nonzero token-pair inputs: largest relative Hadamard norm residual before encoding | 1.6708e-7 | Native float linear algebra agrees with the isolated identity. |
| LP8 energy ratio after that split, minimum / maximum | 3.0518e-5 / 32,768.00365 | The full encoded split is not norm-preserving. |
| Cases with relative energy change above 1e-4 | 53,440 of 65,280 | Physical magnitude distortion is widespread in this exhaustive token population. |
| Largest energy-gain witness | Input `[17,0]`, output `[254,254]` | Quotient radius wrapping matters even without BC5. |
| Opposite-phase directed token pairs with nonzero encoded sum | 240 of 240 | Tiny float cancellation residuals do not become exact zeros; log-radius wrapping amplifies some. |
| Largest raw canceled amplitude / largest decoded sum amplitude | 1.2157e-6 / 9.51366 | Separate maxima across the 240-pair population; not one paired measurement. |
| LP8 nonzero cell-centre roundtrip failures | 0 of 240 | Representable token centres roundtrip; arbitrary physical amplitudes do not. |
| Klein seam maximum component error over 29,161 points | 4.0121e-6 | The coordinate seam holds to float precision at sampled points. |
| Modular phase inverse failures | 0 of 65,536 | A implements the exact defined modular inverse. |
| Encoded source amplitude 2 | Token 176; decoded magnitude 2.37841; complex error 0.570964 | The source initialization is explicitly quantized. |
| Unforced double RK4 error at 256 steps over T=1 | 1.2906e-12 | The comparison recovers classical convergence for the selected diagnostic ODE. |
| Forced double-map error against that same unforced reference | 2.2248e-6 | Fixed fourth-slot forcing leaves model bias when dt shrinks. |

The convergence experiment uses initial q=(0.2,0.3), drive=(0.4,-0.2), coupling=0.15, and an unforced 131,072-step double RK4 reference. These are explicit diagnostic inputs, not values found in the source PDF. The opposite-phase examples count directed pairs; exchanging the inputs produces another entry. The LP8 exhaustive population is a component stress experiment, not a distribution sampled from a long GPU run.

To reproduce without modifying CMake, open a Visual Studio Developer PowerShell at the project root:

```powershell
cl /nologo /O2 /EHsc /std:c++17 /DDW_REFERENCE_KERNEL=1 /Iinclude tools\theory_diagnostics.cpp /Feresults\optimization\theory_diagnostics.exe /Foresults\optimization\theory_diagnostics.obj
.\results\optimization\theory_diagnostics.exe | Set-Content -Encoding utf8 results\optimization\theory_diagnostics.json
```

No empirical physics validation follows from these checks. On the contrary, the LP8 observations rule out treating the default recurrence as an accurate norm-preserving two-path wave model. Preserving source-defined quotient behavior is compatible with stating this limitation plainly.

## 8. Formal role of the optimized cache path

The optional immutable pair table stores the expensive pre-drift chart calculation for each of the `256*256` input token pairs. Each entry contains four floats:

```text
Pair[R,G] = (U(h_plus), V(h_plus), U(h_minus), V(h_minus))
```

Exact zero has an explicit sentinel. An entry is sixteen bytes, so the complete table is 1 MiB. The later du/dv offsets, current operator execution, live phase inverse, coupling twist, jitter, folding, history and mutation remain part of each interval. The table must use the same uploaded LUT and arithmetic convention as the reference device calculation. It memoizes a finite function; it does not create new state capacity or change the theoretical operator law. Exact optimized/reference evidence belongs to the hardware acceptance results, separately from the component diagnostics above.

The original 31 operators plus 256-entry decode table occupy 6,080 bytes per CUDA block in shared memory. The optional pair table resides in device memory and can receive cache preference; it does not add 1 MiB of shared allocation per block. A requested cache policy is not a cache-hit measurement. [NVIDIA's L2 cache-control documentation](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/l2-cache-control.html) describes the preference and possible eviction behavior.

## 9. Storage, work and ELI5 metrics

| Layout | Dichromatic bytes per 16 pairs | Exact B/A bytes | Total bytes per pair |
|---|---:|---:|---:|
| BC5 | 16 | 8 | 1.5 |
| RG8 | 32 | 8 | 2.5 |

BC5 therefore saves 40% of total payload bytes versus RG8 for this same auxiliary layout, rather than halving the whole allocation. Its two-channel block format is documented by [Microsoft](https://learn.microsoft.com/en-us/windows/win32/direct3d11/texture-block-compression-in-direct3d-11). Encoding error on the combined token byte is distinct from phase error, radius error, or distance on K.

Before any overhead, ideal 12 GiB payload capacity is 8,589,934,592 BC5 pairs or 5,153,960,755 RG8 pairs. For decimal 12 GB the bounds are 8.0 billion and 4.8 billion. Actual usable capacity is lower due to reserve, staging, pages, tables and runtime resources. Removing the small operator tree's child pointers cannot create the source assistant's claimed 24-48 billion independently stored pairs.

For N payload blocks, W active blocks, H hops, D tree decisions and body length L, interval work is proportional to `W*(H+D+3L+codec work)+31`. A complete sweep requires at least work proportional to N. Here D=4 and L=8. Updating the constant-size operator catalogue is constant work relative to N; it does not rewrite the whole payload in constant time.

| Report quantity | ELI5 interpretation | What it does not establish |
|---|---|---|
| Actual allocated and remaining device bytes | How full the shelf is | How fast items move or how often the cache helps |
| Token-pair updates per second | How many items get updated each second | Independent physical particles or useful answers per second |
| Time per Psi interval | How long one update batch takes | Comparable behavior if the batch size W changes |
| Complete sweep time and coverage | How long until every stored block is revisited | That every block changes at every interval |
| LP8/BC5 errors | How much representation and packing change values | Lossless amplitudes merely because RG8 bytes are exact |
| Measured cache hit rate / DRAM throughput, when profiled | How often a nearby shelf serves a read / how fast memory transfers | These cannot be inferred from occupancy or a configured hitRatio |
| Code and state digests; continuation equality | Whether the requested digital state reproduces | A proof of physical correctness or universality |

GPU speeds, acceptance results and near-capacity residency measurements are reported separately in `results/optimization` and the accompanying Dawnwood Interactive PDF. This document supplies no invented GPU timings, cache rates or bandwidth figures.

## 10. Scope of a new Dawnwood formalization

The present system is a finite deterministic automaton with editable, self-modifying executable data, geometrically named supports and quotient-coordinate circulation. Pseudorandom hashed jitter is deterministic for a given state and seed. Bounded traversal and fixed instruction counts allow each invocation to finish; jitter supplies no theorem that the complete state avoids cycles, improves a solution, or becomes a quantum computer.

To validate a future physical companion, first define a preparation, wavelength/path geometry, propagation law, coherent versus which-path control, normalized detector rule and independent target data. Any alternative that removes quotient radius wrapping or changes zero handling must be identified as another binding and compared explicitly. No such replacement is silently made here. The present supplement supports the literal computational design while separating its demonstrated properties from the source conversation's stronger claims.
